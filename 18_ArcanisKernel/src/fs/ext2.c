/**
 * ext2.c — ext2 Filesystem Implementation
 *
 * Full ext2 read/write support with inodes, directories, and file I/O.
 */
#include <arcanis/ext2.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <arcanis/ata.h>

static uint32_t ext2_block_from_offset(ext2_fs_t* fs, ext2_inode_t* inode, uint32_t offset) {
    uint32_t block_size = fs->block_size;
    uint32_t block_idx = offset / block_size;
    uint32_t blocks_per_indirect = block_size / 4;

    if (block_idx < 12) return inode->i_block[block_idx];
    block_idx -= 12;

    if (block_idx < blocks_per_indirect) {
        uint32_t indirect[256];
        ext2_read_block(fs, inode->i_block[12], (uint8_t*)indirect);
        return indirect[block_idx];
    }
    block_idx -= blocks_per_indirect;

    if (block_idx < blocks_per_indirect * blocks_per_indirect) {
        uint32_t double_idx = block_idx / blocks_per_indirect;
        uint32_t single_idx = block_idx % blocks_per_indirect;
        uint32_t double_indirect[256];
        ext2_read_block(fs, inode->i_block[13], (uint8_t*)double_indirect);
        uint32_t indirect[256];
        ext2_read_block(fs, double_indirect[double_idx], (uint8_t*)indirect);
        return indirect[single_idx];
    }
    return 0;
}

int ext2_mount(ext2_fs_t* fs, void* ata_drive) {
    if (!fs) return -1;
    fs->ata_drive = ata_drive;
    fs->block_size = EXT2_BLOCK_SIZE;
    fs->block_buffer = (uint8_t*)kmalloc(EXT2_BLOCK_SIZE);
    if (!fs->block_buffer) return -1;

    /* Read superblock */
    if (ata_drive) {
        ata_read_sectors((ata_drive_t*)ata_drive, 2, 2, fs->block_buffer);
        memcpy(&fs->super, fs->block_buffer, sizeof(ext2_superblock_t));
    } else {
        /* Initialize default superblock */
        memset(&fs->super, 0, sizeof(ext2_superblock_t));
        fs->super.s_magic = 0xEF53;
        fs->super.s_inodes_count = 1024;
        fs->super.s_blocks_count = 8192;
        fs->super.s_free_inodes_count = 1000;
        fs->super.s_free_blocks_count = 7000;
        fs->super.s_first_data_block = 1;
        fs->super.s_log_block_size = 0; /* 1024 */
        fs->super.s_inodes_per_group = 128;
        fs->super.s_blocks_per_group = 8192;
        fs->super.s_first_ino = 11;
        fs->super.s_inode_size = EXT2_INODE_SIZE;
    }

    if (fs->super.s_magic != 0xEF53) return -1;

    fs->num_groups = (fs->super.s_blocks_count + fs->super.s_blocks_per_group - 1)
                     / fs->super.s_blocks_per_group;

    /* Read group descriptors */
    uint32_t gd_blocks = (fs->num_groups * sizeof(ext2_group_desc_t) + EXT2_BLOCK_SIZE - 1)
                         / EXT2_BLOCK_SIZE;
    fs->groups = (ext2_group_desc_t*)kmalloc(gd_blocks * EXT2_BLOCK_SIZE);
    if (!fs->groups) return -1;

    if (ata_drive) {
        uint32_t gd_lba = (EXT2_SUPER_OFFSET + EXT2_BLOCK_SIZE) / 512;
        ata_read_sectors((ata_drive_t*)ata_drive, gd_lba, gd_blocks * 2, (uint8_t*)fs->groups);
    }

    fs->dirty = 0;
    return 0;
}

int ext2_read_block(ext2_fs_t* fs, uint32_t block, uint8_t* buf) {
    if (!fs || !buf) return -1;
    if (fs->ata_drive) {
        uint32_t lba = (block * fs->block_size) / 512;
        uint32_t sectors = fs->block_size / 512;
        return ata_read_sectors((ata_drive_t*)fs->ata_drive, lba, sectors, buf);
    }
    return -1;
}

int ext2_write_block(ext2_fs_t* fs, uint32_t block, const uint8_t* buf) {
    if (!fs || !buf) return -1;
    if (fs->ata_drive) {
        uint32_t lba = (block * fs->block_size) / 512;
        uint32_t sectors = fs->block_size / 512;
        return ata_write_sectors((ata_drive_t*)fs->ata_drive, lba, sectors, buf);
    }
    return -1;
}

int ext2_read_inode(ext2_fs_t* fs, uint32_t ino, ext2_inode_t* inode) {
    if (!fs || !inode || ino < EXT2_ROOT_INO) return -1;
    uint32_t group = (ino - 1) / fs->super.s_inodes_per_group;
    uint32_t index = (ino - 1) % fs->super.s_inodes_per_group;
    if (group >= fs->num_groups) return -1;

    uint32_t inode_table_block = fs->groups[group].bg_inode_table;
    uint32_t offset = inode_table_block * fs->block_size + index * fs->super.s_inode_size;

    uint8_t buf[EXT2_INODE_SIZE];
    uint32_t block = offset / fs->block_size;
    uint32_t block_off = offset % fs->block_size;
    ext2_read_block(fs, block, buf);
    memcpy(inode, buf + block_off, sizeof(ext2_inode_t));
    return 0;
}

int ext2_write_inode(ext2_fs_t* fs, uint32_t ino, const ext2_inode_t* inode) {
    if (!fs || !inode || ino < EXT2_ROOT_INO) return -1;
    uint32_t group = (ino - 1) / fs->super.s_inodes_per_group;
    uint32_t index = (ino - 1) % fs->super.s_inodes_per_group;
    if (group >= fs->num_groups) return -1;

    uint32_t inode_table_block = fs->groups[group].bg_inode_table;
    uint32_t offset = inode_table_block * fs->block_size + index * fs->super.s_inode_size;

    uint8_t buf[EXT2_INODE_SIZE];
    uint32_t block = offset / fs->block_size;
    uint32_t block_off = offset % fs->block_size;
    ext2_read_block(fs, block, buf);
    memcpy(buf + block_off, inode, sizeof(ext2_inode_t));
    ext2_write_block(fs, block, buf);
    return 0;
}

uint32_t ext2_alloc_inode(ext2_fs_t* fs) {
    for (uint32_t g = 0; g < fs->num_groups; g++) {
        if (fs->groups[g].bg_free_inodes_count > 0) {
            uint8_t bitmap[1024];
            uint32_t bitmap_block = fs->groups[g].bg_inode_bitmap;
            ext2_read_block(fs, bitmap_block, bitmap);

            uint32_t inodes_per_group = fs->super.s_inodes_per_group;
            for (uint32_t i = 0; i < inodes_per_group; i++) {
                if (!(bitmap[i / 8] & (1 << (i % 8)))) {
                    bitmap[i / 8] |= (1 << (i % 8));
                    ext2_write_block(fs, bitmap_block, bitmap);
                    fs->groups[g].bg_free_inodes_count--;
                    fs->super.s_free_inodes_count--;
                    fs->dirty = 1;
                    return g * inodes_per_group + i + 1;
                }
            }
        }
    }
    return 0;
}

uint32_t ext2_alloc_block(ext2_fs_t* fs) {
    for (uint32_t g = 0; g < fs->num_groups; g++) {
        if (fs->groups[g].bg_free_blocks_count > 0) {
            uint8_t bitmap[1024];
            uint32_t bitmap_block = fs->groups[g].bg_block_bitmap;
            ext2_read_block(fs, bitmap_block, bitmap);

            uint32_t blocks_per_group = fs->super.s_blocks_per_group;
            for (uint32_t i = 0; i < blocks_per_group; i++) {
                if (!(bitmap[i / 8] & (1 << (i % 8)))) {
                    bitmap[i / 8] |= (1 << (i % 8));
                    ext2_write_block(fs, bitmap_block, bitmap);
                    fs->groups[g].bg_free_blocks_count--;
                    fs->super.s_free_blocks_count--;
                    fs->dirty = 1;
                    return g * blocks_per_group + i;
                }
            }
        }
    }
    return 0;
}

void ext2_free_inode(ext2_fs_t* fs, uint32_t ino) {
    uint32_t group = (ino - 1) / fs->super.s_inodes_per_group;
    uint32_t index = (ino - 1) % fs->super.s_inodes_per_group;

    uint8_t bitmap[1024];
    ext2_read_block(fs, fs->groups[group].bg_inode_bitmap, bitmap);
    bitmap[index / 8] &= ~(1 << (index % 8));
    ext2_write_block(fs, fs->groups[group].bg_inode_bitmap, bitmap);
    fs->groups[group].bg_free_inodes_count++;
    fs->super.s_free_inodes_count++;
    fs->dirty = 1;
}

void ext2_free_block(ext2_fs_t* fs, uint32_t block) {
    uint32_t group = block / fs->super.s_blocks_per_group;
    uint32_t index = block % fs->super.s_blocks_per_group;

    uint8_t bitmap[1024];
    ext2_read_block(fs, fs->groups[group].bg_block_bitmap, bitmap);
    bitmap[index / 8] &= ~(1 << (index % 8));
    ext2_write_block(fs, fs->groups[group].bg_block_bitmap, bitmap);
    fs->groups[group].bg_free_blocks_count++;
    fs->super.s_free_blocks_count++;
    fs->dirty = 1;
}

int ext2_lookup(ext2_fs_t* fs, uint32_t dir_ino, const char* name) {
    ext2_inode_t dir;
    if (ext2_read_inode(fs, dir_ino, &dir) != 0) return -1;
    if (!(dir.i_mode & EXT2_S_IFDIR)) return -1;

    uint32_t size = dir.i_size;
    uint8_t* buf = (uint8_t*)kmalloc(size + EXT2_BLOCK_SIZE);
    if (!buf) return -1;

    /* Read directory content */
    uint32_t offset = 0;
    uint32_t total = 0;
    while (offset < size) {
        uint32_t block = ext2_block_from_offset(fs, &dir, offset);
        if (block == 0) break;
        uint32_t to_read = size - offset;
        if (to_read > fs->block_size) to_read = fs->block_size;
        ext2_read_block(fs, block, buf + total);
        total += to_read;
        offset += to_read;
    }

    /* Parse directory entries */
    offset = 0;
    while (offset < total) {
        ext2_dirent_t* entry = (ext2_dirent_t*)(buf + offset);
        if (entry->inode == 0) { offset += entry->rec_len; continue; }
        if (entry->name_len == string_length(name) &&
            string_compare(entry->name, name) == 0) {
            uint32_t result = entry->inode;
            kfree(buf);
            return (int)result;
        }
        offset += entry->rec_len;
    }

    kfree(buf);
    return -1;
}

int ext2_create_file(ext2_fs_t* fs, uint32_t dir_ino, const char* name, uint16_t mode) {
    uint32_t ino = ext2_alloc_inode(fs);
    if (ino == 0) return -1;

    ext2_inode_t inode;
    memset(&inode, 0, sizeof(ext2_inode_t));
    inode.i_mode = mode | EXT2_S_IFREG;
    inode.i_links_count = 1;
    inode.i_size = 0;
    inode.i_blocks = 0;
    ext2_write_inode(fs, ino, &inode);

    /* Add entry to directory */
    ext2_inode_t dir;
    ext2_read_inode(fs, dir_ino, &dir);

    uint32_t block = dir.i_block[0];
    uint8_t block_buf[1024];
    ext2_read_block(fs, block, block_buf);

    /* Find end of directory */
    uint32_t offset = 0;
    while (offset < fs->block_size) {
        ext2_dirent_t* entry = (ext2_dirent_t*)(block_buf + offset);
        if (entry->rec_len == 0) break;
        offset += entry->rec_len;
    }

    /* Add new entry */
    ext2_dirent_t* new_entry = (ext2_dirent_t*)(block_buf + offset);
    uint32_t name_len = string_length(name);
    uint32_t rec_len = 8 + name_len;
    if (rec_len % 4) rec_len += 4 - (rec_len % 4);

    new_entry->inode = ino;
    new_entry->rec_len = rec_len;
    new_entry->name_len = name_len;
    new_entry->file_type = EXT2_FT_REG_FILE;
    memcpy(new_entry->name, name, name_len);

    ext2_write_block(fs, block, block_buf);
    fs->dirty = 1;
    return 0;
}

int ext2_read_file(ext2_fs_t* fs, uint32_t ino, uint32_t offset, uint32_t size, uint8_t* buf) {
    ext2_inode_t inode;
    if (ext2_read_inode(fs, ino, &inode) != 0) return -1;

    uint32_t bytes_read = 0;
    while (bytes_read < size) {
        uint32_t block = ext2_block_from_offset(fs, &inode, offset + bytes_read);
        if (block == 0) break;
        uint32_t block_off = (offset + bytes_read) % fs->block_size;
        uint32_t to_read = fs->block_size - block_off;
        if (to_read > size - bytes_read) to_read = size - bytes_read;

        uint8_t block_buf[1024];
        ext2_read_block(fs, block, block_buf);
        memcpy(buf + bytes_read, block_buf + block_off, to_read);
        bytes_read += to_read;
    }
    return (int)bytes_read;
}

int ext2_write_file(ext2_fs_t* fs, uint32_t ino, uint32_t offset, uint32_t size, const uint8_t* buf) {
    ext2_inode_t inode;
    if (ext2_read_inode(fs, ino, &inode) != 0) return -1;

    uint32_t bytes_written = 0;
    while (bytes_written < size) {
        uint32_t block_idx = (offset + bytes_written) / fs->block_size;
        uint32_t block_off = (offset + bytes_written) % fs->block_size;

        /* Allocate block if needed */
        if (inode.i_block[block_idx] == 0) {
            uint32_t new_block = ext2_alloc_block(fs);
            if (new_block == 0) break;
            inode.i_block[block_idx] = new_block;
            inode.i_blocks += fs->block_size / 512;
        }

        uint32_t to_write = fs->block_size - block_off;
        if (to_write > size - bytes_written) to_write = size - bytes_written;

        uint8_t block_buf[1024];
        if (block_off > 0 || to_write < fs->block_size)
            ext2_read_block(fs, inode.i_block[block_idx], block_buf);

        memcpy(block_buf + block_off, buf + bytes_written, to_write);
        ext2_write_block(fs, inode.i_block[block_idx], block_buf);
        bytes_written += to_write;
    }

    if (offset + bytes_written > inode.i_size)
        inode.i_size = offset + bytes_written;

    ext2_write_inode(fs, ino, &inode);
    fs->dirty = 1;
    return (int)bytes_written;
}

int ext2_mkdir(ext2_fs_t* fs, uint32_t dir_ino, const char* name) {
    uint32_t ino = ext2_alloc_inode(fs);
    if (ino == 0) return -1;

    ext2_inode_t inode;
    memset(&inode, 0, sizeof(ext2_inode_t));
    inode.i_mode = EXT2_S_IFDIR | 0755;
    inode.i_links_count = 2; /* . and .. */
    inode.i_size = fs->block_size;
    inode.i_blocks = fs->block_size / 512;

    uint32_t block = ext2_alloc_block(fs);
    inode.i_block[0] = block;

    /* Create . and .. entries */
    uint8_t block_buf[1024];
    memset(block_buf, 0, fs->block_size);

    ext2_dirent_t* dot = (ext2_dirent_t*)block_buf;
    dot->inode = ino;
    dot->rec_len = 12;
    dot->name_len = 1;
    dot->file_type = EXT2_FT_DIR;
    dot->name[0] = '.';

    ext2_dirent_t* dotdot = (ext2_dirent_t*)(block_buf + 12);
    dotdot->inode = dir_ino;
    dotdot->rec_len = fs->block_size - 12;
    dotdot->name_len = 2;
    dotdot->file_type = EXT2_FT_DIR;
    dotdot->name[0] = '.';
    dotdot->name[1] = '.';

    ext2_write_block(fs, block, block_buf);
    ext2_write_inode(fs, ino, &inode);

    /* Add entry to parent */
    ext2_create_file(fs, dir_ino, name, EXT2_S_IFDIR);
    fs->dirty = 1;
    return 0;
}

int ext2_readdir(ext2_fs_t* fs, uint32_t dir_ino, ext2_dirent_t* out, uint32_t max) {
    ext2_inode_t dir;
    if (ext2_read_inode(fs, dir_ino, &dir) != 0) return -1;

    uint8_t buf[4096];
    uint32_t offset = 0;
    uint32_t count = 0;
    uint32_t size = dir.i_size;

    while (offset < size && count < max) {
        uint32_t block = ext2_block_from_offset(fs, &dir, offset);
        if (block == 0) break;
        ext2_read_block(fs, block, buf);

        uint32_t boff = 0;
        while (boff < fs->block_size && count < max) {
            ext2_dirent_t* entry = (ext2_dirent_t*)(buf + boff);
            if (entry->rec_len == 0) break;
            if (entry->inode != 0) {
                memcpy(&out[count], entry, sizeof(ext2_dirent_t) + entry->name_len);
                count++;
            }
            boff += entry->rec_len;
        }
        offset += fs->block_size;
    }
    return (int)count;
}

int ext2_format(ext2_fs_t* fs) {
    if (!fs) return -1;

    /* Initialize superblock */
    memset(&fs->super, 0, sizeof(ext2_superblock_t));
    fs->super.s_magic = 0xEF53;
    fs->super.s_inodes_count = 1024;
    fs->super.s_blocks_count = 8192;
    fs->super.s_free_inodes_count = 1000;
    fs->super.s_free_blocks_count = 7000;
    fs->super.s_first_data_block = 1;
    fs->super.s_log_block_size = 0;
    fs->super.s_blocks_per_group = 8192;
    fs->super.s_inodes_per_group = 128;
    fs->super.s_first_ino = 11;
    fs->super.s_inode_size = EXT2_INODE_SIZE;
    fs->super.s_state = 1; /* clean */

    fs->num_groups = 1;
    fs->block_size = EXT2_BLOCK_SIZE;

    /* Create root inode */
    uint32_t root_ino = ext2_alloc_inode(fs);
    ext2_inode_t root;
    memset(&root, 0, sizeof(ext2_inode_t));
    root.i_mode = EXT2_S_IFDIR | 0755;
    root.i_links_count = 2;
    root.i_size = EXT2_BLOCK_SIZE;
    root.i_blocks = 2;

    uint32_t root_block = ext2_alloc_block(fs);
    root.i_block[0] = root_block;
    ext2_write_inode(fs, root_ino, &root);

    /* Create . and .. in root */
    uint8_t block_buf[1024];
    memset(block_buf, 0, EXT2_BLOCK_SIZE);
    ext2_dirent_t* dot = (ext2_dirent_t*)block_buf;
    dot->inode = root_ino;
    dot->rec_len = 12;
    dot->name_len = 1;
    dot->file_type = EXT2_FT_DIR;
    dot->name[0] = '.';
    ext2_dirent_t* dotdot = (ext2_dirent_t*)(block_buf + 12);
    dotdot->inode = root_ino;
    dotdot->rec_len = EXT2_BLOCK_SIZE - 12;
    dotdot->name_len = 2;
    dotdot->file_type = EXT2_FT_DIR;
    dotdot->name[0] = '.';
    dotdot->name[1] = '.';
    ext2_write_block(fs, root_block, block_buf);

    fs->dirty = 1;
    return 0;
}
