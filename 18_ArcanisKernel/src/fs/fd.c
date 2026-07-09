/**
 * fd.c — File Descriptor Table
 *
 * Per-process file descriptor management.
 * Maps integer FDs to VFS nodes with offset tracking.
 * Supports pipes for IPC.
 */
#include <arcanis/fd.h>
#include <arcanis/string.h>

void fd_table_init(fd_table_t* table) {
    for (int i = 0; i < FD_MAX; i++) {
        table->entries[i].in_use = 0;
        table->entries[i].node = NULL;
        table->entries[i].offset = 0;
        table->entries[i].flags = 0;
    }
    table->count = 0;
}

int fd_open(fd_table_t* table, vfs_node_t* node, uint32_t flags) {
    if (!table || !node) return -1;

    /* Find first free slot */
    for (int i = 0; i < FD_MAX; i++) {
        if (!table->entries[i].in_use) {
            table->entries[i].in_use = 1;
            table->entries[i].node = node;
            table->entries[i].offset = 0;
            table->entries[i].flags = flags;
            table->count++;

            if (node->ops && node->ops->open)
                node->ops->open(node);

            return i;
        }
    }
    return -1; /* no free fds */
}

int fd_close(fd_table_t* table, int fd) {
    if (!table || fd < 0 || fd >= FD_MAX) return -1;
    if (!table->entries[fd].in_use) return -1;

    fd_entry_t* entry = &table->entries[fd];

    if (entry->node && entry->node->ops && entry->node->ops->close)
        entry->node->ops->close(entry->node);

    entry->in_use = 0;
    entry->node = NULL;
    entry->offset = 0;
    entry->flags = 0;
    table->count--;
    return 0;
}

ssize_t fd_read(fd_table_t* table, int fd, void* buf, uint32_t size) {
    if (!table || fd < 0 || fd >= FD_MAX) return -1;
    fd_entry_t* entry = &table->entries[fd];
    if (!entry->in_use || !entry->node) return -1;

    vfs_node_t* node = entry->node;

    /* Pipe read */
    if (entry->flags & FD_PIPE) {
        /* TODO: pipe buffer read */
        return -1;
    }

    /* Regular file read */
    if (node->ops && node->ops->read) {
        ssize_t result = node->ops->read(node, entry->offset, size, (uint8_t*)buf);
        if (result > 0) entry->offset += result;
        return result;
    }

    /* Direct data read */
    if (node->data && node->type == VFS_FILE) {
        uint32_t avail = node->length - entry->offset;
        uint32_t to_read = (size < avail) ? size : avail;
        if (to_read == 0) return 0;
        for (uint32_t i = 0; i < to_read; i++)
            ((uint8_t*)buf)[i] = node->data[entry->offset + i];
        entry->offset += to_read;
        return (ssize_t)to_read;
    }

    return -1;
}

ssize_t fd_write(fd_table_t* table, int fd, const void* buf, uint32_t size) {
    if (!table || fd < 0 || fd >= FD_MAX) return -1;
    fd_entry_t* entry = &table->entries[fd];
    if (!entry->in_use || !entry->node) return -1;

    vfs_node_t* node = entry->node;

    /* Pipe write */
    if (entry->flags & FD_PIPE) {
        /* TODO: pipe buffer write */
        return -1;
    }

    /* Regular file write */
    if (node->ops && node->ops->write) {
        ssize_t result = node->ops->write(node, entry->offset, size, (uint8_t*)buf);
        if (result > 0) entry->offset += result;
        return result;
    }

    /* Direct data write */
    if (node->type == VFS_FILE) {
        if (!node->data) {
            /* Allocate initial buffer */
            node->data = (uint8_t*)kmalloc(size + 256);
            if (!node->data) return -1;
        }
        if (entry->offset + size > node->length) {
            /* Extend buffer */
            uint8_t* new_data = (uint8_t*)kmalloc(entry->offset + size + 256);
            if (!new_data) return -1;
            for (uint32_t i = 0; i < node->length; i++)
                new_data[i] = node->data[i];
            kfree(node->data);
            node->data = new_data;
        }
        for (uint32_t i = 0; i < size; i++)
            node->data[entry->offset + i] = ((const uint8_t*)buf)[i];
        entry->offset += size;
        if (entry->offset > node->length)
            node->length = entry->offset;
        return (ssize_t)size;
    }

    return -1;
}

int fd_dup(fd_table_t* table, int fd) {
    if (!table || fd < 0 || fd >= FD_MAX) return -1;
    if (!table->entries[fd].in_use) return -1;

    /* Find free slot and copy */
    for (int i = 0; i < FD_MAX; i++) {
        if (!table->entries[i].in_use) {
            table->entries[i] = table->entries[fd];
            table->count++;
            return i;
        }
    }
    return -1;
}

int fd_pipe(fd_table_t* table, int fds[2]) {
    if (!table) return -1;

    /* Allocate two fds */
    int fd0 = -1, fd1 = -1;
    for (int i = 0; i < FD_MAX; i++) {
        if (!table->entries[i].in_use) {
            if (fd0 == -1) fd0 = i;
            else { fd1 = i; break; }
        }
    }
    if (fd0 == -1 || fd1 == -1) return -1;

    /* Create pipe node */
    vfs_node_t* pipe_node = vfs_create_node("pipe", VFS_PIPE);
    if (!pipe_node) return -1;

    /* Allocate pipe buffer (4KB) */
    pipe_node->data = (uint8_t*)kmalloc(4096);
    if (!pipe_node->data) return -1;
    pipe_node->length = 0;

    /* Setup read end */
    table->entries[fd0].in_use = 1;
    table->entries[fd0].node = pipe_node;
    table->entries[fd0].offset = 0;
    table->entries[fd0].flags = FD_READABLE | FD_PIPE;

    /* Setup write end (shares same node) */
    table->entries[fd1].in_use = 1;
    table->entries[fd1].node = pipe_node;
    table->entries[fd1].offset = 0;
    table->entries[fd1].flags = FD_WRITABLE | FD_PIPE;

    table->count += 2;

    fds[0] = fd0;
    fds[1] = fd1;
    return 0;
}
