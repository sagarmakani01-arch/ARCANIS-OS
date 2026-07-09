#ifndef ARCANIS_PIPE_H
#define ARCANIS_PIPE_H

#include <arcanis/types.h>

#define PIPE_BUF_SIZE 4096

typedef struct {
    uint8_t  buffer[PIPE_BUF_SIZE];
    uint32_t read_pos;
    uint32_t write_pos;
    uint32_t count;
    int      readers;
    int      writers;
    int      closed;
} pipe_t;

void     pipe_init(pipe_t* pipe);
ssize_t  pipe_read(pipe_t* pipe, void* buf, uint32_t size);
ssize_t  pipe_write(pipe_t* pipe, const void* buf, uint32_t size);
void     pipe_close_read(pipe_t* pipe);
void     pipe_close_write(pipe_t* pipe);
int      pipe_data_available(pipe_t* pipe);

#endif
