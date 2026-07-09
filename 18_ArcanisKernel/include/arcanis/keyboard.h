#ifndef ARCANIS_KEYBOARD_H
#define ARCANIS_KEYBOARD_H

#include <arcanis/types.h>

typedef void (*keyboard_callback_t)(uint8_t scancode);

void keyboard_initialize(void);
void keyboard_register_callback(keyboard_callback_t cb);
char scancode_to_ascii(uint8_t scancode);
uint8_t keyboard_get_scancode(void);
bool keyboard_has_data(void);

#endif
