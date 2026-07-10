/**
 * file_manager.h — File Manager Application
 *
 * Graphical file manager with directory browsing, file operations.
 */
#ifndef ARCANIS_FILE_MANAGER_H
#define ARCANIS_FILE_MANAGER_H

#include <arcanis/types.h>
#include <arcanis/window.h>
#include <arcanis/gui.h>

#define FM_MAX_PATH      256
#define FM_MAX_ENTRIES    128
#define FM_MAX_NAME       64

typedef enum {
    FM_ENTRY_FILE,
    FM_ENTRY_DIR,
    FM_ENTRY_LINK,
    FM_ENTRY_EXEC
} fm_entry_type_t;

typedef struct {
    char            name[FM_MAX_NAME];
    fm_entry_type_t type;
    uint32_t        size;
    uint32_t        modified;  /* timestamp */
    uint32_t        mode;      /* permissions */
    int             selected;
} fm_entry_t;

typedef struct {
    char        path[FM_MAX_PATH];
    fm_entry_t  entries[FM_MAX_ENTRIES];
    uint32_t    num_entries;
    uint32_t    selected_idx;
    uint32_t    scroll_offset;
    int         show_hidden;
    int         sort_by_name;
    int         view_mode;  /* 0=list, 1=icons, 2=details */
} fm_directory_t;

typedef struct {
    wm_state_t*     wm;
    gui_state_t*    gui;
    uint32_t        window_id;
    fm_directory_t  current_dir;
    fm_directory_t  parent_dir;
    char            cwd[FM_MAX_PATH];

    /* Widget IDs */
    uint32_t    toolbar_id;
    uint32_t    file_list_id;
    uint32_t    path_label_id;
    uint32_t    status_label_id;
    uint32_t    up_btn_id;
    uint32_t    home_btn_id;
    uint32_t    refresh_btn_id;
    uint32_t    new_dir_btn_id;
    uint32_t    delete_btn_id;
    uint32_t    rename_btn_id;
    uint32_t    copy_btn_id;
    uint32_t    paste_btn_id;

    /* State */
    int         clipboard_active;
    char        clipboard_path[FM_MAX_PATH];
    int         clipboard_is_cut;
    char        status_msg[128];
} file_manager_t;

/* Initialize file manager */
int  fm_init(file_manager_t* fm, wm_state_t* wm, gui_state_t* gui);

/* Open a directory */
int  fm_open_dir(file_manager_t* fm, const char* path);

/* Navigation */
int  fm_go_up(file_manager_t* fm);
int  fm_go_home(file_manager_t* fm);
int  fm_go_to(file_manager_t* fm, const char* path);

/* File operations */
int  fm_create_dir(file_manager_t* fm, const char* name);
int  fm_delete(file_manager_t* fm, const char* name);
int  fm_rename(file_manager_t* fm, const char* old_name, const char* new_name);
int  fm_copy(file_manager_t* fm, const char* name, const char* dest);
int  fm_move(file_manager_t* fm, const char* name, const char* dest);

/* Selection */
void fm_select(file_manager_t* fm, uint32_t index);
void fm_select_all(file_manager_t* fm);
void fm_deselect_all(file_manager_t* fm);

/* View */
void fm_set_view_mode(file_manager_t* fm, int mode);
void fm_toggle_hidden(file_manager_t* fm);
void fm_scroll_up(file_manager_t* fm);
void fm_scroll_down(file_manager_t* fm);

/* Rendering */
void fm_render(file_manager_t* fm);
void fm_render_toolbar(file_manager_t* fm);
void fm_render_file_list(file_manager_t* fm);
void fm_render_status_bar(file_manager_t* fm);

/* Get entry icon character */
char fm_get_icon(fm_entry_type_t type, uint32_t mode);

#endif
