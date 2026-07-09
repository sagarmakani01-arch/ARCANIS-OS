#ifndef ARCANIS_FS_H
#define ARCANIS_FS_H

#include <arcanis/types.h>
#include <arcanis/vfs.h>

#define FS_MAX_FILES   256
#define FS_NAME_MAX    64
#define FS_BLOCK_SIZE  512
#define FS_MAX_BLOCKS  8192
#define FS_MAGIC       0x4152434E  /* "ARCN" */

/* File types */
#define FS_TYPE_FILE    1
#define FS_TYPE_DIR     2
#define FS_TYPE_LINK    4

/* File flags */
#define FS_FLAG_DIRTY   0x01
#define FS_FLAG_RDONLY   0x02

typedef struct {
    char     name[FS_NAME_MAX];
    uint32_t inode;
    uint32_t type;
    uint32_t size;
    uint32_t blocks[16];   /* direct block pointers */
    uint32_t parent_inode;
    uint32_t flags;
} fs_file_t;

typedef struct {
    uint32_t magic;
    uint32_t total_blocks;
    uint32_t free_blocks;
    uint32_t root_inode;
    uint32_t file_count;
    uint32_t block_bitmap[FS_MAX_BLOCKS / 32];
    fs_file_t files[FS_MAX_FILES];
} fs_superblock_t;

typedef struct {
    fs_superblock_t super;
    uint8_t*        block_data;
    uint32_t        block_data_size;
    int             dirty;
    void*           ata_drive;
} fs_t;

void     fs_initialize(fs_t* fs);
int      fs_format(fs_t* fs);
int      fs_mount(fs_t* fs);
int      fs_create_file(fs_t* fs, const char* path, uint32_t type);
int      fs_delete(fs_t* fs, const char* path);
fs_file_t* fs_find(fs_t* fs, const char* path);
int      fs_read(fs_t* fs, const char* path, uint32_t offset, uint32_t size, uint8_t* buf);
int      fs_write(fs_t* fs, const char* path, uint32_t offset, uint32_t size, const uint8_t* buf);
int      fs_list_dir(fs_t* fs, const char* path, fs_file_t* out, uint32_t max);
int      fs_mkdir(fs_t* fs, const char* path);
int      fs_sync(fs_t* fs);
int      fs_get_free_block(fs_t* fs);
void     fs_free_block(fs_t* fs, uint32_t block);

#endif
