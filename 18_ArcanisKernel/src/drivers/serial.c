#include <arcanis/serial.h>
#include <arcanis/io.h>
#include <arcanis/types.h>

#define SERIAL_COM1 0x3F8

void serial_initialize(uint16_t port) {
    outb(port + 1, 0x00);
    outb(port + 3, 0x80);
    outb(port + 0, 0x03);
    outb(port + 1, 0x00);
    outb(port + 3, 0x03);
    outb(port + 2, 0xC7);
    outb(port + 4, 0x0B);
}

static int serial_transmit_empty(uint16_t port) {
    return inb(port + 5) & 0x20;
}

void serial_putchar(char c) {
    while (!serial_transmit_empty(SERIAL_COM1));
    outb(SERIAL_COM1, (uint8_t)c);
}

void serial_puts(const char* str) {
    while (*str) {
        if (*str == '\n') serial_putchar('\r');
        serial_putchar(*str++);
    }
}

char serial_getchar(void) {
    while (!(inb(SERIAL_COM1 + 5) & 1));
    return inb(SERIAL_COM1);
}

bool serial_has_data(void) {
    return inb(SERIAL_COM1 + 5) & 1;
}
