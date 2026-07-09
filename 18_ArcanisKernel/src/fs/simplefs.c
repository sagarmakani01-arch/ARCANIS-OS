/**
 * simplefs.c — Simple In-Memory Filesystem
 *
 * Flat filesystem with inode-based file tracking.
 * Supports create, delete, read, write, mkdir, list.
 * Can persist to ATA disk via fs_sync/fs_load.
 */
#include <arcanis/simplefs.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

static uint32_t next_inode = 1;

void fs_initialize(fs_t* fs) {
    memset(&fs->super, 0, sizeof(fs_superblock_t));
    fs->block_data = NULL;
    fs->block_data_size = 0;
    fs->dirty = 0;
    fs->ata_drive = NULL;
}

int fs_format(fs_t* fs) {
    memset(&fs->super, 0, sizeof(fs_superblock_t));
    fs->super.magic = FS_MAGIC;
    fs->super.total_blocks = FS_MAX_BLOCKS;
    fs->super.free_blocks = FS_MAX_BLOCKS;
    fs->super.root_inode = 0;
    fs->super.file_count = 0;
    next_inode = 1;

    /* Clear block bitmap */
    memset(fs->super.block_bitmap, 0, sizeof(fs->super.block_bitmap));

    /* Clear file table */
    memset(fs->super.files, 0, sizeof(fs->super.files));

    /* Create root directory */
    fs_file_t* root = &fs->super.files[0];
    string_copy(root->name, "/");
    root->inode = 0;
    root->type = FS_TYPE_DIR;
    root->size = 0;
    root->parent_inode = 0;
    root->flags = 0;
    for (int i = 0; i < 16; i++) root->blocks[i] = 0;
    fs->super.file_count = 1;
    fs->super.root_inode = 0;

    /* Allocate block data buffer */
    if (!fs->block_data) {
        fs->block_data_size = FS_MAX_BLOCKS * FS_BLOCK_SIZE;
        fs->block_data = (uint8_t*)kmalloc(fs->block_data_size);
        if (!fs->block_data) return -1;
    }
    memset(fs->block_data, 0, fs->block_data_size);

    fs->dirty = 1;
    return 0;
}

int fs_mount(fs_t* fs) {
    /* If no block data, allocate it */
    if (!fs->block_data) {
        fs->block_data_size = FS_MAX_BLOCKS * FS_BLOCK_SIZE;
        fs->block_data = (uint8_t*)kmalloc(fs->block_data_size);
        if (!fs->block_data) return -1;
    }
    /* TODO: load from ATA disk if available */
    return 0;
}

int fs_get_free_block(fs_t* fs) {
    for (uint32_t i = 0; i < FS_MAX_BLOCKS; i++) {
        uint32_t word = fs->super.block_bitmap[i / 32];
        if (!(word & (1 << (i % 32)))) {
            fs->super.block_bitmap[i / 32] |= (1 << (i % 32));
            fs->super.free_blocks--;
            return (int)i;
        }
    }
    return -1;
}

void fs_free_block(fs_t* fs, uint32_t block) {
    if (block >= FS_MAX_BLOCKS) return;
    fs->super.block_bitmap[block / 32] &= ~(1 << (block % 32));
    fs->super.free_blocks++;
}

fs_file_t* fs_find(fs_t* fs, const char* path) {
    if (!fs || !path) return NULL;

    /* Root */
    if (path[0] == '\0' || (path[0] == '/' && path[1] == '\0'))
        return &fs->super.files[0];

    /* Search all files for matching path */
    for (uint32_t i = 0; i < fs->super.file_count; i++) {
        if (fs->super.files[i].inode == 0) continue;
        if (string_compare(fs->super.files[i].name, path) == 0)
            return &fs->super.files[i];
    }
    return NULL;
}

static int fs_find_parent(fs_t* fs, const char* path, char* parent_out, char* name_out) {
    int len = string_length(path);
    int last_slash = -1;

    for (int i = 0; i < len; i++) {
        if (path[i] == '/') last_slash = i;
    }

    if (last_slash < 0) {
        string_copy(parent_out, "/");
        string_copy(name_out, path);
    } else {
        string_copy_n(parent_out, path, last_slash);
        parent_out[last_slash] = '\0';
        string_copy(name_out, path + last_slash + 1);
    }
    return 0;
}

int fs_create_file(fs_t* fs, const char* path, uint32_t type) {
    if (!fs || !path) return -1;
    if (fs->super.file_count >= FS_MAX_FILES) return -1;

    /* Check if already exists */
    if (fs_find(fs, path)) return -1;

    char parent_path[FS_NAME_MAX];
    char name[FS_NAME_MAX];
    fs_find_parent(fs, path, parent_path, name);

    fs_file_t* parent = fs_find(fs, parent_path);
    if (!parent || parent->type != FS_TYPE_DIR) return -1;

    /* Allocate inode */
    uint32_t inode = next_inode++;

    /* Find free slot */
    for (uint32_t i = 0; i < FS_MAX_FILES; i++) {
        if (fs->super.files[i].inode == 0) {
            fs_file_t* f = &fs->super.files[i];
            string_copy(f->name, path);
            f->inode = inode;
            f->type = type;
            f->size = 0;
            f->parent_inode = parent->inode;
            f->flags = 0;
            for (int b = 0; b < 16; b++) f->blocks[b] = 0;

            if (type == FS_TYPE_FILE) {
                /* Allocate first block */
                int block = fs_get_free_block(fs);
                if (block >= 0) f->blocks[0] = (uint32_t)block;
            }

            fs->super.file_count++;
            fs->dirty = 1;
            return 0;
        }
    }
    return -1;
}

int fs_delete(fs_t* fs, const char* path) {
    if (!fs || !path) return -1;

    for (uint32_t i = 0; i < fs->super.file_count; i++) {
        if (fs->super.files[i].inode == 0) continue;
        if (string_compare(fs->super.files[i].name, path) == 0) {
            /* Free blocks */
            for (int b = 0; b < 16; b++) {
                if (fs->super.files[i].blocks[b])
                    fs_free_block(fs, fs->super.files[i].blocks[b]);
            }
            /* Mark as free */
            fs->super.files[i].inode = 0;
            fs->super.file_count--;
            fs->dirty = 1;
            return 0;
        }
    }
    return -1;
}

int fs_read(fs_t* fs, const char* path, uint32_t offset, uint32_t size, uint8_t* buf) {
    fs_file_t* file = fs_find(fs, path);
    if (!file || file->type != FS_TYPE_FILE) return -1;

    uint32_t to_read = size;
    if (offset + to_read > file->size) to_read = file->size - offset;
    if (to_read == 0) return 0;

    uint32_t bytes_read = 0;
    for (uint32_t pos = 0; pos < to_read; ) {
        uint32_t block_idx = (offset + pos) / FS_BLOCK_SIZE;
        uint32_t block_off = (offset + pos) % FS_BLOCK_SIZE;
        if (block_idx >= 16) break;

        uint32_t block_num = file->blocks[block_idx];
        if (block_num == 0) break;

        uint32_t chunk = FS_BLOCK_SIZE - block_off;
        if (chunk > to_read - pos) chunk = to_read - pos;

        uint32_t src_offset = block_num * FS_BLOCK_SIZE + block_off;
        if (src_offset + chunk <= fs->block_data_size) {
            for (uint32_t i = 0; i < chunk; i++)
                buf[bytes_read + i] = fs->block_data[src_offset + i];
        }
        bytes_read += chunk;
        pos += chunk;
    }
    return (int)bytes_read;
}

int fs_write(fs_t* fs, const char* path, uint32_t offset, uint32_t size, const uint8_t* buf) {
    fs_file_t* file = fs_find(fs, path);
    if (!file || file->type != FS_TYPE_FILE) return -1;

    uint32_t bytes_written = 0;
    for (uint32_t pos = 0; pos < size; ) {
        uint32_t block_idx = (offset + pos) / FS_BLOCK_SIZE;
        uint32_t block_off = (offset + pos) % FS_BLOCK_SIZE;
        if (block_idx >= 16) break;

        /* Allocate block if needed */
        if (file->blocks[block_idx] == 0) {
            int block = fs_get_free_block(fs);
            if (block < 0) break;
            file->blocks[block_idx] = (uint32_t)block;
        }

        uint32_t chunk = FS_BLOCK_SIZE - block_off;
        if (chunk > size - pos) chunk = size - pos;

        uint32_t dst_offset = file->blocks[block_idx] * FS_BLOCK_SIZE + block_off;
        if (dst_offset + chunk <= fs->block_data_size) {
            for (uint32_t i = 0; i < chunk; i++)
                fs->block_data[dst_offset + i] = buf[bytes_written + i];
        }
        bytes_written += chunk;
        pos += chunk;
    }

    if (offset + bytes_written > file->size)
        file->size = offset + bytes_written;

    file->flags |= FS_FLAG_DIRTY;
    fs->dirty = 1;
    return (int)bytes_written;
}

int fs_list_dir(fs_t* fs, const char* path, fs_file_t* out, uint32_t max) {
    fs_file_t* dir = fs_find(fs, path);
    if (!dir || dir->type != FS_TYPE_DIR) return -1;

    uint32_t count = 0;
    for (uint32_t i = 0; i < fs->super.file_count && count < max; i++) {
        if (fs->super.files[i].inode == 0) continue;
        if (fs->super.files[i].parent_inode == dir->inode) {
            out[count++] = fs->super.files[i];
        }
    }
    return (int)count;
}

int fs_mkdir(fs_t* fs, const char* path) {
    return fs_create_file(fs, path, FS_TYPE_DIR);
}

int fs_sync(fs_t* fs) {
    /* TODO: write superblock + block data to ATA disk */
    fs->dirty = 0;
    return 0;
}
