#include <arcanis/vfs.h>
#include <arcanis/heap.h>
#include <arcanis/string.h>
#include <arcanis/types.h>

static vfs_node_t* vfs_root = NULL;

void vfs_initialize(void) {
    vfs_root = vfs_create_node("/", VFS_DIRECTORY);
}

vfs_node_t* vfs_create_node(const char* name, enum vfs_node_type type) {
    vfs_node_t* node = (vfs_node_t*)kmalloc(sizeof(vfs_node_t));
    if (!node) return NULL;

    memset(node, 0, sizeof(vfs_node_t));
    strncpy(node->name, name, VFS_NAME_MAX - 1);
    node->type = type;
    node->length = 0;
    node->inode = 0;
    node->flags = 0;
    node->ops = NULL;
    node->children = NULL;
    node->next = NULL;
    node->data = NULL;

    return node;
}

void vfs_mount(vfs_node_t* node) {
    if (!vfs_root) {
        vfs_root = node;
        return;
    }

    node->next = vfs_root->children;
    vfs_root->children = node;
}

ssize_t vfs_read(vfs_node_t* node, uint32_t offset, uint32_t size, uint8_t* buffer) {
    if (!node) return -1;
    if (node->ops && node->ops->read) {
        return node->ops->read(node, offset, size, buffer);
    }
    if (node->data) {
        uint32_t bytes = MIN(size, node->length - offset);
        memcpy(buffer, node->data + offset, bytes);
        return bytes;
    }
    return -1;
}

ssize_t vfs_write(vfs_node_t* node, uint32_t offset, uint32_t size, uint8_t* buffer) {
    if (!node) return -1;
    if (node->ops && node->ops->write) {
        return node->ops->write(node, offset, size, buffer);
    }
    return -1;
}

vfs_node_t* vfs_find(const char* path) {
    if (!vfs_root) return NULL;
    if (strcmp(path, "/") == 0) return vfs_root;

    vfs_node_t* current = vfs_root->children;
    while (current) {
        if (strcmp(current->name, path) == 0) return current;
        current = current->next;
    }

    return NULL;
}
