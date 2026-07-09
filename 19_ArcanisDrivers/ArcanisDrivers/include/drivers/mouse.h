#ifndef ARCANIS_MOUSE_H
#define ARCANIS_MOUSE_H

#include "drivers/driver.h"
#include "utils/driver_ringbuffer.h"

#define MOUSE_DATA_PORT     0x60
#define MOUSE_STATUS_PORT   0x64
#define MOUSE_COMMAND_PORT  0x64
#define MOUSE_IRQ           12

#define MOUSE_BUFFER_SIZE   256

#define MOUSE_CMD_RESET         0xFF
#define MOUSE_CMD_RESEND        0xFE
#define MOUSE_CMD_SET_DEFAULTS  0xF6
#define MOUSE_CMD_DISABLE       0xF5
#define MOUSE_CMD_ENABLE        0xF4
#define MOUSE_CMD_SET_SAMPLE    0xF3
#define MOUSE_CMD_GET_ID        0xF2
#define MOUSE_CMD_SET_REMOTE    0xF0
#define MOUSE_CMD_SET_WRAP      0x80
#define MOUSE_CMD_READ_DATA     0xEB
#define MOUSE_CMD_SET_STREAM    0xEA

#define MOUSE_EN_ACK        0xFA
#define MOUSE_EN_RESEND     0xFE
#define MOUSE_EN_ERROR      0xFC

typedef enum {
    MOUSE_BUTTON_LEFT = 0,
    MOUSE_BUTTON_RIGHT,
    MOUSE_BUTTON_MIDDLE,
    MOUSE_BUTTON_X1,
    MOUSE_BUTTON_X2,
    MOUSE_BUTTON_COUNT
} MouseButton;

typedef enum {
    MOUSE_EVENT_MOVE = 0,
    MOUSE_EVENT_BUTTON_PRESSED,
    MOUSE_EVENT_BUTTON_RELEASED,
    MOUSE_EVENT_WHEEL
} MouseEventType;

typedef struct {
    MouseEventType type;
    int32_t x;
    int32_t y;
    int32_t dx;
    int32_t dy;
    int32_t wheel;
    MouseButton button;
    bool buttons[MOUSE_BUTTON_COUNT];
} MouseEvent;

typedef void (*MouseCallback)(MouseEvent* event, void* user_data);

typedef struct {
    Driver driver;
    Device device;
    RingBuffer buffer;
    uint8_t buffer_data[MOUSE_BUFFER_SIZE];
    int32_t x;
    int32_t y;
    int32_t min_x;
    int32_t min_y;
    int32_t max_x;
    int32_t max_y;
    bool buttons[MOUSE_BUTTON_COUNT];
    int32_t wheel;
    uint8_t packet[4];
    uint8_t packet_index;
    bool has_wheel;
    bool has_extra_buttons;
    uint32_t sample_rate;
    MouseCallback callback;
    void* callback_data;
    HALContext* hal;
    bool initialized;
} MouseDriver;

DriverStatus mouse_init_driver(MouseDriver* mouse, HALContext* hal);
DriverStatus mouse_shutdown_driver(MouseDriver* mouse);
DriverStatus mouse_set_callback(MouseDriver* mouse, MouseCallback callback, void* user_data);
DriverStatus mouse_set_position(MouseDriver* mouse, int32_t x, int32_t y);
DriverStatus mouse_get_position(MouseDriver* mouse, int32_t* x, int32_t* y);
DriverStatus mouse_set_sample_rate(MouseDriver* mouse, uint32_t rate);
DriverStatus mouse_enable_data_reporting(MouseDriver* mouse);
DriverStatus mouse_disable_data_reporting(MouseDriver* mouse);
DriverStatus mouse_reset(MouseDriver* mouse);
bool mouse_is_button_pressed(MouseDriver* mouse, MouseButton button);
DriverStatus mouse_set_bounds(MouseDriver* mouse, int32_t min_x, int32_t min_y, int32_t max_x, int32_t max_y);

#endif