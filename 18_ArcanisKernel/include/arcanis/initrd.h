#ifndef ARCANIS_INITRD_H
#define ARCANIS_INITRD_H

#include <arcanis/types.h>
#include <arcanis/vfs.h>

typedef struct {
    uint32_t nfiles;
} initrd_header_t;

typedef struct {
    uint8_t  magic;
    char     name[64];
    uint32_t offset;
    uint32_t length;
} initrd_file_header_t;

vfs_node_t* initrd_initialize(uint32_t location);

#endif
