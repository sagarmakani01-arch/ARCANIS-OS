#include "drivers/display.h"
#include <string.h>

static const uint8_t vga_320x200[] = {
    0x63, 0x03, 0x01, 0x0F, 0x00, 0x0E
};

static const uint8_t vga_640x480[] = {
    0x03, 0x01, 0x0F, 0x00, 0x0E
};

static void vga_write_reg(uint16_t addr, uint8_t index, uint8_t value) {
    #ifdef _WIN32
    __outb(index, addr);
    __outb(value, addr + 1);
    #endif
}

static void vga_set_mode_text(DisplayDriver* display) {
    display->width = 80;
    display->height = 25;
    display->bpp = 4;
    display->pitch = 80 * 2;
    display->framebuffer_size = 80 * 25 * 2;

    #ifdef _WIN32
    uint8_t misc = __inb(VGA_MISC_ADDR);
    misc |= 0x02;
    __outb(misc, VGA_MISC_ADDR);

    for (int i = 0; i < 5; i++) {
        vga_write_reg(VGA_SEQ_ADDR, i, vga_640x480[i]);
    }

    vga_write_reg(VGA_SEQ_ADDR, 0x02, 0x0F);

    uint8_t crtc_data[] = {0x5F, 0x4F, 0x50, 0x82, 0x55, 0x81, 0xBF, 0x1F, 0x00, 0x4F, 0x0D, 0x0E, 0x00, 0x00, 0x00, 0x00, 0x9C, 0x0E, 0x8F, 0x28, 0x40, 0x96, 0xB9, 0xA3, 0xFF};
    for (int i = 0; i < 25; i++) {
        vga_write_reg(VGA_CRTC_ADDR, i, crtc_data[i]);
    }

    uint8_t gc_data[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x05, 0x0F, 0xFF};
    for (int i = 0; i < 9; i++) {
        vga_write_reg(VGA_GC_ADDR, i, gc_data[i]);
    }

    uint8_t ac_data[] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x41, 0x00, 0x0F, 0x00, 0x00};
    for (int i = 0; i < 21; i++) {
        vga_write_reg(VGA_AC_ADDR, i, ac_data[i]);
    }
    #endif
}

static void vga_set_mode_graphics(DisplayDriver* display, uint32_t width, uint32_t height) {
    display->width = width;
    display->height = height;
    display->bpp = 8;
    display->pitch = width;
    display->framebuffer_size = width * height;

    #ifdef _WIN32
    uint8_t misc = __inb(VGA_MISC_ADDR);
    misc |= 0x02;
    __outb(misc, VGA_MISC_ADDR);

    if (width == 320 && height == 200) {
        for (int i = 0; i < 6; i++) {
            vga_write_reg(VGA_SEQ_ADDR, i, vga_320x200[i]);
        }
    } else {
        for (int i = 0; i < 5; i++) {
            vga_write_reg(VGA_SEQ_ADDR, i, vga_640x480[i]);
        }
    }

    vga_write_reg(VGA_SEQ_ADDR, 0x02, 0x0F);

    uint8_t crtc_data[] = {0x5F, 0x4F, 0x50, 0x82, 0x55, 0x81, 0xBF, 0x1F, 0x00, 0x4F, 0x0D, 0x0E, 0x00, 0x00, 0x00, 0x00, 0x9C, 0x0E, 0x8F, 0x28, 0x40, 0x96, 0xB9, 0xA3, 0xFF};
    for (int i = 0; i < 25; i++) {
        vga_write_reg(VGA_CRTC_ADDR, i, crtc_data[i]);
    }

    uint8_t gc_data[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x05, 0x0F, 0xFF};
    for (int i = 0; i < 9; i++) {
        vga_write_reg(VGA_GC_ADDR, i, gc_data[i]);
    }

    uint8_t ac_data[] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x41, 0x00, 0x0F, 0x00, 0x00};
    for (int i = 0; i < 21; i++) {
        vga_write_reg(VGA_AC_ADDR, i, ac_data[i]);
    }
    #endif
}

DriverStatus display_init_driver(DisplayDriver* display, HALContext* hal) {
    if (!display || !hal) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memset(display, 0, sizeof(DisplayDriver));

    driver_create(&display->driver, "vga_display", DRIVER_TYPE_DISPLAY, NULL);
    device_create(&display->device, "display0", &display->driver);

    display->hal = hal;
    display->mode = DISPLAY_MODE_TEXT_80x25;
    display->cursor.x = 0;
    display->cursor.y = 0;
    display->cursor_visible = true;
    display->cursor_color = display_make_color(255, 255, 255, 255);
    display->dirty = false;

    vga_set_mode_text(display);

    display->framebuffer = (uint8_t*)0xB8000;
    display->backbuffer = NULL;

    if (display->framebuffer_size > 0) {
        display->backbuffer = (uint8_t*)hal_memory_map(hal, 0xB8000, display->framebuffer_size, (void**)&display->framebuffer);
    }

    device_set_state(&display->device, DEVICE_STATE_RUNNING);
    display->initialized = true;

    return DRIVER_STATUS_OK;
}

DriverStatus display_shutdown_driver(DisplayDriver* display) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (display->backbuffer && display->hal) {
        hal_memory_unmap(display->hal, display->backbuffer, display->framebuffer_size);
    }

    device_set_state(&display->device, DEVICE_STATE_SUSPENDED);
    display->initialized = false;

    return DRIVER_STATUS_OK;
}

DriverStatus display_set_mode(DisplayDriver* display, DisplayMode mode) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    switch (mode) {
        case DISPLAY_MODE_TEXT_80x25:
            vga_set_mode_text(display);
            break;
        case DISPLAY_MODE_TEXT_80x50:
            display->width = 80;
            display->height = 50;
            display->bpp = 4;
            display->pitch = 80 * 2;
            display->framebuffer_size = 80 * 50 * 2;
            break;
        case DISPLAY_MODE_GFX_320x200:
            vga_set_mode_graphics(display, 320, 200);
            break;
        case DISPLAY_MODE_GFX_640x480:
            vga_set_mode_graphics(display, 640, 480);
            break;
        case DISPLAY_MODE_GFX_800x600:
            vga_set_mode_graphics(display, 800, 600);
            break;
        default:
            return DRIVER_STATUS_NOT_SUPPORTED;
    }

    display->mode = mode;

    if (display->callback) {
        DisplayEvent event = {
            .type = DISPLAY_EVENT_MODE_CHANGED,
            .mode = mode,
            .width = display->width,
            .height = display->height
        };
        display->callback(&event, display->callback_data);
    }

    return DRIVER_STATUS_OK;
}

DriverStatus display_set_resolution(DisplayDriver* display, uint32_t width, uint32_t height, uint32_t bpp) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (width == 0 || height == 0 || bpp == 0) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (width == 80 && height == 25) {
        return display_set_mode(display, DISPLAY_MODE_TEXT_80x25);
    } else if (width == 320 && height == 200) {
        return display_set_mode(display, DISPLAY_MODE_GFX_320x200);
    } else if (width == 640 && height == 480) {
        return display_set_mode(display, DISPLAY_MODE_GFX_640x480);
    } else if (width == 800 && height == 600) {
        return display_set_mode(display, DISPLAY_MODE_GFX_800x600);
    }

    display->width = width;
    display->height = height;
    display->bpp = bpp;
    display->pitch = width * (bpp / 8);
    display->framebuffer_size = display->pitch * height;
    display->mode = DISPLAY_MODE_CUSTOM;

    return DRIVER_STATUS_OK;
}

DriverStatus display_get_mode(DisplayDriver* display, DisplayMode* mode) {
    if (!display || !mode || !display->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    *mode = display->mode;
    return DRIVER_STATUS_OK;
}

DriverStatus display_get_resolution(DisplayDriver* display, uint32_t* width, uint32_t* height, uint32_t* bpp) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (width) *width = display->width;
    if (height) *height = display->height;
    if (bpp) *bpp = display->bpp;

    return DRIVER_STATUS_OK;
}

DriverStatus display_clear(DisplayDriver* display, Color color) {
    if (!display || !display->initialized || !display->framebuffer) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (display->mode == DISPLAY_MODE_TEXT_80x25 || display->mode == DISPLAY_MODE_TEXT_80x50) {
        uint16_t attr = (color.blue << 12) | (color.green << 8) | (color.red << 4) | color.alpha;
        uint16_t* vga = (uint16_t*)display->framebuffer;
        for (uint32_t i = 0; i < display->width * display->height; i++) {
            vga[i] = (attr << 8) | ' ';
        }
    } else {
        uint8_t pixel = (color.red >> 5) << 5 | (color.green >> 5) << 2 | (color.blue >> 6);
        memset(display->framebuffer, pixel, display->framebuffer_size);
    }

    display->dirty = true;
    return DRIVER_STATUS_OK;
}

DriverStatus display_set_pixel(DisplayDriver* display, int32_t x, int32_t y, Color color) {
    if (!display || !display->initialized || !display->framebuffer) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (x < 0 || x >= (int32_t)display->width || y < 0 || y >= (int32_t)display->height) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (display->mode == DISPLAY_MODE_TEXT_80x25 || display->mode == DISPLAY_MODE_TEXT_80x50) {
        return DRIVER_STATUS_NOT_SUPPORTED;
    }

    uint32_t offset = y * display->pitch + x;
    if (display->bpp == 8) {
        uint8_t pixel = (color.red >> 5) << 5 | (color.green >> 5) << 2 | (color.blue >> 6);
        display->framebuffer[offset] = pixel;
    } else if (display->bpp == 32) {
        offset *= 4;
        display->framebuffer[offset] = color.blue;
        display->framebuffer[offset + 1] = color.green;
        display->framebuffer[offset + 2] = color.red;
        display->framebuffer[offset + 3] = color.alpha;
    }

    display->dirty = true;
    return DRIVER_STATUS_OK;
}

DriverStatus display_get_pixel(DisplayDriver* display, int32_t x, int32_t y, Color* color) {
    if (!display || !color || !display->initialized || !display->framebuffer) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (x < 0 || x >= (int32_t)display->width || y < 0 || y >= (int32_t)display->height) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (display->mode == DISPLAY_MODE_TEXT_80x25 || display->mode == DISPLAY_MODE_TEXT_80x50) {
        return DRIVER_STATUS_NOT_SUPPORTED;
    }

    uint32_t offset = y * display->pitch + x;
    if (display->bpp == 8) {
        uint8_t pixel = display->framebuffer[offset];
        color->red = ((pixel >> 5) & 0x07) * 36;
        color->green = ((pixel >> 2) & 0x07) * 36;
        color->blue = (pixel & 0x03) * 85;
        color->alpha = 255;
    } else if (display->bpp == 32) {
        offset *= 4;
        color->blue = display->framebuffer[offset];
        color->green = display->framebuffer[offset + 1];
        color->red = display->framebuffer[offset + 2];
        color->alpha = display->framebuffer[offset + 3];
    }

    return DRIVER_STATUS_OK;
}

DriverStatus display_fill_rect(DisplayDriver* display, Rect rect, Color color) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (display->mode == DISPLAY_MODE_TEXT_80x25 || display->mode == DISPLAY_MODE_TEXT_80x50) {
        return DRIVER_STATUS_NOT_SUPPORTED;
    }

    for (int32_t y = rect.y; y < rect.y + rect.height; y++) {
        for (int32_t x = rect.x; x < rect.x + rect.width; x++) {
            display_set_pixel(display, x, y, color);
        }
    }

    return DRIVER_STATUS_OK;
}

DriverStatus display_draw_rect(DisplayDriver* display, Rect rect, Color color) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    display_draw_line(display, rect.x, rect.y, rect.x + rect.width - 1, rect.y, color);
    display_draw_line(display, rect.x + rect.width - 1, rect.y, rect.x + rect.width - 1, rect.y + rect.height - 1, color);
    display_draw_line(display, rect.x + rect.width - 1, rect.y + rect.height - 1, rect.x, rect.y + rect.height - 1, color);
    display_draw_line(display, rect.x, rect.y + rect.height - 1, rect.x, rect.y, color);

    return DRIVER_STATUS_OK;
}

DriverStatus display_draw_line(DisplayDriver* display, int32_t x1, int32_t y1, int32_t x2, int32_t y2, Color color) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    int32_t dx = abs(x2 - x1);
    int32_t dy = abs(y2 - y1);
    int32_t sx = x1 < x2 ? 1 : -1;
    int32_t sy = y1 < y2 ? 1 : -1;
    int32_t err = dx - dy;

    while (true) {
        display_set_pixel(display, x1, y1, color);

        if (x1 == x2 && y1 == y2) break;

        int32_t e2 = 2 * err;
        if (e2 > -dy) {
            err -= dy;
            x1 += sx;
        }
        if (e2 < dx) {
            err += dx;
            y1 += sy;
        }
    }

    return DRIVER_STATUS_OK;
}

DriverStatus display_blit(DisplayDriver* display, int32_t x, int32_t y, const uint8_t* data, uint32_t width, uint32_t height) {
    if (!display || !data || !display->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    for (uint32_t row = 0; row < height; row++) {
        for (uint32_t col = 0; col < width; col++) {
            int32_t px = x + col;
            int32_t py = y + row;

            if (px >= 0 && px < (int32_t)display->width && py >= 0 && py < (int32_t)display->height) {
                Color color;
                color.red = data[(row * width + col) * 3];
                color.green = data[(row * width + col) * 3 + 1];
                color.blue = data[(row * width + col) * 3 + 2];
                color.alpha = 255;
                display_set_pixel(display, px, py, color);
            }
        }
    }

    return DRIVER_STATUS_OK;
}

DriverStatus display_flush(DisplayDriver* display) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (display->dirty && display->callback) {
        DisplayEvent event = {
            .type = DISPLAY_EVENT_BUFFER_FLUSH,
            .mode = display->mode,
            .width = display->width,
            .height = display->height
        };
        display->callback(&event, display->callback_data);
    }

    display->dirty = false;
    return DRIVER_STATUS_OK;
}

DriverStatus display_set_cursor(DisplayDriver* display, int32_t x, int32_t y) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    display->cursor.x = x;
    display->cursor.y = y;

    if (display->mode == DISPLAY_MODE_TEXT_80x25 || display->mode == DISPLAY_MODE_TEXT_80x50) {
        uint16_t pos = y * display->width + x;
        #ifdef _WIN32
        __outb(0x0F, VGA_CRTC_ADDR);
        __outb((uint8_t)(pos & 0xFF), VGA_CRTC_ADDR + 1);
        __outb(0x0E, VGA_CRTC_ADDR);
        __outb((uint8_t)((pos >> 8) & 0xFF), VGA_CRTC_ADDR + 1);
        #endif
    }

    if (display->callback) {
        DisplayEvent event = {
            .type = DISPLAY_EVENT_CURSOR_MOVE,
            .mode = display->mode,
            .width = (uint32_t)x,
            .height = (uint32_t)y
        };
        display->callback(&event, display->callback_data);
    }

    return DRIVER_STATUS_OK;
}

DriverStatus display_show_cursor(DisplayDriver* display, bool show) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    display->cursor_visible = show;

    if (display->mode == DISPLAY_MODE_TEXT_80x25 || display->mode == DISPLAY_MODE_TEXT_80x50) {
        #ifdef _WIN32
        __outb(0x0A, VGA_CRTC_ADDR);
        uint8_t cursor_start = show ? 0x0D : 0x20;
        __outb(cursor_start, VGA_CRTC_ADDR + 1);
        #endif
    }

    return DRIVER_STATUS_OK;
}

DriverStatus display_set_cursor_color(DisplayDriver* display, Color color) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    display->cursor_color = color;
    return DRIVER_STATUS_OK;
}

DriverStatus display_set_callback(DisplayDriver* display, DisplayCallback callback, void* user_data) {
    if (!display || !display->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    display->callback = callback;
    display->callback_data = user_data;

    return DRIVER_STATUS_OK;
}

Color display_make_color(uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    Color color;
    color.red = r;
    color.green = g;
    color.blue = b;
    color.alpha = a;
    return color;
}

Color display_make_color_rgb(uint8_t r, uint8_t g, uint8_t b) {
    return display_make_color(r, g, b, 255);
}
