/**
 * gui.c — GUI Toolkit Implementation
 *
 * Widget system with event handling and rendering.
 */
#include <arcanis/gui.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

/* ---- Colors ---- */
#define COLOR_BG       0x1E1E2E
#define COLOR_FG       0xCDD6F4
#define COLOR_BORDER   0x45475A
#define COLOR_HOVER    0x585B70
#define COLOR_FOCUS    0x89B4FA
#define COLOR_BUTTON   0x45475A
#define COLOR_PRESSED  0x313244
#define COLOR_TEXTBOX  0x11111B
#define COLOR_PROGRESS 0xA6E3A1
#define COLOR_CHECKBOX 0x89B4FA
#define COLOR_MENU     0x313244

/* ---- Init ---- */

void gui_init(gui_state_t* gui, wm_state_t* wm) {
    if (!gui) return;
    memset(gui, 0, sizeof(gui_state_t));
    gui->wm = wm;
    gui->next_id = 1;
}

/* ---- Widget creation ---- */

static uint32_t gui_alloc_widget(gui_state_t* gui) {
    if (gui->num_widgets >= GUI_MAX_WIDGETS) return 0;
    widget_t* w = &gui->widgets[gui->num_widgets];
    memset(w, 0, sizeof(widget_t));
    w->id = gui->next_id++;
    w->visible = 1;
    w->enabled = 1;
    w->font_size = 14;
    gui->num_widgets++;
    return w->id;
}

uint32_t gui_create_button(gui_state_t* gui, const char* text, int x, int y, uint32_t w, uint32_t h) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* btn = gui_find_widget(gui, id);
    btn->type = WIDGET_BUTTON;
    string_copy(btn->text, text, GUI_MAX_TEXT);
    btn->x = x; btn->y = y; btn->width = w; btn->height = h;
    btn->bg_color = COLOR_BUTTON; btn->fg_color = COLOR_FG; btn->border_color = COLOR_BORDER;
    btn->hover_color = COLOR_HOVER; btn->button.press_color = COLOR_PRESSED;
    btn->text_align = 1;
    return id;
}

uint32_t gui_create_label(gui_state_t* gui, const char* text, int x, int y) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* lbl = gui_find_widget(gui, id);
    lbl->type = WIDGET_LABEL;
    string_copy(lbl->text, text, GUI_MAX_TEXT);
    lbl->x = x; lbl->y = y; lbl->width = string_length(text) * 8 + 8; lbl->height = 20;
    lbl->bg_color = COLOR_BG; lbl->fg_color = COLOR_FG; lbl->border_color = 0;
    return id;
}

uint32_t gui_create_textbox(gui_state_t* gui, const char* text, int x, int y, uint32_t w, uint32_t h) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* tb = gui_find_widget(gui, id);
    tb->type = WIDGET_TEXTBOX;
    string_copy(tb->text, text ? text : "", GUI_MAX_TEXT);
    tb->x = x; tb->y = y; tb->width = w; tb->height = h;
    tb->bg_color = COLOR_TEXTBOX; tb->fg_color = COLOR_FG; tb->border_color = COLOR_BORDER;
    tb->textbox.cursor_pos = string_length(tb->text);
    tb->textbox.max_length = 255;
    return id;
}

uint32_t gui_create_checkbox(gui_state_t* gui, const char* text, int x, int y) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* cb = gui_find_widget(gui, id);
    cb->type = WIDGET_CHECKBOX;
    string_copy(cb->text, text, GUI_MAX_TEXT);
    cb->x = x; cb->y = y; cb->width = 200; cb->height = 24;
    cb->bg_color = COLOR_BG; cb->fg_color = COLOR_FG; cb->border_color = COLOR_BORDER;
    cb->checkbox.checked = 0;
    return id;
}

uint32_t gui_create_combobox(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* cb = gui_find_widget(gui, id);
    cb->type = WIDGET_COMBOBOX;
    cb->x = x; cb->y = y; cb->width = w; cb->height = h;
    cb->bg_color = COLOR_TEXTBOX; cb->fg_color = COLOR_FG; cb->border_color = COLOR_BORDER;
    cb->combobox.selected = 0;
    cb->combobox.dropped_down = 0;
    return id;
}

uint32_t gui_create_progress(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* pg = gui_find_widget(gui, id);
    pg->type = WIDGET_PROGRESS;
    pg->x = x; pg->y = y; pg->width = w; pg->height = h;
    pg->bg_color = COLOR_BORDER; pg->fg_color = COLOR_PROGRESS; pg->border_color = COLOR_BORDER;
    pg->progress.value = 0; pg->progress.max_value = 100;
    return id;
}

uint32_t gui_create_slider(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h, int vertical) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* sl = gui_find_widget(gui, id);
    sl->type = WIDGET_SLIDER;
    sl->x = x; sl->y = y; sl->width = w; sl->height = h;
    sl->bg_color = COLOR_BORDER; sl->fg_color = COLOR_FOCUS; sl->border_color = COLOR_BORDER;
    sl->slider.min_val = 0; sl->slider.max_val = 100; sl->slider.current = 50;
    sl->slider.vertical = vertical;
    return id;
}

uint32_t gui_create_panel(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* pnl = gui_find_widget(gui, id);
    pnl->type = WIDGET_PANEL;
    pnl->x = x; pnl->y = y; pnl->width = w; pnl->height = h;
    pnl->bg_color = 0x181825; pnl->fg_color = COLOR_FG; pnl->border_color = COLOR_BORDER;
    return id;
}

uint32_t gui_create_menu(gui_state_t* gui, int x, int y, uint32_t w) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* mn = gui_find_widget(gui, id);
    mn->type = WIDGET_MENU;
    mn->x = x; mn->y = y; mn->width = w; mn->height = 28;
    mn->bg_color = COLOR_MENU; mn->fg_color = COLOR_FG; mn->border_color = COLOR_BORDER;
    mn->menu.selected = 0;
    return id;
}

uint32_t gui_create_list(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* ls = gui_find_widget(gui, id);
    ls->type = WIDGET_LIST;
    ls->x = x; ls->y = y; ls->width = w; ls->height = h;
    ls->bg_color = COLOR_TEXTBOX; ls->fg_color = COLOR_FG; ls->border_color = COLOR_BORDER;
    ls->list.selected = 0;
    return id;
}

uint32_t gui_create_tabs(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h) {
    uint32_t id = gui_alloc_widget(gui);
    if (!id) return 0;
    widget_t* tb = gui_find_widget(gui, id);
    tb->type = WIDGET_TABS;
    tb->x = x; tb->y = y; tb->width = w; tb->height = h;
    tb->bg_color = 0x181825; tb->fg_color = COLOR_FG; tb->border_color = COLOR_BORDER;
    tb->tabs.active_tab = 0;
    return id;
}

/* ---- Properties ---- */

void gui_set_text(gui_state_t* gui, uint32_t id, const char* text) {
    widget_t* w = gui_find_widget(gui, id);
    if (w) string_copy(w->text, text, GUI_MAX_TEXT);
}

void gui_set_position(gui_state_t* gui, uint32_t id, int x, int y) {
    widget_t* w = gui_find_widget(gui, id);
    if (w) { w->x = x; w->y = y; }
}

void gui_set_size(gui_state_t* gui, uint32_t id, uint32_t w, uint32_t h) {
    widget_t* wid = gui_find_widget(gui, id);
    if (wid) { wid->width = w; wid->height = h; }
}

void gui_set_colors(gui_state_t* gui, uint32_t id,
                     uint32_t bg, uint32_t fg, uint32_t border) {
    widget_t* w = gui_find_widget(gui, id);
    if (w) { w->bg_color = bg; w->fg_color = fg; w->border_color = border; }
}

void gui_set_visible(gui_state_t* gui, uint32_t id, int visible) {
    widget_t* w = gui_find_widget(gui, id);
    if (w) w->visible = visible;
}

void gui_set_enabled(gui_state_t* gui, uint32_t id, int enabled) {
    widget_t* w = gui_find_widget(gui, id);
    if (w) w->enabled = enabled;
}

/* ---- Widget actions ---- */

void gui_button_press(gui_state_t* gui, uint32_t id) {
    widget_t* w = gui_find_widget(gui, id);
    if (w && w->type == WIDGET_BUTTON && w->enabled) {
        w->button.pressed = 1;
        if (w->on_click) {
            event_t ev = { .type = EVENT_CLICK, .widget_id = id };
            w->on_click(&ev);
        }
    }
}

void gui_textbox_insert(gui_state_t* gui, uint32_t id, char c) {
    widget_t* w = gui_find_widget(gui, id);
    if (!w || w->type != WIDGET_TEXTBOX || !w->enabled) return;
    uint32_t len = string_length(w->text);
    if (len >= w->textbox.max_length) return;
    /* Shift right */
    for (uint32_t i = len; i > w->textbox.cursor_pos; i--)
        w->text[i] = w->text[i - 1];
    w->text[w->textbox.cursor_pos] = c;
    w->textbox.cursor_pos++;
}

void gui_textbox_delete(gui_state_t* gui, uint32_t id) {
    widget_t* w = gui_find_widget(gui, id);
    if (!w || w->type != WIDGET_TEXTBOX || w->textbox.cursor_pos == 0) return;
    uint32_t len = string_length(w->text);
    for (uint32_t i = w->textbox.cursor_pos - 1; i < len - 1; i++)
        w->text[i] = w->text[i + 1];
    w->text[len - 1] = '\0';
    w->textbox.cursor_pos--;
}

void gui_checkbox_toggle(gui_state_t* gui, uint32_t id) {
    widget_t* w = gui_find_widget(gui, id);
    if (w && w->type == WIDGET_CHECKBOX && w->enabled) {
        w->checkbox.checked = !w->checkbox.checked;
        if (w->on_change) {
            event_t ev = { .type = EVENT_CHANGE, .widget_id = id };
            w->on_change(&ev);
        }
    }
}

void gui_progress_set(gui_state_t* gui, uint32_t id, uint32_t value) {
    widget_t* w = gui_find_widget(gui, id);
    if (w && w->type == WIDGET_PROGRESS)
        w->progress.value = (value > w->progress.max_value) ? w->progress.max_value : value;
}

void gui_slider_set(gui_state_t* gui, uint32_t id, int32_t value) {
    widget_t* w = gui_find_widget(gui, id);
    if (w && w->type == WIDGET_SLIDER) {
        if (value < w->slider.min_val) value = w->slider.min_val;
        if (value > w->slider.max_val) value = w->slider.max_val;
        w->slider.current = value;
    }
}

void gui_combobox_add(gui_state_t* gui, uint32_t id, const char* item) {
    widget_t* w = gui_find_widget(gui, id);
    if (w && w->type == WIDGET_COMBOBOX && w->combobox.num_items < GUI_MAX_CHILDREN) {
        string_copy(w->combobox.items[w->combobox.num_items++], item, GUI_MAX_TEXT);
    }
}

void gui_list_add(gui_state_t* gui, uint32_t id, const char* item) {
    widget_t* w = gui_find_widget(gui, id);
    if (w && w->type == WIDGET_LIST && w->list.num_items < GUI_MAX_LIST_ITEMS) {
        string_copy(w->list.items[w->list.num_items++], item, GUI_MAX_TEXT);
    }
}

void gui_tabs_add(gui_state_t* gui, uint32_t id, const char* label) {
    widget_t* w = gui_find_widget(gui, id);
    if (w && w->type == WIDGET_TABS && w->tabs.num_tabs < 16) {
        string_copy(w->tabs.labels[w->tabs.num_tabs++], label, GUI_MAX_TEXT);
    }
}

void gui_menu_add(gui_state_t* gui, uint32_t id, const char* item) {
    widget_t* w = gui_find_widget(gui, id);
    if (w && w->type == WIDGET_MENU && w->menu.num_items < GUI_MAX_MENU_ITEMS) {
        string_copy(w->menu.items[w->menu.num_items++], item, GUI_MAX_TEXT);
    }
}

/* ---- Event handling ---- */

void gui_handle_click(gui_state_t* gui, uint32_t x, uint32_t y) {
    if (!gui) return;
    widget_t* w = gui_hit_test(gui, x, y);
    if (w && w->enabled) {
        gui->focused_widget = w->id;
        w->focused = 1;

        switch (w->type) {
            case WIDGET_BUTTON:
                gui_button_press(gui, w->id);
                break;
            case WIDGET_CHECKBOX:
                gui_checkbox_toggle(gui, w->id);
                break;
            case WIDGET_COMBOBOX:
                w->combobox.dropped_down = !w->combobox.dropped_down;
                break;
            case WIDGET_LIST: {
                uint32_t row = (y - w->y) / 20;
                if (row < w->list.num_items)
                    w->list.selected = row;
                break;
            }
            case WIDGET_SLIDER: {
                int32_t range = w->slider.max_val - w->slider.min_val;
                int32_t pos;
                if (w->slider.vertical)
                    pos = (y - w->y) * range / w->height;
                else
                    pos = (x - w->x) * range / w->width;
                gui_slider_set(gui, w->id, w->slider.min_val + pos);
                break;
            }
            case WIDGET_MENU: {
                uint32_t item = (x - w->x) / 80;
                if (item < w->menu.num_items)
                    w->menu.selected = item;
                break;
            }
            case WIDGET_TABS: {
                uint32_t tab_w = w->width / w->tabs.num_tabs;
                uint32_t tab = (x - w->x) / tab_w;
                if (tab < w->tabs.num_tabs)
                    w->tabs.active_tab = tab;
                break;
            }
            default:
                break;
        }
    }
}

void gui_handle_key(gui_state_t* gui, int key) {
    if (!gui || gui->focused_widget == 0) return;
    widget_t* w = gui_find_widget(gui, gui->focused_widget);
    if (!w || !w->enabled) return;

    if (w->type == WIDGET_TEXTBOX) {
        if (key == '\b' || key == 127) {
            gui_textbox_delete(gui, w->id);
        } else if (key == 13) {
            /* Enter - multiline support */
        } else if (key >= 32) {
            gui_textbox_insert(gui, w->id, (char)key);
        }
        if (w->on_key) {
            event_t ev = { .type = EVENT_KEY, .widget_id = w->id, .key = key };
            w->on_key(&ev);
        }
    }
}

void gui_handle_hover(gui_state_t* gui, uint32_t x, uint32_t y) {
    if (!gui) return;
    widget_t* w = gui_hit_test(gui, x, y);
    if (gui->hovered_widget) {
        widget_t* prev = gui_find_widget(gui, gui->hovered_widget);
        if (prev) prev->hovered = 0;
    }
    if (w) {
        w->hovered = 1;
        gui->hovered_widget = w->id;
    } else {
        gui->hovered_widget = 0;
    }
}

/* ---- Rendering ---- */

void gui_render_button(gui_state_t* gui, widget_t* w) {
    /* Simulated: draw filled rect + text */
    /* In real impl: fill_rect(fb, w->rect, w->pressed ? press : bg) */
    /* draw_text(fb, w->text, center, w->fg) */
}

void gui_render_label(gui_state_t* gui, widget_t* w) {
    /* draw_text(fb, w->text, w->x, w->y, w->fg) */
}

void gui_render_textbox(gui_state_t* gui, widget_t* w) {
    /* fill_rect(fb, w->rect, w->bg) */
    /* draw_text(fb, w->text, w->x+4, w->y+4, w->fg) */
    /* draw_cursor(fb, w->x + 4 + cursor*8, w->y+4) */
}

void gui_render_checkbox(gui_state_t* gui, widget_t* w) {
    /* draw_rect(fb, {w->x, w->y, 16, 16}, w->border) */
    /* if (w->checked) fill_rect(fb, {w->x+2, w->y+2, 12, 12}, COLOR_CHECKBOX) */
    /* draw_text(fb, w->text, w->x+24, w->y+2, w->fg) */
}

void gui_render_progress(gui_state_t* gui, widget_t* w) {
    /* fill_rect(fb, w->rect, w->bg) */
    /* fill_rect(fb, {w->x, w->y, w->width * value/max, w->height}, w->fg) */
}

void gui_render_slider(gui_state_t* gui, widget_t* w) {
    /* fill_rect(fb, w->rect, w->bg) */
    /* Draw handle at current position */
}

void gui_render_menu(gui_state_t* gui, widget_t* w) {
    /* fill_rect(fb, w->rect, w->bg) */
    /* Draw items horizontally */
}

void gui_render_list(gui_state_t* gui, widget_t* w) {
    /* fill_rect(fb, w->rect, w->bg) */
    /* Draw items, highlight selected */
}

void gui_render_tabs(gui_state_t* gui, widget_t* w) {
    /* Draw tab bar */
    /* Highlight active tab */
    /* Draw content area */
}

void gui_render_widget(gui_state_t* gui, widget_t* w) {
    if (!w || !w->visible) return;

    switch (w->type) {
        case WIDGET_BUTTON:    gui_render_button(gui, w); break;
        case WIDGET_LABEL:     gui_render_label(gui, w); break;
        case WIDGET_TEXTBOX:   gui_render_textbox(gui, w); break;
        case WIDGET_CHECKBOX:  gui_render_checkbox(gui, w); break;
        case WIDGET_PROGRESS:  gui_render_progress(gui, w); break;
        case WIDGET_SLIDER:    gui_render_slider(gui, w); break;
        case WIDGET_MENU:      gui_render_menu(gui, w); break;
        case WIDGET_LIST:      gui_render_list(gui, w); break;
        case WIDGET_TABS:      gui_render_tabs(gui, w); break;
        default: break;
    }
}

void gui_render(gui_state_t* gui) {
    if (!gui) return;
    for (uint32_t i = 0; i < gui->num_widgets; i++) {
        if (gui->widgets[i].visible)
            gui_render_widget(gui, &gui->widgets[i]);
    }
}

/* ---- Find ---- */

widget_t* gui_find_widget(gui_state_t* gui, uint32_t id) {
    if (!gui) return NULL;
    for (uint32_t i = 0; i < gui->num_widgets; i++)
        if (gui->widgets[i].id == id)
            return &gui->widgets[i];
    return NULL;
}

widget_t* gui_hit_test(gui_state_t* gui, uint32_t x, uint32_t y) {
    if (!gui) return NULL;
    for (int i = gui->num_widgets - 1; i >= 0; i--) {
        widget_t* w = &gui->widgets[i];
        if (w->visible && w->enabled &&
            x >= (uint32_t)w->x && x < w->x + w->width &&
            y >= (uint32_t)w->y && y < w->y + w->height)
            return w;
    }
    return NULL;
}

/* ---- Layout ---- */

void gui_layout_row(gui_state_t* gui, uint32_t panel_id, int spacing) {
    widget_t* panel = gui_find_widget(gui, panel_id);
    if (!panel || panel->type != WIDGET_PANEL) return;

    int y_offset = 4;
    for (uint32_t i = 0; i < panel->num_children; i++) {
        widget_t* child = gui_find_widget(gui, panel->children[i]);
        if (child && child->visible) {
            child->x = panel->x + 4;
            child->y = panel->y + y_offset;
            child->width = panel->width - 8;
            y_offset += child->height + spacing;
        }
    }
}

void gui_layout_column(gui_state_t* gui, uint32_t panel_id, int spacing) {
    widget_t* panel = gui_find_widget(gui, panel_id);
    if (!panel || panel->type != WIDGET_PANEL) return;

    int x_offset = 4;
    for (uint32_t i = 0; i < panel->num_children; i++) {
        widget_t* child = gui_find_widget(gui, panel->children[i]);
        if (child && child->visible) {
            child->x = panel->x + x_offset;
            child->y = panel->y + 4;
            x_offset += child->width + spacing;
        }
    }
}
