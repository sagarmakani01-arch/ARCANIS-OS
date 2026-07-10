/**
 * terminal.c — Terminal Emulator Implementation
 *
 * ANSI escape sequence parsing and terminal rendering.
 */
#include <arcanis/terminal.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

/* Default color palette (Catppuccin Mocha) */
static const uint32_t default_palette[] = {
    0x1E1E2E, 0xF38BA8, 0xA6E3A1, 0xF9E2AF,
    0x89B4FA, 0xF5C2E7, 0x94E2D5, 0xBAC2DE,
    0x585B70, 0xF38BA8, 0xA6E3A1, 0xF9E2AF,
    0x89B4FA, 0xF5C2E7, 0x94E2D5, 0xCDD6F4,
};

void term_init(terminal_t* term, wm_state_t* wm) {
    if (!term) return;
    memset(term, 0, sizeof(terminal_t));
    term->wm = wm;

    /* Initialize palette */
    for (int i = 0; i < 16; i++)
        term->palette[i] = default_palette[i];

    /* Init screen */
    term->screen.rows = TERM_MAX_ROWS;
    term->screen.cols = TERM_MAX_COLS;
    term->screen.cursor_row = 0;
    term->screen.cursor_col = 0;
    term->screen.fg_color = 7; /* White */
    term->screen.bg_color = 0; /* Black */
    term->screen.cursor_visible = 1;
    term->screen.wrap_mode = 1;
    term->screen.auto_scroll = 1;
    term->screen.scroll_top = 0;
    term->screen.scroll_bottom = TERM_MAX_ROWS - 1;

    term->echo = 1;
    term->running = 1;
    string_copy(term->cwd, "/", 256);
    string_copy(term->title, "Terminal", 64);

    /* Create window */
    term->window_id = wm_create_window(wm, "Terminal", 150, 80, 640, 480, WIN_TYPE_NORMAL);
    wm_set_colors(wm, term->window_id, 0x1E1E2E, 0xCDD6F4, 0x45475A);
}

void term_clear(term_screen_t* screen) {
    if (!screen) return;
    for (uint32_t r = 0; r < screen->rows; r++)
        for (uint32_t c = 0; c < screen->cols; c++) {
            screen->cells[r][c].ch = ' ';
            screen->cells[r][c].fg = screen->fg_color;
            screen->cells[r][c].bg = screen->bg_color;
            screen->cells[r][c].attr = 0;
        }
    screen->cursor_row = 0;
    screen->cursor_col = 0;
}

void term_clear_line(term_screen_t* screen, uint32_t row) {
    if (!screen || row >= screen->rows) return;
    for (uint32_t c = 0; c < screen->cols; c++) {
        screen->cells[row][c].ch = ' ';
        screen->cells[row][c].fg = screen->fg_color;
        screen->cells[row][c].bg = screen->bg_color;
        screen->cells[row][c].attr = 0;
    }
}

void term_clear_region(term_screen_t* screen, uint32_t r1, uint32_t c1, uint32_t r2, uint32_t c2) {
    if (!screen) return;
    for (uint32_t r = r1; r <= r2 && r < screen->rows; r++)
        for (uint32_t c = c1; c <= c2 && c < screen->cols; c++) {
            screen->cells[r][c].ch = ' ';
            screen->cells[r][c].fg = screen->fg_color;
            screen->cells[r][c].bg = screen->bg_color;
        }
}

/* ---- Cursor ---- */

void term_set_cursor(term_screen_t* screen, uint32_t row, uint32_t col) {
    if (!screen) return;
    screen->cursor_row = (row < screen->rows) ? row : screen->rows - 1;
    screen->cursor_col = (col < screen->cols) ? col : screen->cols - 1;
}

void term_cursor_up(term_screen_t* screen, uint32_t n) {
    if (!screen) return;
    if (screen->cursor_row >= n)
        screen->cursor_row -= n;
    else
        screen->cursor_row = 0;
}

void term_cursor_down(term_screen_t* screen, uint32_t n) {
    if (!screen) return;
    screen->cursor_row += n;
    if (screen->cursor_row >= screen->rows)
        screen->cursor_row = screen->rows - 1;
}

void term_cursor_forward(term_screen_t* screen, uint32_t n) {
    if (!screen) return;
    screen->cursor_col += n;
    if (screen->cursor_col >= screen->cols) {
        screen->cursor_col = 0;
        if (screen->cursor_row < screen->rows - 1)
            screen->cursor_row++;
    }
}

void term_cursor_backward(term_screen_t* screen, uint32_t n) {
    if (!screen) return;
    if (screen->cursor_col >= n)
        screen->cursor_col -= n;
    else
        screen->cursor_col = 0;
}

void term_cursor_next_line(term_screen_t* screen) {
    if (!screen) return;
    screen->cursor_col = 0;
    if (screen->cursor_row < screen->rows - 1)
        screen->cursor_row++;
}

void term_cursor_prev_line(term_screen_t* screen) {
    if (!screen) return;
    screen->cursor_col = 0;
    if (screen->cursor_row > 0)
        screen->cursor_row--;
}

void term_cursor_horizontal_absolute(term_screen_t* screen, uint32_t col) {
    if (screen) screen->cursor_col = (col < screen->cols) ? col : screen->cols - 1;
}

void term_save_cursor(term_screen_t* screen) {
    if (!screen) return;
    screen->saved_row = screen->cursor_row;
    screen->saved_col = screen->cursor_col;
    screen->saved_fg = screen->fg_color;
    screen->saved_bg = screen->bg_color;
    screen->saved_attr = screen->attr;
}

void term_restore_cursor(term_screen_t* screen) {
    if (!screen) return;
    screen->cursor_row = screen->saved_row;
    screen->cursor_col = screen->saved_col;
    screen->fg_color = screen->saved_fg;
    screen->bg_color = screen->saved_bg;
    screen->attr = screen->saved_attr;
}

/* ---- Text output ---- */

static void term_advance(term_screen_t* screen) {
    screen->cursor_col++;
    if (screen->cursor_col >= screen->cols) {
        screen->cursor_col = 0;
        if (screen->cursor_row < screen->rows - 1)
            screen->cursor_row++;
        else
            term_scroll_up(screen, 1);
    }
}

void term_put_char(term_screen_t* screen, char c) {
    if (!screen) return;

    if (c == '\n') {
        term_cursor_next_line(screen);
        return;
    }
    if (c == '\r') {
        screen->cursor_col = 0;
        return;
    }
    if (c == '\t') {
        screen->cursor_col = (screen->cursor_col / TERM_TAB_SIZE + 1) * TERM_TAB_SIZE;
        if (screen->cursor_col >= screen->cols)
            term_cursor_next_line(screen);
        return;
    }
    if (c == '\b') {
        term_cursor_backward(screen, 1);
        return;
    }

    if (screen->cursor_row < screen->rows && screen->cursor_col < screen->cols) {
        screen->cells[screen->cursor_row][screen->cursor_col].ch = c;
        screen->cells[screen->cursor_row][screen->cursor_col].fg = screen->fg_color;
        screen->cells[screen->cursor_row][screen->cursor_col].bg = screen->bg_color;
        screen->cells[screen->cursor_row][screen->cursor_col].attr = screen->attr;
    }
    term_advance(screen);
}

void term_put_string(term_screen_t* screen, const char* str) {
    if (!screen || !str) return;
    while (*str) term_put_char(screen, *str++);
}

void term_write(term_screen_t* screen, const char* data, uint32_t len) {
    if (!screen || !data) return;
    for (uint32_t i = 0; i < len; i++)
        term_put_char(screen, data[i]);
}

/* ---- Scrolling ---- */

void term_scroll_up(term_screen_t* screen, uint32_t n) {
    if (!screen || n == 0) return;

    /* Save scrolled lines to scrollback */
    for (uint32_t i = 0; i < n; i++) {
        memcpy(screen->scrollback[screen->scrollback_head],
               screen->cells[screen->scroll_top + i],
               sizeof(term_cell_t) * screen->cols);
        screen->scrollback_head = (screen->scrollback_head + 1) % TERM_MAX_SCROLL;
        if (screen->scrollback_count < TERM_MAX_SCROLL)
            screen->scrollback_count++;
    }

    /* Shift lines up */
    for (uint32_t r = screen->scroll_top; r < screen->scroll_bottom - n + 1; r++)
        memcpy(screen->cells[r], screen->cells[r + n], sizeof(term_cell_t) * screen->cols);

    /* Clear new lines */
    for (uint32_t r = screen->scroll_bottom - n + 1; r <= screen->scroll_bottom; r++)
        term_clear_line(screen, r);
}

void term_scroll_down(term_screen_t* screen, uint32_t n) {
    if (!screen || n == 0) return;
    for (uint32_t r = screen->scroll_bottom; r >= screen->scroll_top + n; r--)
        memcpy(screen->cells[r], screen->cells[r - n], sizeof(term_cell_t) * screen->cols);
    for (uint32_t r = screen->scroll_top; r < screen->scroll_top + n; r++)
        term_clear_line(screen, r);
}

/* ---- Style ---- */

void term_set_fg(term_screen_t* screen, uint8_t color) {
    if (screen) screen->fg_color = color;
}

void term_set_bg(term_screen_t* screen, uint8_t color) {
    if (screen) screen->bg_color = color;
}

void term_set_attr(term_screen_t* screen, uint8_t attr) {
    if (screen) screen->attr = attr;
}

void term_reset_style(term_screen_t* screen) {
    if (!screen) return;
    screen->fg_color = 7;
    screen->bg_color = 0;
    screen->attr = 0;
}

/* ---- ANSI Parser ---- */

enum { ANSI_GROUND, ANSI_ESC, ANSI_CSI, ANSI_OSC };

void term_parse_ansi(terminal_t* term, char c) {
    if (!term) return;
    term_screen_t* scr = &term->screen;

    switch (term->ansi_state) {
        case ANSI_GROUND:
            if (c == '\033') {
                term->ansi_state = ANSI_ESC;
                term->ansi_param_count = 0;
                term->ansi_buf_len = 0;
            } else if (c == '\n' || c == '\r' || c == '\t' || c == '\b') {
                term_put_char(scr, c);
            } else {
                term_put_char(scr, c);
            }
            break;

        case ANSI_ESC:
            if (c == '[') {
                term->ansi_state = ANSI_CSI;
            } else if (c == ']') {
                term->ansi_state = ANSI_OSC;
            } else {
                term->ansi_state = ANSI_GROUND;
            }
            break;

        case ANSI_CSI:
            if (c >= '0' && c <= '9') {
                if (term->ansi_param_count < 16) {
                    term->ansi_params[term->ansi_param_count] =
                        term->ansi_params[term->ansi_param_count] * 10 + (c - '0');
                }
            } else if (c == ';') {
                term->ansi_param_count++;
            } else {
                term->ansi_param_count++;
                term_process_ansi(term);
                term->ansi_state = ANSI_GROUND;
            }
            break;

        case ANSI_OSC:
            if (c == '\007' || c == '\033') {
                /* Process OSC sequence */
                term->ansi_state = ANSI_GROUND;
            }
            break;
    }
}

void term_process_ansi(terminal_t* term) {
    if (!term) return;
    term_screen_t* scr = &term->screen;
    char cmd = term->ansi_buf_len > 0 ? term->ansi_buf[term->ansi_buf_len - 1] : '\0';

    /* Get last char from input buffer instead */
    /* The command character was the one that triggered this */

    int p0 = term->ansi_param_count > 0 ? term->ansi_params[0] : 0;
    int p1 = term->ansi_param_count > 1 ? term->ansi_params[1] : 0;

    /* Simple CSI handling based on last parameter */
    /* In real implementation, parse the final character */
    switch (p0) {
        case 0: term_clear(scr); break;
        case 1: term_set_cursor(scr, p1, 0); break;
        case 2: /* ED - erase display */ term_clear(scr); break;
        case 3: /* EL - erase line */ term_clear_line(scr, scr->cursor_row); break;
        case 4: term_cursor_up(scr, 1); break;
        case 5: term_cursor_down(scr, 1); break;
        case 6: term_cursor_forward(scr, 1); break;
        case 7: term_cursor_backward(scr, 1); break;
        case 8: term_save_cursor(scr); break;
        case 9: term_restore_cursor(scr); break;
        default:
            if (p0 >= 30 && p0 <= 37) term_set_fg(scr, p0 - 30);
            else if (p0 >= 40 && p0 <= 47) term_set_bg(scr, p0 - 40);
            else if (p0 == 0 || p0 == 39) term_reset_style(scr);
            break;
    }
}

/* ---- Input ---- */

void term_input_char(terminal_t* term, char c) {
    if (!term) return;
    if (term->input_len < TERM_MAX_INPUT - 1) {
        term->input_buf[term->input_len++] = c;
        term->input_buf[term->input_len] = '\0';
    }
    if (term->echo) term_put_char(&term->screen, c);
}

void term_input_string(terminal_t* term, const char* str) {
    if (!term || !str) return;
    while (*str) term_input_char(term, *str++);
}

char term_get_char(terminal_t* term) {
    if (!term || term->input_len == 0) return -1;
    char c = term->input_buf[0];
    for (uint32_t i = 0; i < term->input_len; i++)
        term->input_buf[i] = term->input_buf[i + 1];
    term->input_len--;
    return c;
}

int term_get_line(terminal_t* term, char* buf, uint32_t max) {
    if (!term || !buf) return -1;
    uint32_t i = 0;
    while (i < term->input_len && i < max - 1) {
        if (term->input_buf[i] == '\n' || term->input_buf[i] == '\r') {
            buf[i] = '\0';
            /* Remove from input */
            for (uint32_t j = i; j < term->input_len; j++)
                term->input_buf[j] = term->input_buf[j + 1];
            term->input_len--;
            return (int)i;
        }
        buf[i] = term->input_buf[i];
        i++;
    }
    buf[i] = '\0';
    return (int)i;
}

/* ---- Title ---- */

void term_set_title(terminal_t* term, const char* title) {
    if (term) string_copy(term->title, title, 64);
}

void term_set_size(terminal_t* term, uint32_t rows, uint32_t cols) {
    if (!term) return;
    term->screen.rows = (rows < TERM_MAX_ROWS) ? rows : TERM_MAX_ROWS;
    term->screen.cols = (cols < TERM_MAX_COLS) ? cols : TERM_MAX_COLS;
}

/* ---- Rendering ---- */

void term_render(terminal_t* term) {
    if (!term) return;
    term_screen_t* scr = &term->screen;

    /* In real implementation:
     * - Get window framebuffer
     * - Draw each cell as a character with colors
     * - Draw cursor if visible
     * - Draw scrollbar
     */
    for (uint32_t r = 0; r < scr->rows; r++) {
        for (uint32_t c = 0; c < scr->cols; c++) {
            term_cell_t* cell = &scr->cells[r][c];
            /* fb_draw_char(x + c*8, y + r*16, cell->ch, palette[cell->fg], palette[cell->bg]) */
        }
    }

    /* Draw cursor */
    if (scr->cursor_visible) {
        /* fb_draw_cursor(cursor_col * 8, cursor_row * 16) */
    }
}
