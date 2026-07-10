/**
 * gui.h — GUI Toolkit (Widgets)
 *
 * Button, TextBox, Label, CheckBox, ComboBox, ProgressBar, Panel, Menu widgets.
 * Event-driven widget system with layout management.
 */
#ifndef ARCANIS_GUI_H
#define ARCANIS_GUI_H

#include <arcanis/types.h>
#include <arcanis/window.h>

#define GUI_MAX_WIDGETS    256
#define GUI_MAX_TEXT       256
#define GUI_MAX_CHILDREN   32
#define GUI_MAX_MENU_ITEMS 16
#define GUI_MAX_LIST_ITEMS 64

typedef enum {
    WIDGET_BUTTON,
    WIDGET_LABEL,
    WIDGET_TEXTBOX,
    WIDGET_CHECKBOX,
    WIDGET_RADIO,
    WIDGET_COMBOBOX,
    WIDGET_PROGRESS,
    WIDGET_SLIDER,
    WIDGET_PANEL,
    WIDGET_MENU,
    WIDGET_LIST,
    WIDGET_SCROLLBAR,
    WIDGET_IMAGE,
    WIDGET_TABS,
    WIDGET_TOOLBAR
} widget_type_t;

typedef enum {
    EVENT_CLICK,
    EVENT_HOVER,
    EVENT_FOCUS,
    EVENT_UNFOCUS,
    EVENT_KEY,
    EVENT_CHANGE,
    EVENT_SCROLL
} event_type_t;

typedef struct {
    event_type_t type;
    uint32_t     widget_id;
    int          key;
    int          mouse_x;
    int          mouse_y;
    void*        data;
} event_t;

typedef void (*event_handler_t)(event_t* event);

typedef struct {
    uint32_t    id;
    widget_type_t type;
    char        text[GUI_MAX_TEXT];
    int         x, y;
    uint32_t    width, height;
    int         visible;
    int         enabled;
    int         focused;
    int         hovered;

    /* Colors */
    uint32_t    bg_color;
    uint32_t    fg_color;
    uint32_t    border_color;
    uint32_t    hover_color;
    uint32_t    focus_color;

    /* Font */
    uint32_t    font_size;
    int         text_align; /* 0=left, 1=center, 2=right */

    /* Parent/child */
    uint32_t    parent_id;
    uint32_t    children[GUI_MAX_CHILDREN];
    uint32_t    num_children;

    /* Type-specific */
    union {
        struct { /* Button */
            int pressed;
            uint32_t press_color;
        } button;
        struct { /* TextBox */
            uint32_t cursor_pos;
            uint32_t selection_start;
            uint32_t selection_end;
            int      password_mode;
            int      multiline;
            uint32_t max_length;
        } textbox;
        struct { /* CheckBox */
            int checked;
        } checkbox;
        struct { /* ComboBox */
            char     items[GUI_MAX_CHILDREN][GUI_MAX_TEXT];
            uint32_t num_items;
            uint32_t selected;
            int      dropped_down;
        } combobox;
        struct { /* Progress */
            uint32_t value;
            uint32_t max_value;
        } progress;
        struct { /* Slider */
            int32_t  min_val;
            int32_t  max_val;
            int32_t  current;
            int      vertical;
        } slider;
        struct { /* Menu */
            char     items[GUI_MAX_MENU_ITEMS][GUI_MAX_TEXT];
            uint32_t num_items;
            uint32_t selected;
        } menu;
        struct { /* List */
            char     items[GUI_MAX_LIST_ITEMS][GUI_MAX_TEXT];
            uint32_t num_items;
            uint32_t selected;
            uint32_t scroll_offset;
        } list;
        struct { /* Tabs */
            char     labels[16][GUI_MAX_TEXT];
            uint32_t num_tabs;
            uint32_t active_tab;
        } tabs;
    };

    event_handler_t on_click;
    event_handler_t on_change;
    event_handler_t on_key;
} widget_t;

typedef struct {
    widget_t  widgets[GUI_MAX_WIDGETS];
    uint32_t  num_widgets;
    uint32_t  next_id;
    uint32_t  focused_widget;
    uint32_t  hovered_widget;
    wm_state_t* wm;
} gui_state_t;

/* Initialize GUI */
void     gui_init(gui_state_t* gui, wm_state_t* wm);

/* Widget creation */
uint32_t gui_create_button(gui_state_t* gui, const char* text, int x, int y, uint32_t w, uint32_t h);
uint32_t gui_create_label(gui_state_t* gui, const char* text, int x, int y);
uint32_t gui_create_textbox(gui_state_t* gui, const char* text, int x, int y, uint32_t w, uint32_t h);
uint32_t gui_create_checkbox(gui_state_t* gui, const char* text, int x, int y);
uint32_t gui_create_combobox(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h);
uint32_t gui_create_progress(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h);
uint32_t gui_create_slider(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h, int vertical);
uint32_t gui_create_panel(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h);
uint32_t gui_create_menu(gui_state_t* gui, int x, int y, uint32_t w);
uint32_t gui_create_list(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h);
uint32_t gui_create_tabs(gui_state_t* gui, int x, int y, uint32_t w, uint32_t h);

/* Widget properties */
void     gui_set_text(gui_state_t* gui, uint32_t id, const char* text);
void     gui_set_position(gui_state_t* gui, uint32_t id, int x, int y);
void     gui_set_size(gui_state_t* gui, uint32_t id, uint32_t w, uint32_t h);
void     gui_set_colors(gui_state_t* gui, uint32_t id,
                         uint32_t bg, uint32_t fg, uint32_t border);
void     gui_set_visible(gui_state_t* gui, uint32_t id, int visible);
void     gui_set_enabled(gui_state_t* gui, uint32_t id, int enabled);

/* Widget actions */
void     gui_button_press(gui_state_t* gui, uint32_t id);
void     gui_textbox_insert(gui_state_t* gui, uint32_t id, char c);
void     gui_textbox_delete(gui_state_t* gui, uint32_t id);
void     gui_checkbox_toggle(gui_state_t* gui, uint32_t id);
void     gui_progress_set(gui_state_t* gui, uint32_t id, uint32_t value);
void     gui_slider_set(gui_state_t* gui, uint32_t id, int32_t value);
void     gui_combobox_add(gui_state_t* gui, uint32_t id, const char* item);
void     gui_list_add(gui_state_t* gui, uint32_t id, const char* item);
void     gui_tabs_add(gui_state_t* gui, uint32_t id, const char* label);
void     gui_menu_add(gui_state_t* gui, uint32_t id, const char* item);

/* Event handling */
void     gui_handle_click(gui_state_t* gui, uint32_t x, uint32_t y);
void     gui_handle_key(gui_state_t* gui, int key);
void     gui_handle_hover(gui_state_t* gui, uint32_t x, uint32_t y);

/* Rendering */
void     gui_render(gui_state_t* gui);
void     gui_render_widget(gui_state_t* gui, widget_t* w);
void     gui_render_button(gui_state_t* gui, widget_t* w);
void     gui_render_label(gui_state_t* gui, widget_t* w);
void     gui_render_textbox(gui_state_t* gui, widget_t* w);
void     gui_render_checkbox(gui_state_t* gui, widget_t* w);
void     gui_render_progress(gui_state_t* gui, widget_t* w);
void     gui_render_slider(gui_state_t* gui, widget_t* w);
void     gui_render_menu(gui_state_t* gui, widget_t* w);
void     gui_render_list(gui_state_t* gui, widget_t* w);
void     gui_render_tabs(gui_state_t* gui, widget_t* w);

/* Find widget */
widget_t* gui_find_widget(gui_state_t* gui, uint32_t id);
widget_t* gui_hit_test(gui_state_t* gui, uint32_t x, uint32_t y);

/* Layout helpers */
void     gui_layout_row(gui_state_t* gui, uint32_t panel_id, int spacing);
void     gui_layout_column(gui_state_t* gui, uint32_t panel_id, int spacing);

#endif
