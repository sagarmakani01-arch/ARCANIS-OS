#ifndef ARCANIS_VGA_H
#define ARCANIS_VGA_H

#include <arcanis/types.h>

enum vga_color {
    VGA_BLACK        = 0,
    VGA_BLUE         = 1,
    VGA_GREEN        = 2,
    VGA_CYAN         = 3,
    VGA_RED          = 4,
    VGA_MAGENTA      = 5,
    VGA_BROWN        = 6,
    VGA_LIGHT_GREY   = 7,
    VGA_DARK_GREY    = 8,
    VGA_LIGHT_BLUE   = 9,
    VGA_LIGHT_GREEN  = 10,
    VGA_LIGHT_CYAN   = 11,
    VGA_LIGHT_RED    = 12,
    VGA_LIGHT_MAGENTA= 13,
    VGA_YELLOW       = 14,
    VGA_WHITE        = 15,
};

#define VGA_WIDTH  80
#define VGA_HEIGHT 25

void vga_initialize(void);
void vga_clear(void);
void vga_set_color(uint8_t fg, uint8_t bg);
void vga_put_char(char c);
void vga_puts(const char* str);
void vga_printf(const char* format, ...);
void vga_put_hex(uint32_t value);
void vga_put_dec(uint32_t value);
void vga_scroll(void);
void vga_enable_cursor(uint8_t cursor_start, uint8_t cursor_end);
void vga_set_cursor(int x, int y);

#endif
