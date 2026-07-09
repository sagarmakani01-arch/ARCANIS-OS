#include <arcanis/initrd.h>
#include <arcanis/vfs.h>
#include <arcanis/heap.h>
#include <arcanis/string.h>
#include <arcanis/types.h>

static initrd_header_t* initrd_header;
static initrd_file_header_t* initrd_files;

static ssize_t initrd_read(vfs_node_t* node, uint32_t offset, uint32_t size, uint8_t* buffer) {
    initrd_file_header_t* file = (initrd_file_header_t*)node->data;
    if (!file) return -1;

    uint32_t max_size = file->length - offset;
    uint32_t read_size = MIN(size, max_size);

    uint8_t* file_data = (uint8_t*)((uint32_t)initrd_header + file->offset);
    memcpy(buffer, file_data + offset, read_size);

    return read_size;
}

vfs_node_t* initrd_initialize(uint32_t location) {
    initrd_header = (initrd_header_t*)location;
    initrd_files = (initrd_file_header_t*)(location + sizeof(initrd_header_t));

    vfs_node_t* root = vfs_create_node("initrd", VFS_DIRECTORY);

    for (uint32_t i = 0; i < initrd_header->nfiles; i++) {
        initrd_file_header_t* file = &initrd_files[i];

        vfs_node_t* node = vfs_create_node(file->name, VFS_FILE);
        node->length = file->length;
        node->data = (uint8_t*)file;

        vfs_operations_t* ops = (vfs_operations_t*)kmalloc(sizeof(vfs_operations_t));
        ops->read = initrd_read;
        ops->write = NULL;
        ops->open = NULL;
        ops->close = NULL;
        ops->readdir = NULL;
        ops->finddir = NULL;
        node->ops = ops;

        node->next = root->children;
        root->children = node;
    }

    return root;
}
