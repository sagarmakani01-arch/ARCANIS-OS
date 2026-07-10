/**
 * window.h — Window Manager
 *
 * Tiling window manager with window creation, focus, and layout.
 * Supports floating and tiled window modes.
 */
#ifndef ARCANIS_WINDOW_H
#define ARCANIS_WINDOW_H

#include <arcanis/types.h>

#define WM_MAX_WINDOWS    64
#define WM_MAX_TITLE      64
#define WM_TASKBAR_HEIGHT 32
#define WM_SCREEN_WIDTH   1024
#define WM_SCREEN_HEIGHT  768

typedef enum {
    WIN_STATE_HIDDEN,
    WIN_STATE_VISIBLE,
    WIN_STATE_MINIMIZED,
    WIN_STATE_MAXIMIZED,
    WIN_STATE_FOCUSED
} win_state_t;

typedef enum {
    WIN_TYPE_NORMAL,
    WIN_TYPE_DIALOG,
    WIN_TYPE_PANEL,
    WIN_TYPE_TASKBAR,
    WIN_TYPE_DESKTOP
} win_type_t;

typedef enum {
    LAYOUT_TILED,
    LAYOUT_FLOATING,
    LAYOUT_MAXIMIZED
} layout_mode_t;

typedef struct {
    int32_t  x, y;
    uint32_t width, height;
} win_rect_t;

typedef struct {
    uint32_t win_id;
    char     title[WM_MAX_TITLE];
    win_rect_t rect;
    win_rect_t prev_rect;
    win_state_t state;
    win_type_t  type;
    int      pid;
    int      z_order;
    int      resizable;
    int      movable;
    int      has_border;
    uint32_t bg_color;
    uint32_t fg_color;
    uint32_t border_color;
    int      needs_redraw;
    void*    user_data;
} window_t;

typedef struct {
    window_t   windows[WM_MAX_WINDOWS];
    uint32_t   num_windows;
    uint32_t   active_window;
    uint32_t   next_id;
    layout_mode_t layout;
    int        taskbar_visible;
    win_rect_t taskbar;
    uint32_t   screen_width;
    uint32_t   screen_height;
    uint32_t   mouse_x;
    uint32_t   mouse_y;
    int        mouse_buttons;
    int        drag_window;
    int        drag_offset_x;
    int        drag_offset_y;
    uint32_t   desktop_color;
    void*      framebuffer;
} wm_state_t;

/* Initialize window manager */
void wm_init(wm_state_t* wm);

/* Window lifecycle */
uint32_t wm_create_window(wm_state_t* wm, const char* title,
                           uint32_t x, uint32_t y, uint32_t w, uint32_t h,
                           win_type_t type);
void     wm_destroy_window(wm_state_t* wm, uint32_t win_id);
void     wm_show_window(wm_state_t* wm, uint32_t win_id);
void     wm_hide_window(wm_state_t* wm, uint32_t win_id);
void     wm_minimize_window(wm_state_t* wm, uint32_t win_id);
void     wm_maximize_window(wm_state_t* wm, uint32_t win_id);
void     wm_restore_window(wm_state_t* wm, uint32_t win_id);

/* Focus management */
void     wm_focus_window(wm_state_t* wm, uint32_t win_id);
void     wm_unfocus_window(wm_state_t* wm, uint32_t win_id);
uint32_t wm_get_focused(wm_state_t* wm);

/* Window properties */
void     wm_set_title(wm_state_t* wm, uint32_t win_id, const char* title);
void     wm_set_position(wm_state_t* wm, uint32_t win_id, int32_t x, int32_t y);
void     wm_set_size(wm_state_t* wm, uint32_t win_id, uint32_t w, uint32_t h);
void     wm_set_colors(wm_state_t* wm, uint32_t win_id,
                        uint32_t bg, uint32_t fg, uint32_t border);

/* Layout */
void     wm_set_layout(wm_state_t* wm, layout_mode_t mode);
void     wm_tile_windows(wm_state_t* wm);
void     wm_cascade_windows(wm_state_t* wm);
void     wm_arrange(wm_state_t* wm);

/* Mouse handling */
void     wm_mouse_move(wm_state_t* wm, uint32_t x, uint32_t y);
void     wm_mouse_click(wm_state_t* wm, int button);
void     wm_mouse_release(wm_state_t* wm, int button);

/* Rendering */
void     wm_render(wm_state_t* wm);
void     wm_render_window(wm_state_t* wm, window_t* win);
void     wm_render_taskbar(wm_state_t* wm);
void     wm_render_title_bar(wm_state_t* wm, window_t* win);

/* Hit testing */
window_t* wm_hit_test(wm_state_t* wm, uint32_t x, uint32_t y);

/* Find window */
window_t* wm_find_window(wm_state_t* wm, uint32_t win_id);
window_t* wm_find_by_pid(wm_state_t* wm, int pid);

#endif
