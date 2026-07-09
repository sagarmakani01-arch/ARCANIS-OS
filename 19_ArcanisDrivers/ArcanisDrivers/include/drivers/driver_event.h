#ifndef ARCANIS_DRIVER_EVENT_H
#define ARCANIS_DRIVER_EVENT_H

#include "drivers/driver.h"

#define EVENT_MAX_LISTENERS 32
#define EVENT_QUEUE_SIZE    256

typedef enum {
    EVENT_DEVICE_CONNECTED = 0,
    EVENT_DEVICE_DISCONNECTED,
    EVENT_DEVICE_READY,
    EVENT_DEVICE_ERROR,
    EVENT_DATA_RECEIVED,
    EVENT_DATA_SENT,
    EVENT_IRQ_FIRED,
    EVENT_DMA_COMPLETE,
    EVENT_TIMER_TICK,
    EVENT_USER_DEFINED = 1000
} EventType;

typedef struct {
    EventType type;
    Device* source;
    uint32_t data[4];
    uint64_t timestamp;
} DriverEvent;

typedef void (*EventCallback)(DriverEvent* event, void* user_data);

typedef struct {
    EventCallback callback;
    void* user_data;
    bool active;
} EventListener;

typedef struct {
    EventListener listeners[EVENT_MAX_LISTENERS];
    uint32_t listener_count;
} EventDispatcher;

typedef struct {
    DriverEvent events[EVENT_QUEUE_SIZE];
    uint32_t head;
    uint32_t tail;
    uint32_t count;
} EventQueue;

void event_dispatcher_init(EventDispatcher* dispatcher);
DriverStatus event_subscribe(EventDispatcher* dispatcher, EventCallback callback, void* user_data, uint32_t* listener_id);
DriverStatus event_unsubscribe(EventDispatcher* dispatcher, uint32_t listener_id);
DriverStatus event_emit(EventDispatcher* dispatcher, DriverEvent* event);

void event_queue_init(EventQueue* queue);
DriverStatus event_queue_push(EventQueue* queue, DriverEvent* event);
DriverStatus event_queue_pop(EventQueue* queue, DriverEvent* event);
bool event_queue_empty(EventQueue* queue);

#endif