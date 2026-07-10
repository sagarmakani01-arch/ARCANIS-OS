/**
 * window.c — Window Manager Implementation
 *
 * Tiling window manager with mouse support and window stacking.
 */
#include <arcanis/window.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

void wm_init(wm_state_t* wm) {
    if (!wm) return;
    memset(wm, 0, sizeof(wm_state_t));
    wm->screen_width = WM_SCREEN_WIDTH;
    wm->screen_height = WM_SCREEN_HEIGHT;
    wm->next_id = 1;
    wm->layout = LAYOUT_TILED;
    wm->taskbar_visible = 1;

    /* Taskbar geometry */
    wm->taskbar.x = 0;
    wm->taskbar.y = WM_SCREEN_HEIGHT - WM_TASKBAR_HEIGHT;
    wm->taskbar.width = WM_SCREEN_WIDTH;
    wm->taskbar.height = WM_TASKBAR_HEIGHT;

    /* Default colors */
    wm->desktop_color = 0x1E1E2E;
}

/* ---- Window lifecycle ---- */

uint32_t wm_create_window(wm_state_t* wm, const char* title,
                           uint32_t x, uint32_t y, uint32_t w, uint32_t h,
                           win_type_t type) {
    if (!wm || wm->num_windows >= WM_MAX_WINDOWS) return 0;

    window_t* win = &wm->windows[wm->num_windows];
    memset(win, 0, sizeof(window_t));

    win->win_id = wm->next_id++;
    string_copy(win->title, title, WM_MAX_TITLE);
    win->rect.x = x;
    win->rect.y = y;
    win->rect.width = w;
    win->rect.height = h;
    win->prev_rect = win->rect;
    win->state = WIN_STATE_VISIBLE;
    win->type = type;
    win->z_order = wm->num_windows;
    win->resizable = (type == WIN_TYPE_NORMAL);
    win->movable = (type != WIN_TYPE_TASKBAR && type != WIN_TYPE_DESKTOP);
    win->has_border = (type == WIN_TYPE_NORMAL || type == WIN_TYPE_DIALOG);

    /* Default colors by type */
    switch (type) {
        case WIN_TYPE_TASKBAR:
            win->bg_color = 0x313244;
            win->fg_color = 0xCDD6F4;
            win->border_color = 0x45475A;
            break;
        case WIN_TYPE_DIALOG:
            win->bg_color = 0x313244;
            win->fg_color = 0xCDD6F4;
            win->border_color = 0xF38BA8;
            break;
        case WIN_TYPE_PANEL:
            win->bg_color = 0x1E1E2E;
            win->fg_color = 0xBAC2DE;
            win->border_color = 0x585B70;
            break;
        default:
            win->bg_color = 0x1E1E2E;
            win->fg_color = 0xCDD6F4;
            win->border_color = 0x45475A;
            break;
    }

    wm->num_windows++;
    win->needs_redraw = 1;

    /* Auto-arrange if tiled */
    if (wm->layout == LAYOUT_TILED && type == WIN_TYPE_NORMAL)
        wm_tile_windows(wm);

    return win->win_id;
}

void wm_destroy_window(wm_state_t* wm, uint32_t win_id) {
    if (!wm) return;

    for (uint32_t i = 0; i < wm->num_windows; i++) {
        if (wm->windows[i].win_id == win_id) {
            /* Shift windows down */
            for (uint32_t j = i; j < wm->num_windows - 1; j++)
                wm->windows[j] = wm->windows[j + 1];
            wm->num_windows--;
            if (wm->active_window == win_id)
                wm->active_window = 0;
            if (wm->layout == LAYOUT_TILED)
                wm_tile_windows(wm);
            return;
        }
    }
}

void wm_show_window(wm_state_t* wm, uint32_t win_id) {
    window_t* win = wm_find_window(wm, win_id);
    if (win) { win->state = WIN_STATE_VISIBLE; win->needs_redraw = 1; }
}

void wm_hide_window(wm_state_t* wm, uint32_t win_id) {
    window_t* win = wm_find_window(wm, win_id);
    if (win) { win->state = WIN_STATE_HIDDEN; win->needs_redraw = 1; }
}

void wm_minimize_window(wm_state_t* wm, uint32_t win_id) {
    window_t* win = wm_find_window(wm, win_id);
    if (win) { win->state = WIN_STATE_MINIMIZED; win->needs_redraw = 1; }
}

void wm_maximize_window(wm_state_t* wm, uint32_t win_id) {
    window_t* win = wm_find_window(wm, win_id);
    if (!win) return;
    win->prev_rect = win->rect;
    win->rect.x = 0;
    win->rect.y = 0;
    win->rect.width = wm->screen_width;
    win->rect.height = wm->screen_height - (wm->taskbar_visible ? WM_TASKBAR_HEIGHT : 0);
    win->state = WIN_STATE_MAXIMIZED;
    win->needs_redraw = 1;
}

void wm_restore_window(wm_state_t* wm, uint32_t win_id) {
    window_t* win = wm_find_window(wm, win_id);
    if (!win) return;
    win->rect = win->prev_rect;
    win->state = WIN_STATE_VISIBLE;
    win->needs_redraw = 1;
}

/* ---- Focus ---- */

void wm_focus_window(wm_state_t* wm, uint32_t win_id) {
    if (!wm) return;

    /* Unfocus previous */
    if (wm->active_window) {
        window_t* prev = wm_find_window(wm, wm->active_window);
        if (prev) prev->state = WIN_STATE_VISIBLE;
    }

    /* Focus new */
    window_t* win = wm_find_window(wm, win_id);
    if (win) {
        win->state = WIN_STATE_FOCUSED;
        wm->active_window = win_id;
        /* Bring to front */
        win->z_order = wm->num_windows;
        win->needs_redraw = 1;
    }
}

void wm_unfocus_window(wm_state_t* wm, uint32_t win_id) {
    window_t* win = wm_find_window(wm, win_id);
    if (win) { win->state = WIN_STATE_VISIBLE; }
    if (wm->active_window == win_id) wm->active_window = 0;
}

uint32_t wm_get_focused(wm_state_t* wm) {
    return wm ? wm->active_window : 0;
}

/* ---- Properties ---- */

void wm_set_title(wm_state_t* wm, uint32_t win_id, const char* title) {
    window_t* win = wm_find_window(wm, win_id);
    if (win) { string_copy(win->title, title, WM_MAX_TITLE); win->needs_redraw = 1; }
}

void wm_set_position(wm_state_t* wm, uint32_t win_id, int32_t x, int32_t y) {
    window_t* win = wm_find_window(wm, win_id);
    if (win) { win->rect.x = x; win->rect.y = y; win->needs_redraw = 1; }
}

void wm_set_size(wm_state_t* wm, uint32_t win_id, uint32_t w, uint32_t h) {
    window_t* win = wm_find_window(wm, win_id);
    if (win) { win->rect.width = w; win->rect.height = h; win->needs_redraw = 1; }
}

void wm_set_colors(wm_state_t* wm, uint32_t win_id,
                    uint32_t bg, uint32_t fg, uint32_t border) {
    window_t* win = wm_find_window(wm, win_id);
    if (win) {
        win->bg_color = bg;
        win->fg_color = fg;
        win->border_color = border;
        win->needs_redraw = 1;
    }
}

/* ---- Layout ---- */

void wm_set_layout(wm_state_t* wm, layout_mode_t mode) {
    if (!wm) return;
    wm->layout = mode;
    wm_arrange(wm);
}

void wm_tile_windows(wm_state_t* wm) {
    if (!wm) return;

    uint32_t count = 0;
    for (uint32_t i = 0; i < wm->num_windows; i++) {
        if (wm->windows[i].type == WIN_TYPE_NORMAL &&
            wm->windows[i].state != WIN_STATE_HIDDEN &&
            wm->windows[i].state != WIN_STATE_MINIMIZED)
            count++;
    }
    if (count == 0) return;

    uint32_t usable_height = wm->screen_height -
        (wm->taskbar_visible ? WM_TASKBAR_HEIGHT : 0);
    uint32_t tile_w = wm->screen_width;
    uint32_t tile_h = usable_height / count;
    uint32_t idx = 0;

    for (uint32_t i = 0; i < wm->num_windows; i++) {
        window_t* win = &wm->windows[i];
        if (win->type == WIN_TYPE_NORMAL &&
            win->state != WIN_STATE_HIDDEN &&
            win->state != WIN_STATE_MINIMIZED) {
            win->prev_rect = win->rect;
            win->rect.x = 0;
            win->rect.y = idx * tile_h;
            win->rect.width = tile_w;
            win->rect.height = tile_h;
            win->needs_redraw = 1;
            idx++;
        }
    }
}

void wm_cascade_windows(wm_state_t* wm) {
    if (!wm) return;

    uint32_t offset = 0;
    for (uint32_t i = 0; i < wm->num_windows; i++) {
        window_t* win = &wm->windows[i];
        if (win->type == WIN_TYPE_NORMAL &&
            win->state != WIN_STATE_HIDDEN) {
            win->prev_rect = win->rect;
            win->rect.x = 30 + offset;
            win->rect.y = 30 + offset;
            if (win->rect.width < 400) win->rect.width = 400;
            if (win->rect.height < 300) win->rect.height = 300;
            win->needs_redraw = 1;
            offset += 30;
        }
    }
}

void wm_arrange(wm_state_t* wm) {
    if (!wm) return;
    switch (wm->layout) {
        case LAYOUT_TILED:     wm_tile_windows(wm);   break;
        case LAYOUT_FLOATING:  wm_cascade_windows(wm); break;
        case LAYOUT_MAXIMIZED:
            for (uint32_t i = 0; i < wm->num_windows; i++)
                if (wm->windows[i].type == WIN_TYPE_NORMAL)
                    wm_maximize_window(wm, wm->windows[i].win_id);
            break;
    }
}

/* ---- Mouse ---- */

void wm_mouse_move(wm_state_t* wm, uint32_t x, uint32_t y) {
    if (!wm) return;
    wm->mouse_x = x;
    wm->mouse_y = y;

    /* Handle drag */
    if (wm->drag_window && wm->mouse_buttons) {
        window_t* win = wm_find_window(wm, wm->drag_window);
        if (win && win->movable) {
            win->rect.x = x - wm->drag_offset_x;
            win->rect.y = y - wm->drag_offset_y;
            win->needs_redraw = 1;
        }
    }
}

void wm_mouse_click(wm_state_t* wm, int button) {
    if (!wm) return;
    wm->mouse_buttons |= (1 << button);

    /* Find window under cursor */
    window_t* win = wm_hit_test(wm, wm->mouse_x, wm->mouse_y);
    if (win) {
        wm_focus_window(wm, win->win_id);

        /* Start drag on title bar */
        if (win->movable && wm->mouse_y < win->rect.y + 24) {
            wm->drag_window = win->win_id;
            wm->drag_offset_x = wm->mouse_x - win->rect.x;
            wm->drag_offset_y = wm->mouse_y - win->rect.y;
        }
    } else {
        wm->active_window = 0;
    }
}

void wm_mouse_release(wm_state_t* wm, int button) {
    if (!wm) return;
    wm->mouse_buttons &= ~(1 << button);
    wm->drag_window = 0;
}

/* ---- Rendering ---- */

void wm_render_window(wm_state_t* wm, window_t* win) {
    if (!wm || !win || !win->needs_redraw) return;
    if (win->state == WIN_STATE_HIDDEN || win->state == WIN_STATE_MINIMIZED) return;

    /* Draw window background */
    /* In real implementation: fill_rect(fb, win->rect, win->bg_color) */

    /* Draw border */
    if (win->has_border) {
        /* draw_rect(fb, win->rect, win->border_color) */
    }

    /* Draw title bar */
    if (win->has_border) {
        /* Title bar background */
        uint32_t title_h = 24;
        /* fill_rect(fb, {win->rect.x, win->rect.y, win->rect.width, title_h}, 0x313244) */
        /* draw_text(fb, win->title, win->rect.x + 8, win->rect.y + 4, win->fg_color) */
    }

    win->needs_redraw = 0;
}

void wm_render_taskbar(wm_state_t* wm) {
    if (!wm || !wm->taskbar_visible) return;
    /* fill_rect(fb, wm->taskbar, 0x313244) */

    /* Draw window buttons */
    uint32_t btn_x = 4;
    for (uint32_t i = 0; i < wm->num_windows; i++) {
        window_t* win = &wm->windows[i];
        if (win->type == WIN_TYPE_NORMAL && win->state != WIN_STATE_HIDDEN) {
            uint32_t btn_w = 120;
            uint32_t btn_h = WM_TASKBAR_HEIGHT - 8;
            uint32_t btn_y = wm->taskbar.y + 4;

            /* Button background */
            uint32_t bg = (win->win_id == wm->active_window) ? 0x45475A : 0x313244;
            /* fill_rect(fb, {btn_x, btn_y, btn_w, btn_h}, bg) */

            /* Button text */
            /* draw_text(fb, win->title, btn_x + 4, btn_y + 4, 0xCDD6F4) */

            btn_x += btn_w + 4;
        }
    }
}

void wm_render(wm_state_t* wm) {
    if (!wm) return;

    /* Draw desktop background */
    /* fill_rect(fb, full_screen, wm->desktop_color) */

    /* Sort windows by z-order and render */
    for (uint32_t z = 0; z < wm->num_windows; z++) {
        for (uint32_t i = 0; i < wm->num_windows; i++) {
            if (wm->windows[i].z_order == (int)z)
                wm_render_window(wm, &wm->windows[i]);
        }
    }

    /* Draw taskbar on top */
    wm_render_taskbar(wm);

    /* Draw cursor */
    /* draw_cursor(fb, wm->mouse_x, wm->mouse_y) */
}

/* ---- Hit testing ---- */

window_t* wm_hit_test(wm_state_t* wm, uint32_t x, uint32_t y) {
    if (!wm) return NULL;

    /* Check windows in reverse z-order (top first) */
    for (int z = wm->num_windows - 1; z >= 0; z--) {
        for (uint32_t i = 0; i < wm->num_windows; i++) {
            window_t* win = &wm->windows[i];
            if (win->z_order == z &&
                win->state != WIN_STATE_HIDDEN &&
                win->state != WIN_STATE_MINIMIZED) {
                if (x >= (uint32_t)win->rect.x && x < win->rect.x + win->rect.width &&
                    y >= (uint32_t)win->rect.y && y < win->rect.y + win->rect.height) {
                    return win;
                }
            }
        }
    }
    return NULL;
}

/* ---- Find ---- */

window_t* wm_find_window(wm_state_t* wm, uint32_t win_id) {
    if (!wm) return NULL;
    for (uint32_t i = 0; i < wm->num_windows; i++)
        if (wm->windows[i].win_id == win_id)
            return &wm->windows[i];
    return NULL;
}

window_t* wm_find_by_pid(wm_state_t* wm, int pid) {
    if (!wm) return NULL;
    for (uint32_t i = 0; i < wm->num_windows; i++)
        if (wm->windows[i].pid == pid)
            return &wm->windows[i];
    return NULL;
}
