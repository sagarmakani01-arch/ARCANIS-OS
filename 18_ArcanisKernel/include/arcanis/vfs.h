#ifndef ARCANIS_VFS_H
#define ARCANIS_VFS_H

#include <arcanis/types.h>

#define VFS_NAME_MAX 256

enum vfs_node_type {
    VFS_FILE      = 0x01,
    VFS_DIRECTORY = 0x02,
    VFS_CHARDEV   = 0x04,
    VFS_BLOCKDEV  = 0x08,
    VFS_SYMLINK   = 0x10,
    VFS_PIPE      = 0x20,
};

typedef struct vfs_node {
    char                  name[VFS_NAME_MAX];
    enum vfs_node_type    type;
    uint32_t              length;
    uint32_t              inode;
    uint32_t              flags;
    struct vfs_operations* ops;
    struct vfs_node*      children;
    struct vfs_node*      next;
    uint8_t*              data;
} vfs_node_t;

typedef struct vfs_operations {
    ssize_t (*read)(vfs_node_t*, uint32_t, uint32_t, uint8_t*);
    ssize_t (*write)(vfs_node_t*, uint32_t, uint32_t, uint8_t*);
    void    (*open)(vfs_node_t*);
    void    (*close)(vfs_node_t*);
    ssize_t (*readdir)(vfs_node_t*, uint32_t, vfs_node_t*);
    ssize_t (*finddir)(vfs_node_t*, const char*, vfs_node_t*);
} vfs_operations_t;

void vfs_initialize(void);
vfs_node_t* vfs_create_node(const char* name, enum vfs_node_type type);
void vfs_mount(vfs_node_t* node);
ssize_t vfs_read(vfs_node_t* node, uint32_t offset, uint32_t size, uint8_t* buffer);
ssize_t vfs_write(vfs_node_t* node, uint32_t offset, uint32_t size, uint8_t* buffer);
vfs_node_t* vfs_find(const char* path);

#endif
