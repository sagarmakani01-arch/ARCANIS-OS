#include "drivers/driver_event.h"
#include <string.h>

void event_dispatcher_init(EventDispatcher* dispatcher) {
    if (!dispatcher) return;
    memset(dispatcher, 0, sizeof(EventDispatcher));
}

DriverStatus event_subscribe(EventDispatcher* dispatcher, EventCallback callback, void* user_data, uint32_t* listener_id) {
    if (!dispatcher || !callback) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (dispatcher->listener_count >= EVENT_MAX_LISTENERS) {
        return DRIVER_STATUS_NO_MEMORY;
    }

    for (uint32_t i = 0; i < EVENT_MAX_LISTENERS; i++) {
        if (!dispatcher->listeners[i].active) {
            dispatcher->listeners[i].callback = callback;
            dispatcher->listeners[i].user_data = user_data;
            dispatcher->listeners[i].active = true;
            dispatcher->listener_count++;

            if (listener_id) {
                *listener_id = i;
            }

            return DRIVER_STATUS_OK;
        }
    }

    return DRIVER_STATUS_NO_MEMORY;
}

DriverStatus event_unsubscribe(EventDispatcher* dispatcher, uint32_t listener_id) {
    if (!dispatcher || listener_id >= EVENT_MAX_LISTENERS) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (!dispatcher->listeners[listener_id].active) {
        return DRIVER_STATUS_ERROR;
    }

    dispatcher->listeners[listener_id].active = false;
    dispatcher->listeners[listener_id].callback = NULL;
    dispatcher->listeners[listener_id].user_data = NULL;
    dispatcher->listener_count--;

    return DRIVER_STATUS_OK;
}

DriverStatus event_emit(EventDispatcher* dispatcher, DriverEvent* event) {
    if (!dispatcher || !event) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    for (uint32_t i = 0; i < EVENT_MAX_LISTENERS; i++) {
        if (dispatcher->listeners[i].active && dispatcher->listeners[i].callback) {
            dispatcher->listeners[i].callback(event, dispatcher->listeners[i].user_data);
        }
    }

    return DRIVER_STATUS_OK;
}

void event_queue_init(EventQueue* queue) {
    if (!queue) return;
    memset(queue, 0, sizeof(EventQueue));
}

DriverStatus event_queue_push(EventQueue* queue, DriverEvent* event) {
    if (!queue || !event) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (queue->count >= EVENT_QUEUE_SIZE) {
        return DRIVER_STATUS_NO_MEMORY;
    }

    queue->events[queue->tail] = *event;
    queue->tail = (queue->tail + 1) % EVENT_QUEUE_SIZE;
    queue->count++;

    return DRIVER_STATUS_OK;
}

DriverStatus event_queue_pop(EventQueue* queue, DriverEvent* event) {
    if (!queue || !event) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (queue->count == 0) {
        return DRIVER_STATUS_NOT_READY;
    }

    *event = queue->events[queue->head];
    queue->head = (queue->head + 1) % EVENT_QUEUE_SIZE;
    queue->count--;

    return DRIVER_STATUS_OK;
}

bool event_queue_empty(EventQueue* queue) {
    return queue ? queue->count == 0 : true;
}
