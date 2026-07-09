#ifndef ARCANIS_DISPLAY_H
#define ARCANIS_DISPLAY_H

#include "drivers/driver.h"
#include <stdint.h>
#include <stdbool.h>

#define DISPLAY_DEFAULT_WIDTH    800
#define DISPLAY_DEFAULT_HEIGHT   600
#define DISPLAY_DEFAULT_BPP      32

#define VGA_MISC_ADDR    0x3C2
#define VGA_SEQ_ADDR     0x3C4
#define VGA_CRTC_ADDR    0x3D4
#define VGA_GC_ADDR      0x3CE
#define VGA_AC_ADDR      0x3C0
#define VGA_STATUS_ADDR  0x3DA

#define VGA_AC_INDEX     0x3C0
#define VGA_AC_WRITE     0x3C0
#define VGA_GC_INDEX     0x3CE
#define VGA_GC_WRITE     0x3CE
#define VGA_SEQ_INDEX    0x3C4
#define VGA_SEQ_WRITE    0x3C4
#define VGA_CRTC_INDEX   0x3D4
#define VGA_CRTC_WRITE   0x3D4
#define VGA_INSTAT_READ  0x3DA

typedef enum {
    DISPLAY_MODE_TEXT_80x25 = 0,
    DISPLAY_MODE_TEXT_80x50,
    DISPLAY_MODE_GFX_320x200,
    DISPLAY_MODE_GFX_640x480,
    DISPLAY_MODE_GFX_800x600,
    DISPLAY_MODE_GFX_1024x768,
    DISPLAY_MODE_GFX_1280x720,
    DISPLAY_MODE_GFX_1920x1080,
    DISPLAY_MODE_CUSTOM
} DisplayMode;

typedef struct {
    uint8_t blue;
    uint8_t green;
    uint8_t red;
    uint8_t alpha;
} Color;

typedef struct {
    int32_t x;
    int32_t y;
} Point;

typedef struct {
    int32_t x;
    int32_t y;
    int32_t width;
    int32_t height;
} Rect;

typedef enum {
    DISPLAY_EVENT_MODE_CHANGED = 0,
    DISPLAY_EVENT_BUFFER_FLUSH,
    DISPLAY_EVENT_CURSOR_MOVE
} DisplayEventType;

typedef struct {
    DisplayEventType type;
    DisplayMode mode;
    uint32_t width;
    uint32_t height;
} DisplayEvent;

typedef void (*DisplayCallback)(DisplayEvent* event, void* user_data);

typedef struct {
    Driver driver;
    Device device;
    DisplayMode mode;
    uint32_t width;
    uint32_t height;
    uint32_t bpp;
    uint32_t pitch;
    uint8_t* framebuffer;
    uint8_t* backbuffer;
    uint32_t framebuffer_size;
    Point cursor;
    Color cursor_color;
    bool cursor_visible;
    Rect dirty_region;
    bool dirty;
    DisplayCallback callback;
    void* callback_data;
    HALContext* hal;
    bool initialized;
} DisplayDriver;

typedef struct {
    uint8_t width;
    uint8_t height;
    uint8_t* data;
} FontGlyph;

DriverStatus display_init_driver(DisplayDriver* display, HALContext* hal);
DriverStatus display_shutdown_driver(DisplayDriver* display);

DriverStatus display_set_mode(DisplayDriver* display, DisplayMode mode);
DriverStatus display_set_resolution(DisplayDriver* display, uint32_t width, uint32_t height, uint32_t bpp);
DriverStatus display_get_mode(DisplayDriver* display, DisplayMode* mode);
DriverStatus display_get_resolution(DisplayDriver* display, uint32_t* width, uint32_t* height, uint32_t* bpp);

DriverStatus display_clear(DisplayDriver* display, Color color);
DriverStatus display_set_pixel(DisplayDriver* display, int32_t x, int32_t y, Color color);
DriverStatus display_get_pixel(DisplayDriver* display, int32_t x, int32_t y, Color* color);
DriverStatus display_fill_rect(DisplayDriver* display, Rect rect, Color color);
DriverStatus display_draw_rect(DisplayDriver* display, Rect rect, Color color);
DriverStatus display_draw_line(DisplayDriver* display, int32_t x1, int32_t y1, int32_t x2, int32_t y2, Color color);
DriverStatus display_blit(DisplayDriver* display, int32_t x, int32_t y, const uint8_t* data, uint32_t width, uint32_t height);
DriverStatus display_flush(DisplayDriver* display);

DriverStatus display_set_cursor(DisplayDriver* display, int32_t x, int32_t y);
DriverStatus display_show_cursor(DisplayDriver* display, bool show);
DriverStatus display_set_cursor_color(DisplayDriver* display, Color color);

DriverStatus display_set_callback(DisplayDriver* display, DisplayCallback callback, void* user_data);

Color display_make_color(uint8_t r, uint8_t g, uint8_t b, uint8_t a);
Color display_make_color_rgb(uint8_t r, uint8_t g, uint8_t b);

#endif