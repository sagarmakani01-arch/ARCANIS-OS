#ifndef ARCANIS_KEYBOARD_H
#define ARCANIS_KEYBOARD_H

#include "drivers/driver.h"
#include "utils/driver_ringbuffer.h"

#define KB_DATA_PORT        0x60
#define KB_STATUS_PORT      0x64
#define KB_COMMAND_PORT     0x64
#define KB_IRQ              1

#define KB_BUFFER_SIZE      256
#define KB_MAX_KEY_STATES   128

typedef enum {
    KEY_NONE = 0,
    KEY_ESC = 0x01,
    KEY_BACKSPACE = 0x0E,
    KEY_TAB = 0x0F,
    KEY_ENTER = 0x1C,
    KEY_LEFT_CTRL = 0x1D,
    KEY_LEFT_SHIFT = 0x2A,
    KEY_RIGHT_SHIFT = 0x36,
    KEY_LEFT_ALT = 0x38,
    KEY_CAPS_LOCK = 0x3A,
    KEY_F1 = 0x3B,
    KEY_F2 = 0x3C,
    KEY_F3 = 0x3D,
    KEY_F4 = 0x3E,
    KEY_F5 = 0x3F,
    KEY_F6 = 0x40,
    KEY_F7 = 0x41,
    KEY_F8 = 0x42,
    KEY_F9 = 0x43,
    KEY_F10 = 0x44,
    KEY_F11 = 0x57,
    KEY_F12 = 0x58,
    KEY_NUM_LOCK = 0x45,
    KEY_SCROLL_LOCK = 0x46,
    KEY_HOME = 0x47,
    KEY_UP = 0x48,
    KEY_PAGE_UP = 0x49,
    KEY_MINUS = 0x4A,
    KEY_LEFT = 0x4B,
    KEY_KP5 = 0x4C,
    KEY_RIGHT = 0x4D,
    KEY_PLUS = 0x4E,
    KEY_END = 0x4F,
    KEY_DOWN = 0x50,
    KEY_PAGE_DOWN = 0x51,
    KEY_INSERT = 0x52,
    KEY_DELETE = 0x53,
    KEY_LGUI = 0x5B,
    KEY_RGUI = 0x5C
} KeyCode;

typedef enum {
    KB_EVENT_KEY_PRESSED = 0,
    KB_EVENT_KEY_RELEASED,
    KB_EVENT_SCANCODE,
    KB_EVENT_LED_UPDATE
} KeyboardEventType;

typedef struct {
    KeyboardEventType type;
    KeyCode key;
    uint8_t scancode;
    bool shift;
    bool ctrl;
    bool alt;
    bool gui;
} KeyboardEvent;

typedef void (*KeyboardCallback)(KeyboardEvent* event, void* user_data);

typedef struct {
    Driver driver;
    Device device;
    RingBuffer buffer;
    uint8_t buffer_data[KB_BUFFER_SIZE];
    bool key_states[KB_MAX_KEY_STATES];
    bool shift_pressed;
    bool ctrl_pressed;
    bool alt_pressed;
    bool gui_pressed;
    bool caps_lock;
    bool num_lock;
    bool scroll_lock;
    uint8_t leds;
    KeyboardCallback callback;
    void* callback_data;
    HALContext* hal;
    bool initialized;
} KeyboardDriver;

DriverStatus keyboard_init_driver(KeyboardDriver* kbd, HALContext* hal);
DriverStatus keyboard_shutdown_driver(KeyboardDriver* kbd);
DriverStatus keyboard_set_callback(KeyboardDriver* kbd, KeyboardCallback callback, void* user_data);
bool keyboard_is_key_pressed(KeyboardDriver* kbd, KeyCode key);
bool keyboard_get_modifiers(KeyboardDriver* kbd, bool* shift, bool* ctrl, bool* alt, bool* gui);
DriverStatus keyboard_update_leds(KeyboardDriver* kbd);
char keyboard_scancode_to_ascii(KeyboardDriver* kbd, uint8_t scancode);
const char* key_code_to_string(KeyCode key);

#endif