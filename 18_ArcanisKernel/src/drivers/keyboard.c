#include <arcanis/keyboard.h>
#include <arcanis/io.h>
#include <arcanis/types.h>

static keyboard_callback_t keyboard_callback = NULL;
static uint8_t keyboard_buffer[256];
static volatile uint8_t buffer_head = 0;
static volatile uint8_t buffer_tail = 0;
static bool shift_pressed = false;
static bool ctrl_pressed = false;

static const char scancode_ascii[] = {
    0, 0, '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 0, 0,
    'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\n', 0,
    'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '`', 0, '\\',
    'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 0, '*', 0, ' '
};

static const char scancode_shift_ascii[] = {
    0, 0, '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', 0, 0,
    'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', '\n', 0,
    'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"', '~', 0, '|',
    'Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?', 0, '*', 0, ' '
};

static inline bool keyboard_buffer_empty(void) {
    return buffer_head == buffer_tail;
}

static inline bool keyboard_buffer_full(void) {
    return ((buffer_head + 1) % 256) == buffer_tail;
}

static void keyboard_buffer_push(uint8_t scancode) {
    if (!keyboard_buffer_full()) {
        keyboard_buffer[buffer_head] = scancode;
        buffer_head = (buffer_head + 1) % 256;
    }
}

void keyboard_interrupt_handler(registers_t* regs) {
    (void)regs;
    uint8_t scancode = inb(0x60);

    if (scancode & 0x80) {
        uint8_t released = scancode & 0x7F;
        if (released == 0x2A || released == 0x36) shift_pressed = false;
        if (released == 0x1D) ctrl_pressed = false;
        return;
    }

    if (scancode == 0x2A || scancode == 0x36) { shift_pressed = true; return; }
    if (scancode == 0x1D) { ctrl_pressed = true; return; }

    keyboard_buffer_push(scancode);

    if (keyboard_callback) {
        keyboard_callback(scancode);
    }
}

void keyboard_initialize(void) {
    buffer_head = 0;
    buffer_tail = 0;
    shift_pressed = false;
    ctrl_pressed = false;

    extern void irq_register_handler(int irq, void (*handler)(registers_t*));
    irq_register_handler(1, keyboard_interrupt_handler);
}

void keyboard_register_callback(keyboard_callback_t cb) {
    keyboard_callback = cb;
}

char scancode_to_ascii(uint8_t scancode) {
    if (scancode >= sizeof(scancode_ascii)) return 0;
    if (shift_pressed) return scancode_shift_ascii[scancode];
    return scancode_ascii[scancode];
}

uint8_t keyboard_get_scancode(void) {
    if (keyboard_buffer_empty()) return 0;
    uint8_t sc = keyboard_buffer[buffer_tail];
    buffer_tail = (buffer_tail + 1) % 256;
    return sc;
}

bool keyboard_has_data(void) {
    return !keyboard_buffer_empty();
}
