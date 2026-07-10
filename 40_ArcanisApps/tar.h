/**
 * arcanis_tar.h — File Archiver (TAR format)
 *
 * Create and extract tar archives.
 * Supports ustar format with file metadata.
 */
#ifndef ARCANIS_TAR_H
#define ARCANIS_TAR_H

#include <arcanis/types.h>

#define TAR_BLOCK_SIZE    512
#define TAR_MAX_PATH     100
#define TAR_MAX_NAME      32
#define TAR_MAX_UNAME     32
#define TAR_MAX_GNAME     32
#define TAR_MAX_DEVICES   8

#pragma pack(push, 1)
typedef struct {
    char name[TAR_MAX_PATH];
    char mode[8];
    char uid[8];
    char gid[8];
    char size[12];
    char mtime[12];
    char chksum[8];
    char typeflag;
    char linkname[TAR_MAX_PATH];
    char magic[6];
    char version[2];
    char uname[TAR_MAX_UNAME];
    char gname[TAR_MAX_GNAME];
    char devmajor[8];
    char devminor[8];
    char prefix[155];
} tar_header_t;
#pragma pack(pop)

typedef enum {
    TAR_FILE_REGULAR    = '0',
    TAR_FILE_HARDLINK   = '1',
    TAR_FILE_SYMLINK    = '2',
    TAR_FILE_CHARDEV    = '3',
    TAR_FILE_BLOCKDEV   = '4',
    TAR_FILE_DIRECTORY  = '5',
    TAR_FILE_FIFO       = '6',
    TAR_FILE_CONTIGUOUS = '7'
} tar_type_t;

typedef struct {
    char        path[256];
    tar_type_t  type;
    uint32_t    size;
    uint32_t    mode;
    uint32_t    uid;
    uint32_t    gid;
    uint32_t    mtime;
    uint8_t*    data;
    uint32_t    data_size;
} tar_entry_t;

typedef struct {
    tar_entry_t entries[256];
    uint32_t    num_entries;
    uint32_t    total_size;
    uint8_t*    archive;
    uint32_t    archive_size;
    int         error;
    char        error_msg[128];
} tar_archive_t;

/* Initialize archive */
void tar_init(tar_archive_t* tar);

/* Create archive */
int  tar_create(tar_archive_t* tar, const char** files, uint32_t num_files);
int  tar_add_file(tar_archive_t* tar, const char* path, const uint8_t* data, uint32_t size);
int  tar_add_dir(tar_archive_t* tar, const char* path);

/* Extract archive */
int  tar_extract(tar_archive_t* tar, const uint8_t* data, uint32_t size);
int  tar_extract_entry(tar_archive_t* tar, const tar_entry_t* entry, const char* dest);

/* List archive contents */
int  tar_list(tar_archive_t* tar, const uint8_t* data, uint32_t size);

/* Header operations */
void tar_init_header(tar_header_t* header);
int  tar_calc_checksum(const tar_header_t* header);
void tar_set_octal(char* field, uint32_t value, uint32_t len);
uint32_t tar_get_octal(const char* field, uint32_t len);
void tar_set_filename(tar_header_t* header, const char* filename);

/* Utility */
uint32_t tar_checksum(const uint8_t* data, uint32_t size);
void     tar_write_header(tar_header_t* header, uint8_t* buf);
int      tar_read_header(const uint8_t* buf, tar_header_t* header);

#endif
