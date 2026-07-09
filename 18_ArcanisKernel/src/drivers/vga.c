#include <arcanis/vga.h>
#include <arcanis/io.h>
#include <arcanis/types.h>
#include <arcanis/string.h>

static uint16_t* vga_buffer = (uint16_t*)0xB8000;
static int vga_x = 0;
static int vga_y = 0;
static uint8_t vga_color_attr = 0x0F;

static inline uint8_t vga_entry_color(uint8_t fg, uint8_t bg) {
    return fg | (bg << 4);
}

static inline uint16_t vga_entry(char c, uint8_t color) {
    return (uint16_t)c | ((uint16_t)color << 8);
}

void vga_initialize(void) {
    vga_buffer = (uint16_t*)0xB8000;
    vga_color_attr = vga_entry_color(VGA_LIGHT_GREY, VGA_BLACK);
    vga_enable_cursor(14, 15);
    vga_clear();
}

void vga_clear(void) {
    for (int i = 0; i < VGA_WIDTH * VGA_HEIGHT; i++) {
        vga_buffer[i] = vga_entry(' ', vga_color_attr);
    }
    vga_x = 0;
    vga_y = 0;
    vga_set_cursor(0, 0);
}

void vga_set_color(uint8_t fg, uint8_t bg) {
    vga_color_attr = vga_entry_color(fg, bg);
}

void vga_scroll(void) {
    if (vga_y >= VGA_HEIGHT) {
        for (int i = 0; i < (VGA_HEIGHT - 1) * VGA_WIDTH; i++) {
            vga_buffer[i] = vga_buffer[i + VGA_WIDTH];
        }
        for (int i = (VGA_HEIGHT - 1) * VGA_WIDTH; i < VGA_HEIGHT * VGA_WIDTH; i++) {
            vga_buffer[i] = vga_entry(' ', vga_color_attr);
        }
        vga_y = VGA_HEIGHT - 1;
    }
}

void vga_put_char(char c) {
    if (c == '\n') {
        vga_x = 0;
        vga_y++;
    } else if (c == '\r') {
        vga_x = 0;
    } else if (c == '\t') {
        vga_x = (vga_x + 8) & ~7;
    } else if (c == '\b') {
        if (vga_x > 0) {
            vga_x--;
            vga_buffer[vga_y * VGA_WIDTH + vga_x] = vga_entry(' ', vga_color_attr);
        }
    } else {
        vga_buffer[vga_y * VGA_WIDTH + vga_x] = vga_entry(c, vga_color_attr);
        vga_x++;
    }

    if (vga_x >= VGA_WIDTH) {
        vga_x = 0;
        vga_y++;
    }

    vga_scroll();
    vga_set_cursor(vga_x, vga_y);
}

void vga_puts(const char* str) {
    while (*str) {
        vga_put_char(*str++);
    }
}

void vga_put_hex(uint32_t value) {
    char buf[11] = "0x00000000";
    char hex[] = "0123456789abcdef";
    for (int i = 9; i >= 2; i--) {
        buf[i] = hex[value & 0xF];
        value >>= 4;
    }
    vga_puts(buf);
}

void vga_put_dec(uint32_t value) {
    char buf[12];
    itoa((int)value, buf, 10);
    vga_puts(buf);
}

void vga_enable_cursor(uint8_t cursor_start, uint8_t cursor_end) {
    outb(0x3D4, 0x0A);
    outb(0x3D5, (inb(0x3D5) & 0xC0) | cursor_start);
    outb(0x3D4, 0x0B);
    outb(0x3D5, (inb(0x3D5) & 0xE0) | cursor_end);
}

void vga_set_cursor(int x, int y) {
    uint16_t pos = y * VGA_WIDTH + x;
    outb(0x3D4, 0x0F);
    outb(0x3D5, (uint8_t)(pos & 0xFF));
    outb(0x3D4, 0x0E);
    outb(0x3D5, (uint8_t)((pos >> 8) & 0xFF));
}
