/**
 * tar.c — TAR Archive Implementation
 *
 * Create and extract ustar format tar archives.
 */
#include <arcanis/tar.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <arcanis/stdio.h>

void tar_init(tar_archive_t* tar) {
    if (!tar) return;
    memset(tar, 0, sizeof(tar_archive_t));
}

/* ---- Header helpers ---- */

void tar_init_header(tar_header_t* header) {
    if (!header) return;
    memset(header, 0, sizeof(tar_header_t));
    string_copy(header->magic, "ustar", 6);
    header->version[0] = '0';
    header->version[1] = '0';
    string_copy(header->uname, "root", TAR_MAX_UNAME);
    string_copy(header->gname, "root", TAR_MAX_GNAME);
}

void tar_set_octal(char* field, uint32_t value, uint32_t len) {
    if (!field) return;
    char octal[32];
    int pos = 0;

    if (value == 0) {
        octal[pos++] = '0';
    } else {
        while (value > 0 && pos < 31) {
            octal[pos++] = '0' + (value & 7);
            value >>= 3;
        }
    }

    /* Reverse */
    for (uint32_t i = 0; i < pos / 2; i++) {
        char tmp = octal[i];
        octal[i] = octal[pos - 1 - i];
        octal[pos - 1 - i] = tmp;
    }

    /* Pad with leading zeros */
    uint32_t pad = len - 1 - pos;
    for (uint32_t i = 0; i < pad; i++) field[i] = '0';
    for (uint32_t i = 0; i < pos; i++) field[pad + i] = octal[i];
    field[len - 1] = '\0';
}

uint32_t tar_get_octal(const char* field, uint32_t len) {
    if (!field) return 0;
    uint32_t result = 0;
    uint32_t i = 0;
    while (i < len && field[i] >= '0' && field[i] <= '7') {
        result = result * 8 + (field[i] - '0');
        i++;
    }
    return result;
}

void tar_set_filename(tar_header_t* header, const char* filename) {
    if (!header || !filename) return;

    uint32_t len = string_length(filename);
    if (len < TAR_MAX_PATH) {
        string_copy(header->name, filename, TAR_MAX_PATH);
        header->prefix[0] = '\0';
    } else {
        /* Split into prefix and name */
        uint32_t split = len - TAR_MAX_NAME;
        while (split > 0 && filename[split] != '/') split--;
        if (split > 0) {
            string_copy(header->prefix, filename, split < 155 ? split : 154);
            string_copy(header->name, filename + split + 1, TAR_MAX_NAME);
        } else {
            string_copy(header->name, filename, TAR_MAX_PATH);
        }
    }
}

int tar_calc_checksum(const tar_header_t* header) {
    if (!header) return 0;

    const uint8_t* data = (const uint8_t*)header;
    uint32_t sum = 0;

    /* Sum all bytes, treating checksum field as spaces */
    for (uint32_t i = 0; i < sizeof(tar_header_t); i++) {
        if (i >= 148 && i < 156) sum += ' '; /* Checksum field */
        else sum += data[i];
    }
    return (int)sum;
}

uint32_t tar_checksum(const uint8_t* data, uint32_t size) {
    uint32_t sum = 0;
    for (uint32_t i = 0; i < size; i++) sum += data[i];
    return sum;
}

void tar_write_header(tar_header_t* header, uint8_t* buf) {
    if (!header || !buf) return;

    /* Calculate and set checksum */
    int chksum = tar_calc_checksum(header);
    tar_set_octal(header->chksum, chksum, 8);

    memcpy(buf, header, sizeof(tar_header_t));
}

int tar_read_header(const uint8_t* buf, tar_header_t* header) {
    if (!buf || !header) return -1;
    memcpy(header, buf, sizeof(tar_header_t));

    /* Verify magic */
    if (string_compare_n(header->magic, "ustar", 5) != 0)
        return -1;

    return 0;
}

/* ---- Create ---- */

int tar_add_file(tar_archive_t* tar, const char* path, const uint8_t* data, uint32_t size) {
    if (!tar || !path) return -1;
    if (tar->num_entries >= 256) return -1;

    tar_entry_t* entry = &tar->entries[tar->num_entries];
    string_copy(entry->path, path, 256);
    entry->type = TAR_FILE_REGULAR;
    entry->size = size;
    entry->mode = 0644;
    entry->mtime = 0;

    if (data && size > 0) {
        entry->data = (uint8_t*)kmalloc(size);
        if (!entry->data) return -1;
        memcpy(entry->data, data, size);
        entry->data_size = size;
    }

    tar->num_entries++;
    return 0;
}

int tar_add_dir(tar_archive_t* tar, const char* path) {
    if (!tar || !path) return -1;
    if (tar->num_entries >= 256) return -1;

    tar_entry_t* entry = &tar->entries[tar->num_entries];
    string_copy(entry->path, path, 256);
    entry->type = TAR_FILE_DIRECTORY;
    entry->size = 0;
    entry->mode = 0755;
    entry->data = NULL;
    entry->data_size = 0;

    tar->num_entries++;
    return 0;
}

int tar_create(tar_archive_t* tar, const char** files, uint32_t num_files) {
    if (!tar || !files) return -1;

    /* Calculate total size */
    uint32_t total = 0;
    for (uint32_t i = 0; i < tar->num_entries; i++) {
        total += sizeof(tar_header_t);
        uint32_t data_size = tar->entries[i].size;
        total += (data_size + TAR_BLOCK_SIZE - 1) & ~(TAR_BLOCK_SIZE - 1);
    }
    total += TAR_BLOCK_SIZE * 2; /* Two zero blocks at end */

    tar->archive_size = total;
    tar->archive = (uint8_t*)kmalloc(total);
    if (!tar->archive) return -1;

    uint32_t offset = 0;
    for (uint32_t i = 0; i < tar->num_entries; i++) {
        tar_entry_t* entry = &tar->entries[i];

        /* Build header */
        tar_header_t header;
        tar_init_header(&header);
        tar_set_filename(&header, entry->path);

        char mode_str[8], uid_str[8], gid_str[8], size_str[12], mtime_str[12];
        tar_set_octal(mode_str, entry->mode, 8);
        tar_set_octal(uid_str, entry->uid, 8);
        tar_set_octal(gid_str, entry->gid, 8);
        tar_set_octal(size_str, entry->size, 12);
        tar_set_octal(mtime_str, entry->mtime, 12);

        memcpy(header.mode, mode_str, 8);
        memcpy(header.uid, uid_str, 8);
        memcpy(header.gid, gid_str, 8);
        memcpy(header.size, size_str, 12);
        memcpy(header.mtime, mtime_str, 12);
        header.typeflag = entry->type;

        /* Write header */
        tar_write_header(&header, tar->archive + offset);
        offset += sizeof(tar_header_t);

        /* Write data */
        if (entry->data && entry->size > 0) {
            memcpy(tar->archive + offset, entry->data, entry->size);
            uint32_t padded = (entry->size + TAR_BLOCK_SIZE - 1) & ~(TAR_BLOCK_SIZE - 1);
            offset += padded;
        }
    }

    /* Write two zero blocks */
    memset(tar->archive + offset, 0, TAR_BLOCK_SIZE * 2);

    return 0;
}

/* ---- Extract ---- */

int tar_extract_entry(tar_archive_t* tar, const tar_entry_t* entry, const char* dest) {
    if (!tar || !entry) return -1;
    /* In real implementation: create file/dir and write data */
    return 0;
}

int tar_extract(tar_archive_t* tar, const uint8_t* data, uint32_t size) {
    if (!tar || !data || size < TAR_BLOCK_SIZE) return -1;

    tar->num_entries = 0;
    uint32_t offset = 0;

    while (offset + sizeof(tar_header_t) <= size) {
        tar_header_t header;
        if (tar_read_header(data + offset, &header) != 0) break;

        /* Check for end-of-archive */
        if (header.name[0] == '\0') break;

        tar_entry_t* entry = &tar->entries[tar->num_entries];
        string_copy(entry->path, header.name, 256);
        entry->type = header.typeflag;
        entry->size = tar_get_octal(header.size, 12);
        entry->mode = tar_get_octal(header.mode, 8);
        entry->mtime = tar_get_octal(header.mtime, 12);

        offset += sizeof(tar_header_t);

        if (entry->size > 0 && entry->type == TAR_FILE_REGULAR) {
            entry->data = (uint8_t*)kmalloc(entry->size);
            if (entry->data) {
                memcpy(entry->data, data + offset, entry->size);
                entry->data_size = entry->size;
            }
            uint32_t padded = (entry->size + TAR_BLOCK_SIZE - 1) & ~(TAR_BLOCK_SIZE - 1);
            offset += padded;
        }

        tar->num_entries++;
    }

    return 0;
}

int tar_list(tar_archive_t* tar, const uint8_t* data, uint32_t size) {
    /* Parse and list entries */
    tar_archive_t tmp;
    tar_init(&tmp);
    tar_extract(&tmp, data, size);

    for (uint32_t i = 0; i < tmp.num_entries; i++) {
        /* printf("%c %s\n", tmp.entries[i].type, tmp.entries[i].path); */
    }

    /* Free temp data */
    for (uint32_t i = 0; i < tmp.num_entries; i++)
        if (tmp.entries[i].data) kfree(tmp.entries[i].data);

    return 0;
}
