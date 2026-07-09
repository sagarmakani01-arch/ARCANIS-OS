#ifndef ARCANIS_FD_H
#define ARCANIS_FD_H

#include <arcanis/types.h>
#include <arcanis/vfs.h>

#define FD_MAX 64

enum fd_flags {
    FD_READABLE = 0x01,
    FD_WRITABLE = 0x02,
    FD_APPEND   = 0x04,
    FD_PIPE     = 0x08,
};

typedef struct {
    vfs_node_t* node;
    uint32_t    offset;
    uint32_t    flags;
    uint8_t     in_use;
} fd_entry_t;

typedef struct {
    fd_entry_t entries[FD_MAX];
    uint32_t   count;
} fd_table_t;

void     fd_table_init(fd_table_t* table);
int      fd_open(fd_table_t* table, vfs_node_t* node, uint32_t flags);
int      fd_close(fd_table_t* table, int fd);
ssize_t  fd_read(fd_table_t* table, int fd, void* buf, uint32_t size);
ssize_t  fd_write(fd_table_t* table, int fd, const void* buf, uint32_t size);
int      fd_dup(fd_table_t* table, int fd);
int      fd_pipe(fd_table_t* table, int fds[2]);

#endif
