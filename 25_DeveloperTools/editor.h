/**
 * editor.h — Vi-like Text Editor
 *
 * Modal text editor with normal/insert/visual modes.
 * Supports file I/O, cursor movement, search, and basic editing.
 */
#ifndef ARCANIS_EDITOR_H
#define ARCANIS_EDITOR_H

#include <arcanis/types.h>

#define EDITOR_MAX_LINES    4096
#define EDITOR_MAX_LINE_LEN 256
#define EDITOR_MAX_UNDO     64

typedef enum {
    MODE_NORMAL,
    MODE_INSERT,
    MODE_VISUAL,
    MODE_COMMAND
} editor_mode_t;

typedef struct {
    char*    text;
    uint32_t len;
    uint32_t capacity;
} editor_line_t;

typedef struct {
    char*    old_text;
    uint32_t old_len;
    uint32_t line;
    uint32_t col;
} editor_undo_t;

typedef struct {
    char*        filename;
    editor_line_t* lines;
    uint32_t     num_lines;
    uint32_t     cursor_line;
    uint32_t     cursor_col;
    uint32_t     scroll_top;
    uint32_t     scroll_left;
    editor_mode_t mode;
    char         command_buf[128];
    uint32_t     command_len;
    char         search_buf[128];
    uint32_t     search_len;
    editor_undo_t undo_stack[EDITOR_MAX_UNDO];
    uint32_t     undo_top;
    uint32_t     undo_count;
    int          dirty;
    int          running;
    uint32_t     screen_rows;
    uint32_t     screen_cols;
    char         status_msg[128];
    char         filename_buf[256];
} editor_t;

/* Lifecycle */
int      editor_open(editor_t* ed, const char* filename);
int      editor_new(editor_t* ed);
void     editor_free(editor_t* ed);
void     editor_run(editor_t* ed);

/* Navigation */
void     editor_move_up(editor_t* ed);
void     editor_move_down(editor_t* ed);
void     editor_move_left(editor_t* ed);
void     editor_move_right(editor_t* ed);
void     editor_move_line_start(editor_t* ed);
void     editor_move_line_end(editor_t* ed);
void     editor_move_word_forward(editor_t* ed);
void     editor_move_word_backward(editor_t* ed);
void     editor_move_page_up(editor_t* ed);
void     editor_move_page_down(editor_t* ed);
void     editor_move_to_line(editor_t* ed, uint32_t line);
void     editor_move_to_end(editor_t* ed);

/* Editing */
void     editor_insert_char(editor_t* ed, char c);
void     editor_insert_line(editor_t* ed);
void     editor_delete_char(editor_t* ed);
void     editor_delete_line(editor_t* ed);
void     editor_delete_selection(editor_t* ed);
void     editor_join_lines(editor_t* ed);
void     editor_indent(editor_t* ed);
void     editor_unindent(editor_t* ed);

/* Undo/Redo */
void     editor_push_undo(editor_t* ed);
int      editor_undo(editor_t* ed);
int      editor_redo(editor_t* ed);

/* Search */
int      editor_search_forward(editor_t* ed, const char* pattern);
int      editor_search_backward(editor_t* ed, const char* pattern);

/* File I/O */
int      editor_save(editor_t* ed, const char* filename);
int      editor_load(editor_t* ed, const char* filename);

/* Display */
void     editor_refresh(editor_t* ed);
void     editor_draw_status(editor_t* ed);
void     editor_draw_command_line(editor_t* ed);
void     editor_set_status(editor_t* ed, const char* msg);

/* Commands */
void     editor_command(editor_t* ed, const char* cmd);

#endif
