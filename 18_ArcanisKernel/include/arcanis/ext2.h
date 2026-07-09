/**
 * ext2.h — ext2 Filesystem Driver
 *
 * Read/write ext2 filesystems on disk.
 * Supports inodes, directories, and file I/O.
 */
#ifndef ARCANIS_EXT2_H
#define ARCANIS_EXT2_H

#include <arcanis/types.h>

#define EXT2_BLOCK_SIZE   1024
#define EXT2_INODE_SIZE   128
#define EXT2_ROOT_INO     2
#define EXT2_SUPER_OFFSET 1024

/* Superblock fields */
typedef struct {
    uint32_t s_inodes_count;
    uint32_t s_blocks_count;
    uint32_t s_r_blocks_count;
    uint32_t s_free_blocks_count;
    uint32_t s_free_inodes_count;
    uint32_t s_first_data_block;
    uint32_t s_log_block_size;
    uint32_t s_log_frag_size;
    uint32_t s_blocks_per_group;
    uint32_t s_frags_per_group;
    uint32_t s_inodes_per_group;
    uint32_t s_mtime;
    uint32_t s_wtime;
    uint16_t s_mnt_count;
    uint16_t s_max_mnt_count;
    uint16_t s_magic;
    uint16_t s_state;
    uint32_t s_first_ino;
    uint16_t s_inode_size;
    uint16_t s_block_group_nr;
    uint32_t s_feature_compat;
    uint32_t s_feature_incompat;
    uint32_t s_feature_ro_compat;
    char     s_uuid[16];
    char     s_volume_name[16];
    char     s_last_mounted[64];
    uint32_t s_algo_bitmap;
} ext2_superblock_t;

/* Group descriptor */
typedef struct {
    uint32_t bg_block_bitmap;
    uint32_t bg_inode_bitmap;
    uint32_t bg_inode_table;
    uint16_t bg_free_blocks_count;
    uint16_t bg_free_inodes_count;
    uint16_t bg_used_dirs_count;
    uint16_t bg_pad;
    uint8_t  bg_reserved[12];
} ext2_group_desc_t;

/* Inode */
typedef struct {
    uint16_t i_mode;
    uint16_t i_uid;
    uint32_t i_size;
    uint32_t i_atime;
    uint32_t i_ctime;
    uint32_t i_mtime;
    uint32_t i_dtime;
    uint16_t i_gid;
    uint16_t i_links_count;
    uint32_t i_blocks;
    uint32_t i_flags;
    uint32_t i_osd1;
    uint32_t i_block[15];  /* 0-11: direct, 12: indirect, 13: double, 14: triple */
    uint32_t i_generation;
    uint32_t i_file_acl;
    uint32_t i_dir_acl;
    uint32_t i_faddr;
    uint8_t  i_osd2[12];
} ext2_inode_t;

/* Directory entry */
typedef struct {
    uint32_t inode;
    uint16_t rec_len;
    uint8_t  name_len;
    uint8_t  file_type;
    char     name[];
} ext2_dirent_t;

/* File types */
#define EXT2_FT_UNKNOWN  0
#define EXT2_FT_REG_FILE 1
#define EXT2_FT_DIR      2
#define EXT2_FT_CHRDEV   3
#define EXT2_FT_BLKDEV   4
#define EXT2_FT_FIFO     5
#define EXT2_FT_SOCK     6
#define EXT2_FT_SYMLINK  7

/* Permission bits */
#define EXT2_S_IFSOCK  0xC000
#define EXT2_S_IFLNK   0xA000
#define EXT2_S_IFREG   0x8000
#define EXT2_S_IFBLK   0x6000
#define EXT2_S_IFDIR   0x4000
#define EXT2_S_IFCHR   0x2000
#define EXT2_S_IFIFO   0x1000
#define EXT2_S_PERM    0x0FFF

typedef struct {
    ext2_superblock_t super;
    ext2_group_desc_t* groups;
    uint32_t block_size;
    uint32_t num_groups;
    uint8_t* block_buffer;
    void*    ata_drive;
    int      dirty;
} ext2_fs_t;

int      ext2_mount(ext2_fs_t* fs, void* ata_drive);
int      ext2_read_inode(ext2_fs_t* fs, uint32_t ino, ext2_inode_t* inode);
int      ext2_write_inode(ext2_fs_t* fs, uint32_t ino, const ext2_inode_t* inode);
int      ext2_read_block(ext2_fs_t* fs, uint32_t block, uint8_t* buf);
int      ext2_write_block(ext2_fs_t* fs, uint32_t block, const uint8_t* buf);
uint32_t ext2_alloc_inode(ext2_fs_t* fs);
uint32_t ext2_alloc_block(ext2_fs_t* fs);
void     ext2_free_inode(ext2_fs_t* fs, uint32_t ino);
void     ext2_free_block(ext2_fs_t* fs, uint32_t block);
int      ext2_lookup(ext2_fs_t* fs, uint32_t dir_ino, const char* name);
int      ext2_create_file(ext2_fs_t* fs, uint32_t dir_ino, const char* name, uint16_t mode);
int      ext2_read_file(ext2_fs_t* fs, uint32_t ino, uint32_t offset, uint32_t size, uint8_t* buf);
int      ext2_write_file(ext2_fs_t* fs, uint32_t ino, uint32_t offset, uint32_t size, const uint8_t* buf);
int      ext2_mkdir(ext2_fs_t* fs, uint32_t dir_ino, const char* name);
int      ext2_readdir(ext2_fs_t* fs, uint32_t dir_ino, ext2_dirent_t* out, uint32_t max);
int      ext2_format(ext2_fs_t* fs);

#endif
