#include "utils/driver_ringbuffer.h"
#include <string.h>

DriverStatus ringbuffer_init(RingBuffer* rb, uint8_t* buffer, size_t capacity) {
    if (!rb || !buffer || capacity == 0) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    rb->buffer = buffer;
    rb->capacity = capacity;
    rb->head = 0;
    rb->tail = 0;
    rb->count = 0;
    rb->initialized = true;

    return DRIVER_STATUS_OK;
}

DriverStatus ringbuffer_destroy(RingBuffer* rb) {
    if (!rb) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    rb->initialized = false;
    rb->buffer = NULL;
    rb->capacity = 0;
    rb->head = 0;
    rb->tail = 0;
    rb->count = 0;

    return DRIVER_STATUS_OK;
}

DriverStatus ringbuffer_push(RingBuffer* rb, uint8_t byte) {
    if (!rb || !rb->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (rb->count >= rb->capacity) {
        return DRIVER_STATUS_NO_MEMORY;
    }

    rb->buffer[rb->tail] = byte;
    rb->tail = (rb->tail + 1) % rb->capacity;
    rb->count++;

    return DRIVER_STATUS_OK;
}

DriverStatus ringbuffer_pop(RingBuffer* rb, uint8_t* byte) {
    if (!rb || !byte || !rb->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (rb->count == 0) {
        return DRIVER_STATUS_NOT_READY;
    }

    *byte = rb->buffer[rb->head];
    rb->head = (rb->head + 1) % rb->capacity;
    rb->count--;

    return DRIVER_STATUS_OK;
}

DriverStatus ringbuffer_write(RingBuffer* rb, const uint8_t* data, size_t len, size_t* written) {
    if (!rb || !data || !rb->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    size_t written_count = 0;
    for (size_t i = 0; i < len; i++) {
        DriverStatus status = ringbuffer_push(rb, data[i]);
        if (status != DRIVER_STATUS_OK) {
            break;
        }
        written_count++;
    }

    if (written) {
        *written = written_count;
    }

    return written_count > 0 ? DRIVER_STATUS_OK : DRIVER_STATUS_NO_MEMORY;
}

DriverStatus ringbuffer_read(RingBuffer* rb, uint8_t* data, size_t len, size_t* read) {
    if (!rb || !data || !rb->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    size_t read_count = 0;
    for (size_t i = 0; i < len; i++) {
        DriverStatus status = ringbuffer_pop(rb, &data[i]);
        if (status != DRIVER_STATUS_OK) {
            break;
        }
        read_count++;
    }

    if (read) {
        *read = read_count;
    }

    return read_count > 0 ? DRIVER_STATUS_OK : DRIVER_STATUS_NOT_READY;
}

DriverStatus ringbuffer_peek(RingBuffer* rb, uint8_t* byte) {
    if (!rb || !byte || !rb->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (rb->count == 0) {
        return DRIVER_STATUS_NOT_READY;
    }

    *byte = rb->buffer[rb->head];
    return DRIVER_STATUS_OK;
}

DriverStatus ringbuffer_flush(RingBuffer* rb) {
    if (!rb || !rb->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    rb->head = 0;
    rb->tail = 0;
    rb->count = 0;

    return DRIVER_STATUS_OK;
}

size_t ringbuffer_count(RingBuffer* rb) {
    return rb ? rb->count : 0;
}

size_t ringbuffer_free(RingBuffer* rb) {
    return rb ? rb->capacity - rb->count : 0;
}

bool ringbuffer_empty(RingBuffer* rb) {
    return rb ? rb->count == 0 : true;
}

bool ringbuffer_full(RingBuffer* rb) {
    return rb ? rb->count >= rb->capacity : true;
}
