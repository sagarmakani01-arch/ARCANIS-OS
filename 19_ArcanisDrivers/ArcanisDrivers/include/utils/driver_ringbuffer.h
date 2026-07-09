#ifndef ARCANIS_DRIVER_RINGBUFFER_H
#define ARCANIS_DRIVER_RINGBUFFER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#include "drivers/driver.h"

#define RING_BUFFER_DEFAULT_SIZE 4096

typedef struct {
    uint8_t* buffer;
    size_t capacity;
    size_t head;
    size_t tail;
    size_t count;
    bool initialized;
} RingBuffer;

DriverStatus ringbuffer_init(RingBuffer* rb, uint8_t* buffer, size_t capacity);
DriverStatus ringbuffer_destroy(RingBuffer* rb);
DriverStatus ringbuffer_push(RingBuffer* rb, uint8_t byte);
DriverStatus ringbuffer_pop(RingBuffer* rb, uint8_t* byte);
DriverStatus ringbuffer_write(RingBuffer* rb, const uint8_t* data, size_t len, size_t* written);
DriverStatus ringbuffer_read(RingBuffer* rb, uint8_t* data, size_t len, size_t* read);
DriverStatus ringbuffer_peek(RingBuffer* rb, uint8_t* byte);
DriverStatus ringbuffer_flush(RingBuffer* rb);
size_t ringbuffer_count(RingBuffer* rb);
size_t ringbuffer_free(RingBuffer* rb);
bool ringbuffer_empty(RingBuffer* rb);
bool ringbuffer_full(RingBuffer* rb);

#endif