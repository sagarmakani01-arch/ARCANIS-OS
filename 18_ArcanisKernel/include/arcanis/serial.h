#ifndef ARCANIS_SERIAL_H
#define ARCANIS_SERIAL_H

#include <arcanis/types.h>

void serial_initialize(uint16_t port);
void serial_putchar(char c);
void serial_puts(const char* str);
char serial_getchar(void);
bool serial_has_data(void);

#endif
