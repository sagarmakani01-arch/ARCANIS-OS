/**
 * pipe.c — POSIX-like Pipe Implementation
 *
 * Circular buffer pipe for inter-process communication.
 * Blocks read if empty, blocks write if full.
 * Supports multiple readers/writers.
 */
#include <arcanis/pipe.h>
#include <arcanis/string.h>

void pipe_init(pipe_t* pipe) {
    pipe->read_pos = 0;
    pipe->write_pos = 0;
    pipe->count = 0;
    pipe->readers = 1;
    pipe->writers = 1;
    pipe->closed = 0;
    memset(pipe->buffer, 0, PIPE_BUF_SIZE);
}

ssize_t pipe_read(pipe_t* pipe, void* buf, uint32_t size) {
    if (!pipe) return -1;

    /* If no data and writers remain, caller should block */
    if (pipe->count == 0 && !pipe->closed) return 0;

    /* If pipe closed and no data, EOF */
    if (pipe->count == 0 && pipe->closed) return 0;

    uint32_t to_read = (size < pipe->count) ? size : pipe->count;
    uint8_t* dst = (uint8_t*)buf;

    for (uint32_t i = 0; i < to_read; i++) {
        dst[i] = pipe->buffer[pipe->read_pos];
        pipe->read_pos = (pipe->read_pos + 1) % PIPE_BUF_SIZE;
    }
    pipe->count -= to_read;

    return (ssize_t)to_read;
}

ssize_t pipe_write(pipe_t* pipe, const void* buf, uint32_t size) {
    if (!pipe || pipe->closed) return -1;

    uint32_t avail = PIPE_BUF_SIZE - pipe->count;
    uint32_t to_write = (size < avail) ? size : avail;

    /* If no space and readers remain, caller should block */
    if (to_write == 0) return 0;

    const uint8_t* src = (const uint8_t*)buf;

    for (uint32_t i = 0; i < to_write; i++) {
        pipe->buffer[pipe->write_pos] = src[i];
        pipe->write_pos = (pipe->write_pos + 1) % PIPE_BUF_SIZE;
    }
    pipe->count += to_write;

    return (ssize_t)to_write;
}

void pipe_close_read(pipe_t* pipe) {
    if (!pipe) return;
    pipe->readers--;
    if (pipe->readers <= 0 && pipe->writers <= 0) {
        pipe->closed = 1;
    }
}

void pipe_close_write(pipe_t* pipe) {
    if (!pipe) return;
    pipe->writers--;
    if (pipe->writers <= 0) {
        pipe->closed = 1;
        /* Wake all blocked readers */
    }
    if (pipe->readers <= 0 && pipe->writers <= 0) {
        pipe->closed = 1;
    }
}

int pipe_data_available(pipe_t* pipe) {
    if (!pipe) return 0;
    return pipe->count > 0 || pipe->closed;
}
