#include "drivers/mouse.h"
#include <string.h>

static void mouse_wait_input(void) {
    #ifdef _WIN32
    uint32_t timeout = 100000;
    while (((__inb(MOUSE_STATUS_PORT) & 0x01) == 0) && timeout > 0) {
        timeout--;
    }
    #endif
}

static void mouse_wait_output(void) {
    #ifdef _WIN32
    uint32_t timeout = 100000;
    while (((__inb(MOUSE_STATUS_PORT) & 0x02) != 0) && timeout > 0) {
        timeout--;
    }
    #endif
}

static void mouse_write(uint8_t data) {
    mouse_wait_output();
    #ifdef _WIN32
    __outb(0xD4, MOUSE_COMMAND_PORT);
    mouse_wait_output();
    __outb(data, MOUSE_DATA_PORT);
    #endif
}

static uint8_t mouse_read(void) {
    mouse_wait_input();
    #ifdef _WIN32
    return __inb(MOUSE_DATA_PORT);
    #else
    return 0;
    #endif
}

static void mouse_irq_handler(void* data) {
    MouseDriver* mouse = (MouseDriver*)data;
    if (!mouse || !mouse->initialized) return;

    uint8_t data_byte = mouse_read();

    if (data_byte == MOUSE_EN_ACK || data_byte == MOUSE_EN_RESEND || data_byte == MOUSE_EN_ERROR) {
        return;
    }

    mouse->packet[mouse->packet_index] = data_byte;
    mouse->packet_index++;

    if (mouse->packet_index >= 3) {
        if (mouse->has_wheel && mouse->packet_index < 4) {
            return;
        }

        MouseEvent event;
        memset(&event, 0, sizeof(MouseEvent));

        event.buttons[MOUSE_BUTTON_LEFT] = (mouse->packet[0] & 0x01) != 0;
        event.buttons[MOUSE_BUTTON_RIGHT] = (mouse->packet[0] & 0x02) != 0;
        event.buttons[MOUSE_BUTTON_MIDDLE] = (mouse->packet[0] & 0x04) != 0;

        if (mouse->has_extra_buttons) {
            event.buttons[MOUSE_BUTTON_X1] = (mouse->packet[3] & 0x10) != 0;
            event.buttons[MOUSE_BUTTON_X2] = (mouse->packet[3] & 0x20) != 0;
        }

        for (int i = 0; i < MOUSE_BUTTON_COUNT; i++) {
            if (event.buttons[i] && !mouse->buttons[i]) {
                event.type = MOUSE_EVENT_BUTTON_PRESSED;
                event.button = (MouseButton)i;
                if (mouse->callback) {
                    mouse->callback(&event, mouse->callback_data);
                }
            } else if (!event.buttons[i] && mouse->buttons[i]) {
                event.type = MOUSE_EVENT_BUTTON_RELEASED;
                event.button = (MouseButton)i;
                if (mouse->callback) {
                    mouse->callback(&event, mouse->callback_data);
                }
            }
            mouse->buttons[i] = event.buttons[i];
        }

        int32_t dx = (int8_t)mouse->packet[1];
        int32_t dy = (int8_t)mouse->packet[2];

        if (mouse->packet[0] & 0x10) {
            dx |= 0xFFFFFF00;
        }
        if (mouse->packet[0] & 0x20) {
            dy |= 0xFFFFFF00;
        }

        dy = -dy;

        mouse->x += dx;
        mouse->y += dy;

        if (mouse->x < mouse->min_x) mouse->x = mouse->min_x;
        if (mouse->x > mouse->max_x) mouse->x = mouse->max_x;
        if (mouse->y < mouse->min_y) mouse->y = mouse->min_y;
        if (mouse->y > mouse->max_y) mouse->y = mouse->max_y;

        event.type = MOUSE_EVENT_MOVE;
        event.x = mouse->x;
        event.y = mouse->y;
        event.dx = dx;
        event.dy = dy;

        if (mouse->has_wheel && mouse->packet_index >= 4) {
            int8_t wheel_data = (int8_t)(mouse->packet[3] & 0x0F);
            if (wheel_data & 0x08) {
                wheel_data |= 0xF0;
            }
            mouse->wheel += wheel_data;
            event.wheel = wheel_data;
            event.type = MOUSE_EVENT_WHEEL;
        }

        if (mouse->callback) {
            mouse->callback(&event, mouse->callback_data);
        }

        mouse->packet_index = 0;
    }
}

DriverStatus mouse_init_driver(MouseDriver* mouse, HALContext* hal) {
    if (!mouse || !hal) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memset(mouse, 0, sizeof(MouseDriver));

    driver_create(&mouse->driver, "ps2_mouse", DRIVER_TYPE_INPUT, NULL);
    device_create(&mouse->device, "mouse0", &mouse->driver);

    ringbuffer_init(&mouse->buffer, mouse->buffer_data, MOUSE_BUFFER_SIZE);

    mouse->hal = hal;
    mouse->x = 0;
    mouse->y = 0;
    mouse->min_x = 0;
    mouse->min_y = 0;
    mouse->max_x = 1024;
    mouse->max_y = 768;
    mouse->sample_rate = 100;
    mouse->has_wheel = false;
    mouse->has_extra_buttons = false;
    mouse->packet_index = 0;

    mouse_write(MOUSE_CMD_DISABLE);
    mouse_write(MOUSE_CMD_SET_DEFAULTS);
    mouse_read();

    mouse_write(MOUSE_CMD_GET_ID);
    uint8_t id = mouse_read();
    if (id == 0x03) {
        mouse->has_wheel = true;
    }

    if (mouse->has_wheel) {
        mouse_write(MOUSE_CMD_SET_SAMPLE);
        mouse_write(200);
        mouse_read();

        mouse_write(MOUSE_CMD_SET_SAMPLE);
        mouse_write(100);
        mouse_read();

        mouse_write(MOUSE_CMD_GET_ID);
        id = mouse_read();
        if (id == 0x04) {
            mouse->has_extra_buttons = true;
        }
    }

    mouse_write(MOUSE_CMD_SET_SAMPLE);
    mouse_write(mouse->sample_rate);
    mouse_read();

    if (hal->irq.register_handler) {
        hal->irq.register_handler(MOUSE_IRQ, mouse_irq_handler, mouse);
    }

    if (hal->irq.enable_irq) {
        hal->irq.enable_irq(MOUSE_IRQ);
    }

    mouse_write(MOUSE_CMD_ENABLE);
    mouse_read();

    device_set_state(&mouse->device, DEVICE_STATE_RUNNING);
    mouse->initialized = true;

    return DRIVER_STATUS_OK;
}

DriverStatus mouse_shutdown_driver(MouseDriver* mouse) {
    if (!mouse || !mouse->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    mouse_write(MOUSE_CMD_DISABLE);

    if (mouse->hal->irq.disable_irq) {
        mouse->hal->irq.disable_irq(MOUSE_IRQ);
    }

    if (mouse->hal->irq.unregister_handler) {
        mouse->hal->irq.unregister_handler(MOUSE_IRQ);
    }

    device_set_state(&mouse->device, DEVICE_STATE_SUSPENDED);
    mouse->initialized = false;

    return DRIVER_STATUS_OK;
}

DriverStatus mouse_set_callback(MouseDriver* mouse, MouseCallback callback, void* user_data) {
    if (!mouse || !mouse->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    mouse->callback = callback;
    mouse->callback_data = user_data;

    return DRIVER_STATUS_OK;
}

DriverStatus mouse_set_position(MouseDriver* mouse, int32_t x, int32_t y) {
    if (!mouse || !mouse->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    mouse->x = x;
    mouse->y = y;

    return DRIVER_STATUS_OK;
}

DriverStatus mouse_get_position(MouseDriver* mouse, int32_t* x, int32_t* y) {
    if (!mouse || !x || !y || !mouse->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    *x = mouse->x;
    *y = mouse->y;

    return DRIVER_STATUS_OK;
}

DriverStatus mouse_set_sample_rate(MouseDriver* mouse, uint32_t rate) {
    if (!mouse || !mouse->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (rate < 10 || rate > 200) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    mouse_write(MOUSE_CMD_SET_SAMPLE);
    mouse_write(rate);
    mouse_read();

    mouse->sample_rate = rate;

    return DRIVER_STATUS_OK;
}

DriverStatus mouse_enable_data_reporting(MouseDriver* mouse) {
    if (!mouse || !mouse->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    mouse_write(MOUSE_CMD_ENABLE);
    mouse_read();

    return DRIVER_STATUS_OK;
}

DriverStatus mouse_disable_data_reporting(MouseDriver* mouse) {
    if (!mouse || !mouse->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    mouse_write(MOUSE_CMD_DISABLE);
    mouse_read();

    return DRIVER_STATUS_OK;
}

DriverStatus mouse_reset(MouseDriver* mouse) {
    if (!mouse || !mouse->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    mouse_write(MOUSE_CMD_RESET);
    mouse_read();

    mouse->x = 0;
    mouse->y = 0;
    mouse->wheel = 0;
    mouse->packet_index = 0;

    for (int i = 0; i < MOUSE_BUTTON_COUNT; i++) {
        mouse->buttons[i] = false;
    }

    return DRIVER_STATUS_OK;
}

bool mouse_is_button_pressed(MouseDriver* mouse, MouseButton button) {
    if (!mouse || !mouse->initialized || button >= MOUSE_BUTTON_COUNT) {
        return false;
    }

    return mouse->buttons[button];
}

DriverStatus mouse_set_bounds(MouseDriver* mouse, int32_t min_x, int32_t min_y, int32_t max_x, int32_t max_y) {
    if (!mouse || !mouse->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (min_x >= max_x || min_y >= max_y) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    mouse->min_x = min_x;
    mouse->min_y = min_y;
    mouse->max_x = max_x;
    mouse->max_y = max_y;

    if (mouse->x < min_x) mouse->x = min_x;
    if (mouse->x > max_x) mouse->x = max_x;
    if (mouse->y < min_y) mouse->y = min_y;
    if (mouse->y > max_y) mouse->y = max_y;

    return DRIVER_STATUS_OK;
}
