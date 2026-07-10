/**
 * terminal.h — Terminal Emulator
 *
 * ANSI terminal emulator with escape sequence parsing.
 * Supports colors, cursor movement, scrolling.
 */
#ifndef ARCANIS_TERMINAL_H
#define ARCANIS_TERMINAL_H

#include <arcanis/types.h>
#include <arcanis/window.h>

#define TERM_MAX_ROWS    50
#define TERM_MAX_COLS    120
#define TERM_MAX_SCROLL  1024
#define TERM_MAX_INPUT   256
#define TERM_TAB_SIZE    8

typedef enum {
    TERM_COLOR_BLACK = 0,
    TERM_COLOR_RED,
    TERM_COLOR_GREEN,
    TERM_COLOR_YELLOW,
    TERM_COLOR_BLUE,
    TERM_COLOR_MAGENTA,
    TERM_COLOR_CYAN,
    TERM_COLOR_WHITE,
    TERM_COLOR_BRIGHT_BLACK,
    TERM_COLOR_BRIGHT_RED,
    TERM_COLOR_BRIGHT_GREEN,
    TERM_COLOR_BRIGHT_YELLOW,
    TERM_COLOR_BRIGHT_BLUE,
    TERM_COLOR_BRIGHT_MAGENTA,
    TERM_COLOR_BRIGHT_CYAN,
    TERM_COLOR_BRIGHT_WHITE
} term_color_t;

typedef struct {
    char     ch;
    uint8_t  fg;
    uint8_t  bg;
    uint8_t  attr;  /* bold, underline, blink, etc. */
} term_cell_t;

typedef struct {
    term_cell_t cells[TERM_MAX_ROWS][TERM_MAX_COLS];
    uint32_t    rows;
    uint32_t    cols;
    uint32_t    cursor_row;
    uint32_t    cursor_col;
    uint32_t    scroll_top;
    uint32_t    scroll_bottom;
    uint8_t     fg_color;
    uint8_t     bg_color;
    uint8_t     attr;
    int         cursor_visible;
    int         insert_mode;
    int         wrap_mode;
    int         auto_scroll;
    uint32_t    saved_row;
    uint32_t    saved_col;
    uint8_t     saved_fg;
    uint8_t     saved_bg;
    uint8_t     saved_attr;
    /* Saved lines for scrolling */
    term_cell_t scrollback[TERM_MAX_SCROLL][TERM_MAX_COLS];
    uint32_t    scrollback_count;
    uint32_t    scrollback_head;
} term_screen_t;

typedef struct {
    wm_state_t*  wm;
    uint32_t     window_id;
    term_screen_t screen;
    char         input_buf[TERM_MAX_INPUT];
    uint32_t     input_len;
    int          input_mode;   /* 0=line, 1=raw */
    int          echo;
    int          running;
    /* ANSI parser state */
    int          ansi_state;
    int          ansi_params[16];
    int          ansi_param_count;
    char         ansi_buf[64];
    int          ansi_buf_len;
    /* Colors (ANSI 256 palette) */
    uint32_t     palette[256];
    /* Title */
    char         title[64];
    /* CWD */
    char         cwd[256];
} terminal_t;

/* Initialize terminal */
void term_init(terminal_t* term, wm_state_t* wm);

/* Screen operations */
void term_clear(term_screen_t* screen);
void term_clear_line(term_screen_t* screen, uint32_t row);
void term_clear_region(term_screen_t* screen, uint32_t r1, uint32_t c1, uint32_t r2, uint32_t c2);

/* Cursor movement */
void term_set_cursor(term_screen_t* screen, uint32_t row, uint32_t col);
void term_move_cursor(term_screen_t* screen, int dr, int dc);
void term_cursor_up(term_screen_t* screen, uint32_t n);
void term_cursor_down(term_screen_t* screen, uint32_t n);
void term_cursor_forward(term_screen_t* screen, uint32_t n);
void term_cursor_backward(term_screen_t* screen, uint32_t n);
void term_cursor_next_line(term_screen_t* screen);
void term_cursor_prev_line(term_screen_t* screen);
void term_cursor_horizontal_absolute(term_screen_t* screen, uint32_t col);
void term_save_cursor(term_screen_t* screen);
void term_restore_cursor(term_screen_t* screen);

/* Text output */
void term_put_char(term_screen_t* screen, char c);
void term_put_string(term_screen_t* screen, const char* str);
void term_write(term_screen_t* screen, const char* data, uint32_t len);

/* Scrolling */
void term_scroll_up(term_screen_t* screen, uint32_t n);
void term_scroll_down(term_screen_t* screen, uint32_t n);

/* Colors and attributes */
void term_set_fg(term_screen_t* screen, uint8_t color);
void term_set_bg(term_screen_t* screen, uint8_t color);
void term_set_attr(term_screen_t* screen, uint8_t attr);
void term_reset_style(term_screen_t* screen);

/* ANSI escape sequence parsing */
void term_parse_ansi(terminal_t* term, char c);
void term_process_ansi(terminal_t* term);

/* Input handling */
void term_input_char(terminal_t* term, char c);
void term_input_string(terminal_t* term, const char* str);
char term_get_char(terminal_t* term);
int  term_get_line(terminal_t* term, char* buf, uint32_t max);

/* Rendering */
void term_render(terminal_t* term);

/* Title and properties */
void term_set_title(terminal_t* term, const char* title);
void term_set_size(terminal_t* term, uint32_t rows, uint32_t cols);

#endif
