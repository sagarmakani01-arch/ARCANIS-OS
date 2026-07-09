#include "drivers/keyboard.h"
#include <string.h>

static const char scancode_ascii[] = {
    0, 0, '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 0, 0,
    'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', 0, 0,
    'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '`', 0, '\\',
    'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 0, '*', 0, ' '
};

static const char scancode_shift_ascii[] = {
    0, 0, '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', 0, 0,
    'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', 0, 0,
    'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"', '~', 0, '|',
    'Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?', 0, '*', 0, ' '
};

static void keyboard_irq_handler(void* data) {
    KeyboardDriver* kbd = (KeyboardDriver*)data;
    if (!kbd || !kbd->initialized) return;

    uint8_t scancode = 0;
    #ifdef _WIN32
    __inb(KB_DATA_PORT);
    #endif

    ringbuffer_push(&kbd->buffer, scancode);

    bool key_released = (scancode & 0x80) != 0;
    uint8_t key_code = scancode & 0x7F;

    if (key_code < KB_MAX_KEY_STATES) {
        kbd->key_states[key_code] = !key_released;
    }

    switch (key_code) {
        case KEY_LEFT_SHIFT:
        case KEY_RIGHT_SHIFT:
            kbd->shift_pressed = !key_released;
            break;
        case KEY_LEFT_CTRL:
            kbd->ctrl_pressed = !key_released;
            break;
        case KEY_LEFT_ALT:
            kbd->alt_pressed = !key_released;
            break;
        case KEY_LGUI:
        case KEY_RGUI:
            kbd->gui_pressed = !key_released;
            break;
        case KEY_CAPS_LOCK:
            if (!key_released) {
                kbd->caps_lock = !kbd->caps_lock;
                keyboard_update_leds(kbd);
            }
            break;
        case KEY_NUM_LOCK:
            if (!key_released) {
                kbd->num_lock = !kbd->num_lock;
                keyboard_update_leds(kbd);
            }
            break;
        case KEY_SCROLL_LOCK:
            if (!key_released) {
                kbd->scroll_lock = !kbd->scroll_lock;
                keyboard_update_leds(kbd);
            }
            break;
    }

    if (kbd->callback) {
        KeyboardEvent event;
        event.scancode = scancode;
        event.key = (KeyCode)key_code;
        event.shift = kbd->shift_pressed;
        event.ctrl = kbd->ctrl_pressed;
        event.alt = kbd->alt_pressed;
        event.gui = kbd->gui_pressed;

        if (key_released) {
            event.type = KB_EVENT_KEY_RELEASED;
        } else {
            event.type = KB_EVENT_KEY_PRESSED;
        }

        kbd->callback(&event, kbd->callback_data);
    }
}

DriverStatus keyboard_init_driver(KeyboardDriver* kbd, HALContext* hal) {
    if (!kbd || !hal) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memset(kbd, 0, sizeof(KeyboardDriver));

    driver_create(&kbd->driver, "ps2_keyboard", DRIVER_TYPE_INPUT, NULL);
    device_create(&kbd->device, "keyboard0", &kbd->driver);

    ringbuffer_init(&kbd->buffer, kbd->buffer_data, KB_BUFFER_SIZE);

    kbd->hal = hal;
    kbd->caps_lock = false;
    kbd->num_lock = true;
    kbd->scroll_lock = false;
    kbd->leds = 0x02;

    keyboard_update_leds(kbd);

    if (hal->irq.register_handler) {
        hal->irq.register_handler(KB_IRQ, keyboard_irq_handler, kbd);
    }

    if (hal->irq.enable_irq) {
        hal->irq.enable_irq(KB_IRQ);
    }

    device_set_state(&kbd->device, DEVICE_STATE_RUNNING);
    kbd->initialized = true;

    return DRIVER_STATUS_OK;
}

DriverStatus keyboard_shutdown_driver(KeyboardDriver* kbd) {
    if (!kbd || !kbd->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (kbd->hal->irq.disable_irq) {
        kbd->hal->irq.disable_irq(KB_IRQ);
    }

    if (kbd->hal->irq.unregister_handler) {
        kbd->hal->irq.unregister_handler(KB_IRQ);
    }

    device_set_state(&kbd->device, DEVICE_STATE_SUSPENDED);
    ringbuffer_flush(&kbd->buffer);
    kbd->initialized = false;

    return DRIVER_STATUS_OK;
}

DriverStatus keyboard_set_callback(KeyboardDriver* kbd, KeyboardCallback callback, void* user_data) {
    if (!kbd || !kbd->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    kbd->callback = callback;
    kbd->callback_data = user_data;

    return DRIVER_STATUS_OK;
}

bool keyboard_is_key_pressed(KeyboardDriver* kbd, KeyCode key) {
    if (!kbd || !kbd->initialized || key >= KB_MAX_KEY_STATES) {
        return false;
    }

    return kbd->key_states[key];
}

bool keyboard_get_modifiers(KeyboardDriver* kbd, bool* shift, bool* ctrl, bool* alt, bool* gui) {
    if (!kbd || !kbd->initialized) {
        return false;
    }

    if (shift) *shift = kbd->shift_pressed;
    if (ctrl) *ctrl = kbd->ctrl_pressed;
    if (alt) *alt = kbd->alt_pressed;
    if (gui) *gui = kbd->gui_pressed;

    return true;
}

DriverStatus keyboard_update_leds(KeyboardDriver* kbd) {
    if (!kbd || !kbd->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    kbd->leds = 0;
    if (kbd->scroll_lock) kbd->leds |= 0x01;
    if (kbd->num_lock) kbd->leds |= 0x02;
    if (kbd->caps_lock) kbd->leds |= 0x04;

    #ifdef _WIN32
    while (__inb(KB_STATUS_PORT) & 0x02);
    __outb(0xED, KB_COMMAND_PORT);
    while (__inb(KB_STATUS_PORT) & 0x02);
    __outb(kbd->leds, KB_DATA_PORT);
    #endif

    return DRIVER_STATUS_OK;
}

char keyboard_scancode_to_ascii(KeyboardDriver* kbd, uint8_t scancode) {
    if (!kbd || scancode >= sizeof(scancode_ascii)) {
        return 0;
    }

    bool shift = kbd->shift_pressed ^ kbd->caps_lock;

    if (shift) {
        return scancode_shift_ascii[scancode];
    }

    return scancode_ascii[scancode];
}

const char* key_code_to_string(KeyCode key) {
    switch (key) {
        case KEY_NONE:          return "None";
        case KEY_ESC:           return "Escape";
        case KEY_BACKSPACE:     return "Backspace";
        case KEY_TAB:           return "Tab";
        case KEY_ENTER:         return "Enter";
        case KEY_LEFT_CTRL:     return "Left Ctrl";
        case KEY_LEFT_SHIFT:    return "Left Shift";
        case KEY_RIGHT_SHIFT:   return "Right Shift";
        case KEY_LEFT_ALT:      return "Left Alt";
        case KEY_CAPS_LOCK:     return "Caps Lock";
        case KEY_F1:            return "F1";
        case KEY_F2:            return "F2";
        case KEY_F3:            return "F3";
        case KEY_F4:            return "F4";
        case KEY_F5:            return "F5";
        case KEY_F6:            return "F6";
        case KEY_F7:            return "F7";
        case KEY_F8:            return "F8";
        case KEY_F9:            return "F9";
        case KEY_F10:           return "F10";
        case KEY_F11:           return "F11";
        case KEY_F12:           return "F12";
        case KEY_NUM_LOCK:      return "Num Lock";
        case KEY_SCROLL_LOCK:   return "Scroll Lock";
        case KEY_HOME:          return "Home";
        case KEY_UP:            return "Up";
        case KEY_PAGE_UP:       return "Page Up";
        case KEY_LEFT:          return "Left";
        case KEY_RIGHT:         return "Right";
        case KEY_END:           return "End";
        case KEY_DOWN:          return "Down";
        case KEY_PAGE_DOWN:     return "Page Down";
        case KEY_INSERT:        return "Insert";
        case KEY_DELETE:        return "Delete";
        case KEY_LGUI:          return "Left GUI";
        case KEY_RGUI:          return "Right GUI";
        default:                return "Unknown";
    }
}
