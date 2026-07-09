/**
 * editor.c — Vi-like Text Editor Implementation
 *
 * Full modal editor with normal/insert/visual modes.
 */
#include <arcanis/editor.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <arcanis/stdio.h>

/* ---- Helpers ---- */

static editor_line_t* editor_alloc_line(uint32_t capacity) {
    editor_line_t* line = (editor_line_t*)kmalloc(sizeof(editor_line_t));
    if (!line) return NULL;
    line->text = (char*)kmalloc(capacity);
    if (!line->text) { kfree(line); return NULL; }
    line->text[0] = '\0';
    line->len = 0;
    line->capacity = capacity;
    return line;
}

static void editor_insert_line_at(editor_t* ed, uint32_t index, const char* text, uint32_t len) {
    if (ed->num_lines >= EDITOR_MAX_LINES) return;
    if (index > ed->num_lines) index = ed->num_lines;

    /* Shift lines down */
    for (uint32_t i = ed->num_lines; i > index; i--)
        ed->lines[i] = ed->lines[i - 1];

    editor_line_t* line = editor_alloc_line(len + 1);
    if (!line) return;
    memcpy(line->text, text, len);
    line->text[len] = '\0';
    line->len = len;
    ed->lines[index] = line;
    ed->num_lines++;
}

static void editor_remove_line_at(editor_t* ed, uint32_t index) {
    if (index >= ed->num_lines) return;
    kfree(ed->lines[index]->text);
    kfree(ed->lines[index]);
    for (uint32_t i = index; i < ed->num_lines - 1; i++)
        ed->lines[i] = ed->lines[i + 1];
    ed->num_lines--;
}

/* ---- Lifecycle ---- */

int editor_new(editor_t* ed) {
    if (!ed) return -1;
    memset(ed, 0, sizeof(editor_t));
    ed->filename = NULL;
    ed->lines = (editor_line_t**)kmalloc(sizeof(editor_line_t*) * EDITOR_MAX_LINES);
    if (!ed->lines) return -1;
    ed->num_lines = 1;
    ed->lines[0] = editor_alloc_line(EDITOR_MAX_LINE_LEN);
    ed->cursor_line = 0;
    ed->cursor_col = 0;
    ed->mode = MODE_NORMAL;
    ed->running = 1;
    ed->dirty = 0;
    ed->screen_rows = 24;
    ed->screen_cols = 80;
    ed->undo_top = 0;
    ed->undo_count = 0;
    return 0;
}

int editor_open(editor_t* ed, const char* filename) {
    if (!ed || !filename) return -1;
    if (editor_new(ed) != 0) return -1;
    string_copy(ed->filename_buf, filename, 256);
    ed->filename = ed->filename_buf;
    return editor_load(ed, filename);
}

void editor_free(editor_t* ed) {
    if (!ed) return;
    for (uint32_t i = 0; i < ed->num_lines; i++) {
        if (ed->lines[i]) {
            kfree(ed->lines[i]->text);
            kfree(ed->lines[i]);
        }
    }
    kfree(ed->lines);
}

/* ---- Navigation ---- */

void editor_move_up(editor_t* ed) {
    if (ed->cursor_line > 0) ed->cursor_line--;
    uint32_t line_len = ed->lines[ed->cursor_line]->len;
    if (ed->cursor_col > line_len) ed->cursor_col = line_len;
}

void editor_move_down(editor_t* ed) {
    if (ed->cursor_line < ed->num_lines - 1) ed->cursor_line++;
    uint32_t line_len = ed->lines[ed->cursor_line]->len;
    if (ed->cursor_col > line_len) ed->cursor_col = line_len;
}

void editor_move_left(editor_t* ed) {
    if (ed->cursor_col > 0) ed->cursor_col--;
    else if (ed->cursor_line > 0) {
        ed->cursor_line--;
        ed->cursor_col = ed->lines[ed->cursor_line]->len;
    }
}

void editor_move_right(editor_t* ed) {
    uint32_t line_len = ed->lines[ed->cursor_line]->len;
    if (ed->cursor_col < line_len) ed->cursor_col++;
    else if (ed->cursor_line < ed->num_lines - 1) {
        ed->cursor_line++;
        ed->cursor_col = 0;
    }
}

void editor_move_line_start(editor_t* ed) { ed->cursor_col = 0; }
void editor_move_line_end(editor_t* ed)   { ed->cursor_col = ed->lines[ed->cursor_line]->len; }

void editor_move_word_forward(editor_t* ed) {
    char* text = ed->lines[ed->cursor_line]->text;
    uint32_t col = ed->cursor_col;
    while (col < ed->lines[ed->cursor_line]->len && text[col] == ' ') col++;
    while (col < ed->lines[ed->cursor_line]->len && text[col] != ' ') col++;
    ed->cursor_col = col;
}

void editor_move_word_backward(editor_t* ed) {
    char* text = ed->lines[ed->cursor_line]->text;
    uint32_t col = ed->cursor_col;
    if (col > 0) col--;
    while (col > 0 && text[col] == ' ') col--;
    while (col > 0 && text[col - 1] != ' ') col--;
    ed->cursor_col = col;
}

void editor_move_page_up(editor_t* ed) {
    uint32_t page = ed->screen_rows > 2 ? ed->screen_rows - 2 : 1;
    for (uint32_t i = 0; i < page && ed->cursor_line > 0; i++)
        editor_move_up(ed);
}

void editor_move_page_down(editor_t* ed) {
    uint32_t page = ed->screen_rows > 2 ? ed->screen_rows - 2 : 1;
    for (uint32_t i = 0; i < page && ed->cursor_line < ed->num_lines - 1; i++)
        editor_move_down(ed);
}

void editor_move_to_line(editor_t* ed, uint32_t line) {
    if (line < ed->num_lines) ed->cursor_line = line;
    ed->cursor_col = 0;
}

void editor_move_to_end(editor_t* ed) {
    ed->cursor_line = ed->num_lines - 1;
    ed->cursor_col = ed->lines[ed->cursor_line]->len;
}

/* ---- Editing ---- */

void editor_push_undo(editor_t* ed) {
    if (ed->undo_count >= EDITOR_MAX_UNDO) return;
    editor_undo_t* u = &ed->undo_stack[ed->undo_top];
    editor_line_t* line = ed->lines[ed->cursor_line];
    u->old_text = (char*)kmalloc(line->capacity);
    if (!u->old_text) return;
    memcpy(u->old_text, line->text, line->len + 1);
    u->old_len = line->len;
    u->line = ed->cursor_line;
    u->col = ed->cursor_col;
    ed->undo_top = (ed->undo_top + 1) % EDITOR_MAX_UNDO;
    ed->undo_count++;
}

void editor_insert_char(editor_t* ed, char c) {
    editor_line_t* line = ed->lines[ed->cursor_line];
    if (line->len >= line->capacity - 1) return;

    editor_push_undo(ed);
    /* Shift right */
    for (uint32_t i = line->len; i > ed->cursor_col; i--)
        line->text[i] = line->text[i - 1];
    line->text[ed->cursor_col] = c;
    line->len++;
    line->text[line->len] = '\0';
    ed->cursor_col++;
    ed->dirty = 1;
}

void editor_insert_line(editor_t* ed) {
    editor_push_undo(ed);
    editor_line_t* line = ed->lines[ed->cursor_line];
    uint32_t split_col = ed->cursor_col;

    /* Create new line from rest of current line */
    editor_insert_line_at(ed, ed->cursor_line + 1,
                          line->text + split_col,
                          line->len - split_col);

    /* Truncate current line */
    line->text[split_col] = '\0';
    line->len = split_col;

    ed->cursor_line++;
    ed->cursor_col = 0;
    ed->dirty = 1;
}

void editor_delete_char(editor_t* ed) {
    if (ed->cursor_col == 0 && ed->cursor_line == 0) return;
    editor_push_undo(ed);

    if (ed->cursor_col > 0) {
        editor_line_t* line = ed->lines[ed->cursor_line];
        for (uint32_t i = ed->cursor_col - 1; i < line->len - 1; i++)
            line->text[i] = line->text[i + 1];
        line->len--;
        line->text[line->len] = '\0';
        ed->cursor_col--;
    } else {
        /* Join with previous line */
        editor_line_t* prev = ed->lines[ed->cursor_line - 1];
        editor_line_t* curr = ed->lines[ed->cursor_line];
        uint32_t prev_len = prev->len;
        uint32_t new_len = prev_len + curr->len;
        if (new_len >= prev->capacity) {
            prev->text = (char*)krealloc(prev->text, new_len + 1);
            prev->capacity = new_len + 1;
        }
        memcpy(prev->text + prev_len, curr->text, curr->len);
        prev->len = new_len;
        prev->text[new_len] = '\0';
        editor_remove_line_at(ed, ed->cursor_line);
        ed->cursor_line--;
        ed->cursor_col = prev_len;
    }
    ed->dirty = 1;
}

void editor_delete_line(editor_t* ed) {
    if (ed->num_lines <= 1) return;
    editor_push_undo(ed);
    editor_remove_line_at(ed, ed->cursor_line);
    if (ed->cursor_line >= ed->num_lines)
        ed->cursor_line = ed->num_lines - 1;
    ed->cursor_col = 0;
    ed->dirty = 1;
}

void editor_join_lines(editor_t* ed) {
    if (ed->cursor_line >= ed->num_lines - 1) return;
    editor_push_undo(ed);
    editor_line_t* top = ed->lines[ed->cursor_line];
    editor_line_t* bottom = ed->lines[ed->cursor_line + 1];
    uint32_t new_len = top->len + bottom->len;
    if (new_len >= top->capacity) {
        top->text = (char*)krealloc(top->text, new_len + 1);
        top->capacity = new_len + 1;
    }
    memcpy(top->text + top->len, bottom->text, bottom->len);
    top->len = new_len;
    top->text[new_len] = '\0';
    editor_remove_line_at(ed, ed->cursor_line + 1);
    ed->dirty = 1;
}

void editor_indent(editor_t* ed) {
    editor_line_t* line = ed->lines[ed->cursor_line];
    if (line->len + 4 >= line->capacity) return;
    editor_push_undo(ed);
    for (uint32_t i = line->len; i > 0; i--)
        line->text[i + 4] = line->text[i];
    line->text[4] = line->text[0];
    for (int i = 0; i < 4; i++) line->text[i] = ' ';
    line->len += 4;
    ed->cursor_col += 4;
    ed->dirty = 1;
}

void editor_unindent(editor_t* ed) {
    editor_line_t* line = ed->lines[ed->cursor_line];
    if (line->len < 4) return;
    editor_push_undo(ed);
    uint32_t spaces = 0;
    while (spaces < 4 && line->text[spaces] == ' ') spaces++;
    if (spaces > 0) {
        for (uint32_t i = spaces; i < line->len; i++)
            line->text[i - spaces] = line->text[i];
        line->len -= spaces;
        line->text[line->len] = '\0';
        if (ed->cursor_col >= spaces) ed->cursor_col -= spaces;
        else ed->cursor_col = 0;
    }
    ed->dirty = 1;
}

int editor_undo(editor_t* ed) {
    if (ed->undo_count == 0) return -1;
    ed->undo_top = (ed->undo_top + EDITOR_MAX_UNDO - 1) % EDITOR_MAX_UNDO;
    ed->undo_count--;
    editor_undo_t* u = &ed->undo_stack[ed->undo_top];

    editor_line_t* line = ed->lines[u->line];
    kfree(line->text);
    line->text = u->old_text;
    line->len = u->old_len;
    line->capacity = u->old_len + 1;
    ed->cursor_line = u->line;
    ed->cursor_col = u->col;
    ed->dirty = 1;
    return 0;
}

int editor_redo(editor_t* ed) {
    return -1; /* Simplified: no redo */
}

/* ---- Search ---- */

int editor_search_forward(editor_t* ed, const char* pattern) {
    uint32_t plen = string_length(pattern);
    for (uint32_t i = ed->cursor_line; i < ed->num_lines; i++) {
        char* text = ed->lines[i]->text;
        uint32_t start = (i == ed->cursor_line) ? ed->cursor_col + 1 : 0;
        for (uint32_t j = start; j <= ed->lines[i]->len - plen; j++) {
            if (string_compare_n(text + j, pattern, plen) == 0) {
                ed->cursor_line = i;
                ed->cursor_col = j;
                return 0;
            }
        }
    }
    return -1;
}

int editor_search_backward(editor_t* ed, const char* pattern) {
    uint32_t plen = string_length(pattern);
    for (int i = ed->cursor_line; i >= 0; i--) {
        char* text = ed->lines[i]->text;
        uint32_t end = (i == (int)ed->cursor_line) ? ed->cursor_col : ed->lines[i]->len - plen;
        for (int j = (int)end; j >= 0; j--) {
            if (string_compare_n(text + j, pattern, plen) == 0) {
                ed->cursor_line = i;
                ed->cursor_col = j;
                return 0;
            }
        }
    }
    return -1;
}

/* ---- File I/O ---- */

int editor_save(editor_t* ed, const char* filename) {
    if (!filename && !ed->filename) return -1;
    const char* fn = filename ? filename : ed->filename;

    FILE* f = fopen(fn, "w");
    if (!f) return -1;
    for (uint32_t i = 0; i < ed->num_lines; i++) {
        fwrite(ed->lines[i]->text, 1, ed->lines[i]->len, f);
        if (i < ed->num_lines - 1) fputc('\n', f);
    }
    fclose(f);
    ed->dirty = 0;
    string_copy(ed->filename_buf, fn, 256);
    ed->filename = ed->filename_buf;
    return 0;
}

int editor_load(editor_t* ed, const char* filename) {
    FILE* f = fopen(filename, "r");
    if (!f) return -1;

    /* Free existing lines */
    for (uint32_t i = 0; i < ed->num_lines; i++) {
        kfree(ed->lines[i]->text);
        kfree(ed->lines[i]);
    }
    ed->num_lines = 0;

    char line_buf[EDITOR_MAX_LINE_LEN];
    while (fgets(line_buf, EDITOR_MAX_LINE_LEN, f)) {
        uint32_t len = string_length(line_buf);
        /* Remove trailing newline */
        if (len > 0 && line_buf[len - 1] == '\n') len--;
        editor_insert_line_at(ed, ed->num_lines, line_buf, len);
    }
    fclose(f);
    ed->dirty = 0;
    ed->cursor_line = 0;
    ed->cursor_col = 0;
    return 0;
}

/* ---- Display (Text Mode) ---- */

void editor_refresh(editor_t* ed) {
    /* Update scroll */
    if (ed->cursor_line < ed->scroll_top)
        ed->scroll_top = ed->cursor_line;
    if (ed->cursor_line >= ed->scroll_top + ed->screen_rows - 2)
        ed->scroll_top = ed->cursor_line - ed->screen_rows + 3;
    if (ed->cursor_col < ed->scroll_left)
        ed->scroll_left = ed->cursor_col;
    if (ed->cursor_col >= ed->scroll_left + ed->screen_cols)
        ed->scroll_left = ed->cursor_col - ed->screen_cols + 1;
}

void editor_draw_status(editor_t* ed) {
    char status[128];
    const char* mode_str;
    switch (ed->mode) {
        case MODE_NORMAL:  mode_str = "NORMAL";  break;
        case MODE_INSERT:  mode_str = "INSERT";  break;
        case MODE_VISUAL:  mode_str = "VISUAL";  break;
        case MODE_COMMAND: mode_str = "COMMAND";  break;
        default:           mode_str = "???";      break;
    }
    string_format(status, " [%s] %s | %d:%d | %d lines%s",
                  mode_str,
                  ed->filename ? ed->filename : "[No Name]",
                  ed->cursor_line + 1, ed->cursor_col + 1,
                  ed->num_lines,
                  ed->dirty ? " [+]" : "");
    printf("\n%s", status);
}

void editor_draw_command_line(editor_t* ed) {
    if (ed->mode == MODE_COMMAND) {
        printf("\n:%s", ed->command_buf);
    } else if (ed->status_msg[0]) {
        printf("\n%s", ed->status_msg);
    }
}

void editor_set_status(editor_t* ed, const char* msg) {
    string_copy(ed->status_msg, msg, 128);
}

/* ---- Commands ---- */

void editor_command(editor_t* ed, const char* cmd) {
    if (cmd[0] == 'w' && cmd[1] == '\0') {
        /* :w */
        if (editor_save(ed, NULL) == 0)
            editor_set_status(ed, "Written");
        else
            editor_set_status(ed, "Error writing file");
    } else if (cmd[0] == 'w' && cmd[1] == 'q' && cmd[2] == '\0') {
        /* :wq */
        if (editor_save(ed, NULL) == 0)
            ed->running = 0;
    } else if (cmd[0] == 'q' && cmd[1] == '!' && cmd[2] == '\0') {
        /* :q! */
        ed->running = 0;
    } else if (cmd[0] == 'q' && cmd[1] == '\0') {
        /* :q */
        if (ed->dirty) editor_set_status(ed, "No write (use :q! to quit)");
        else ed->running = 0;
    } else if (cmd[0] == 'e' && cmd[1] == ' ' && cmd[2]) {
        /* :e filename */
        if (editor_load(ed, cmd + 2) == 0)
            editor_set_status(ed, "Loaded");
        else
            editor_set_status(ed, "Error loading file");
    } else if (cmd[0] >= '0' && cmd[0] <= '9') {
        /* :42 — go to line */
        uint32_t line = 0;
        uint32_t i = 0;
        while (cmd[i] >= '0' && cmd[i] <= '9') {
            line = line * 10 + (cmd[i] - '0');
            i++;
        }
        if (line > 0) editor_move_to_line(ed, line - 1);
    } else if (cmd[0] == 's' && cmd[1] == 'e' && cmd[2] == 't' && cmd[3] == ' ') {
        /* :set options */
        editor_set_status(ed, "Set option");
    } else if (string_compare_n(cmd, "help", 4) == 0) {
        editor_set_status(ed, ":w save :wq save+quit :q! quit :e file :set opt");
    } else {
        editor_set_status(ed, "Unknown command");
    }
}

/* ---- Main Loop ---- */

void editor_run(editor_t* ed) {
    while (ed->running) {
        editor_refresh(ed);

        /* Display lines */
        printf("\033[2J\033[H"); /* Clear screen */
        for (uint32_t i = 0; i < ed->screen_rows - 2 && ed->scroll_top + i < ed->num_lines; i++) {
            uint32_t line_idx = ed->scroll_top + i;
            char* text = ed->lines[line_idx]->text;
            uint32_t len = ed->lines[line_idx]->len;
            uint32_t start = ed->scroll_left;
            uint32_t display_len = (len > start) ? len - start : 0;
            if (display_len > ed->screen_cols) display_len = ed->screen_cols;
            if (display_len > 0) {
                for (uint32_t j = 0; j < display_len; j++)
                    putchar(text[start + j]);
            }
            printf("\r\n");
        }
        /* Fill empty lines */
        for (uint32_t i = ed->num_lines; i < ed->screen_rows - 1; i++)
            printf("~\r\n");

        editor_draw_status(ed);
        editor_draw_command_line(ed);

        /* Get input */
        char c = getchar();

        if (ed->mode == MODE_NORMAL) {
            switch (c) {
                case 'h': editor_move_left(ed); break;
                case 'j': editor_move_down(ed); break;
                case 'k': editor_move_up(ed); break;
                case 'l': editor_move_right(ed); break;
                case '0': editor_move_line_start(ed); break;
                case '$': editor_move_line_end(ed); break;
                case 'w': editor_move_word_forward(ed); break;
                case 'b': editor_move_word_backward(ed); break;
                case 'x': editor_delete_char(ed); break;
                case 'd': editor_delete_line(ed); break;
                case 'J': editor_join_lines(ed); break;
                case '>': editor_indent(ed); break;
                case '<': editor_unindent(ed); break;
                case 'u': editor_undo(ed); break;
                case 'p': break; /* paste */
                case 'v': ed->mode = MODE_VISUAL; break;
                case 'i': ed->mode = MODE_INSERT; break;
                case 'I': ed->mode = MODE_INSERT; editor_move_line_start(ed); break;
                case 'a': ed->mode = MODE_INSERT; editor_move_right(ed); break;
                case 'A': ed->mode = MODE_INSERT; editor_move_line_end(ed); break;
                case 'o': ed->mode = MODE_INSERT;
                    editor_insert_line_at(ed, ed->cursor_line + 1, "", 0);
                    ed->cursor_line++;
                    ed->cursor_col = 0;
                    break;
                case 'O': ed->mode = MODE_INSERT;
                    editor_insert_line_at(ed, ed->cursor_line, "", 0);
                    ed->cursor_col = 0;
                    break;
                case ':': ed->mode = MODE_COMMAND;
                    ed->command_len = 0;
                    ed->command_buf[0] = '\0';
                    break;
                case '/': ed->mode = MODE_COMMAND;
                    ed->command_len = 0;
                    ed->command_buf[0] = '\0';
                    break;
                case 'q': ed->running = 0; break;
                case 'G': editor_move_to_end(ed); break;
                case 'g': {
                    char next = getchar();
                    if (next == 'g') editor_move_to_line(ed, 0);
                    break;
                }
                case '\x1b': /* ESC */
                    break;
            }
        } else if (ed->mode == MODE_INSERT) {
            if (c == '\x1b') {
                ed->mode = MODE_NORMAL;
                if (ed->cursor_col > 0) ed->cursor_col--;
            } else if (c == '\r' || c == '\n') {
                editor_insert_line(ed);
            } else if (c == '\t') {
                for (int i = 0; i < 4; i++)
                    editor_insert_char(ed, ' ');
            } else if (c == 127 || c == '\b') {
                editor_delete_char(ed);
            } else if (c >= 32) {
                editor_insert_char(ed, c);
            }
        } else if (ed->mode == MODE_VISUAL) {
            if (c == '\x1b') ed->mode = MODE_NORMAL;
            else if (c == 'h') editor_move_left(ed);
            else if (c == 'j') editor_move_down(ed);
            else if (c == 'k') editor_move_up(ed);
            else if (c == 'l') editor_move_right(ed);
            else if (c == 'd') editor_delete_selection(ed);
            else if (c == 'y') { /* yank */ ed->mode = MODE_NORMAL; }
        } else if (ed->mode == MODE_COMMAND) {
            if (c == '\r') {
                ed->command_buf[ed->command_len] = '\0';
                if (ed->command_buf[0] == '/') {
                    /* Search */
                    editor_search_forward(ed, ed->command_buf + 1);
                } else {
                    editor_command(ed, ed->command_buf);
                }
                ed->mode = MODE_NORMAL;
            } else if (c == '\x1b') {
                ed->mode = MODE_NORMAL;
            } else if (c == 127 || c == '\b') {
                if (ed->command_len > 0) ed->command_len--;
            } else if (c >= 32 && ed->command_len < 127) {
                ed->command_buf[ed->command_len++] = c;
            }
        }
    }
}
