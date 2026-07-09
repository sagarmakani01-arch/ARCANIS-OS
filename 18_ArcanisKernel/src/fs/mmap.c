/**
 * mmap.c — Memory-Mapped File Implementation
 *
 * Maps files into process address space using page-aligned regions.
 */
#include <arcanis/mmap.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <arcanis/vmm.h>
#include <arcanis/fd.h>

void mmap_init(mmap_state_t* state) {
    if (!state) return;
    memset(state, 0, sizeof(mmap_state_t));
}

void* mmap_anonymous(mmap_state_t* state, uint32_t length, int prot, int flags) {
    if (!state || length == 0) return NULL;

    /* Align length to page size */
    uint32_t aligned_len = (length + MMAP_PAGE_SIZE - 1) & ~(MMAP_PAGE_SIZE - 1);

    /* Find free slot */
    for (uint32_t i = 0; i < MMAP_MAX_MAPPINGS; i++) {
        if (!state->regions[i].active) {
            mmap_region_t* r = &state->regions[i];

            /* Allocate backing memory */
            r->backing = (uint8_t*)kmalloc(aligned_len);
            if (!r->backing) return NULL;
            memset(r->backing, 0, aligned_len);

            r->addr = r->backing;
            r->offset = 0;
            r->length = aligned_len;
            r->file_size = 0;
            r->prot = prot;
            r->flags = flags | MAP_ANONYMOUS;
            r->fd = -1;
            r->dirty = 0;
            r->active = 1;

            state->num_regions++;
            state->total_mapped += aligned_len;

            return r->addr;
        }
    }
    return NULL;
}

void* mmap_map(mmap_state_t* state, int fd, uint32_t offset, uint32_t length,
               int prot, int flags, void* addr_hint) {
    if (!state || length == 0) return NULL;

    /* Align to page boundaries */
    uint32_t page_offset = offset & (MMAP_PAGE_SIZE - 1);
    uint32_t aligned_offset = offset & ~(MMAP_PAGE_SIZE - 1);
    uint32_t aligned_len = (length + page_offset + MMAP_PAGE_SIZE - 1) & ~(MMAP_PAGE_SIZE - 1);

    /* Find free slot */
    for (uint32_t i = 0; i < MMAP_MAX_MAPPINGS; i++) {
        if (!state->regions[i].active) {
            mmap_region_t* r = &state->regions[i];

            /* Read file data */
            r->backing = (uint8_t*)kmalloc(aligned_len);
            if (!r->backing) return NULL;

            if (fd >= 0) {
                /* Read from file */
                uint32_t bytes_read = (uint32_t)fd_read(fd, r->backing, aligned_len);
                if (bytes_read < aligned_len)
                    memset(r->backing + bytes_read, 0, aligned_len - bytes_read);
            } else {
                memset(r->backing, 0, aligned_len);
            }

            r->addr = addr_hint ? addr_hint : r->backing;
            r->offset = aligned_offset;
            r->length = aligned_len;
            r->file_size = aligned_len;
            r->prot = prot;
            r->flags = flags;
            r->fd = fd;
            r->dirty = 0;
            r->active = 1;

            state->num_regions++;
            state->total_mapped += aligned_len;

            return r->addr;
        }
    }
    return NULL;
}

int mmap_unmap(mmap_state_t* state, void* addr) {
    if (!state || !addr) return -1;

    for (uint32_t i = 0; i < MMAP_MAX_MAPPINGS; i++) {
        mmap_region_t* r = &state->regions[i];
        if (r->active && r->addr == addr) {
            /* Sync if dirty */
            if (r->dirty && r->fd >= 0 && (r->flags & MAP_SHARED)) {
                fd_write(r->fd, r->backing, r->length);
            }

            kfree(r->backing);
            memset(r, 0, sizeof(mmap_region_t));
            state->num_regions--;
            state->total_mapped -= r->length;
            return 0;
        }
    }
    return -1;
}

int mmap_sync(mmap_state_t* state, void* addr, uint32_t length) {
    if (!state || !addr) return -1;

    for (uint32_t i = 0; i < MMAP_MAX_MAPPINGS; i++) {
        mmap_region_t* r = &state->regions[i];
        if (r->active && r->addr == addr) {
            if (r->fd >= 0 && (r->flags & MAP_SHARED)) {
                uint32_t sync_len = length;
                if (sync_len > r->length) sync_len = r->length;
                fd_write(r->fd, r->backing, sync_len);
                r->dirty = 0;
                return 0;
            }
            return 0;
        }
    }
    return -1;
}

int mmap_protect(mmap_state_t* state, void* addr, uint32_t length, int prot) {
    if (!state || !addr) return -1;

    for (uint32_t i = 0; i < MMAP_MAX_MAPPINGS; i++) {
        mmap_region_t* r = &state->regions[i];
        if (r->active && r->addr == addr) {
            r->prot = prot;
            return 0;
        }
    }
    return -1;
}

void* mmap_remap(mmap_state_t* state, void* old_addr, uint32_t old_length,
                 uint32_t new_length, int flags, void* new_addr) {
    if (!state || !old_addr) return NULL;

    for (uint32_t i = 0; i < MMAP_MAX_MAPPINGS; i++) {
        mmap_region_t* r = &state->regions[i];
        if (r->active && r->addr == old_addr) {
            uint32_t aligned_len = (new_length + MMAP_PAGE_SIZE - 1) & ~(MMAP_PAGE_SIZE - 1);

            /* Reallocate backing store */
            uint8_t* new_backing = (uint8_t*)krealloc(r->backing, aligned_len);
            if (!new_backing) return NULL;

            /* Zero new pages if expanded */
            if (aligned_len > r->length)
                memset(new_backing + r->length, 0, aligned_len - r->length);

            r->backing = new_backing;
            r->addr = new_addr ? new_addr : r->addr;
            r->length = aligned_len;
            state->total_mapped += (aligned_len - r->length);

            return r->addr;
        }
    }
    return NULL;
}

mmap_region_t* mmap_find(mmap_state_t* state, void* addr) {
    if (!state || !addr) return NULL;

    for (uint32_t i = 0; i < MMAP_MAX_MAPPINGS; i++) {
        mmap_region_t* r = &state->regions[i];
        if (r->active && (uint32_t)r->addr <= (uint32_t)addr &&
            (uint32_t)addr < (uint32_t)r->addr + r->length) {
            return r;
        }
    }
    return NULL;
}

int mmap_update_pte(mmap_state_t* state, mmap_region_t* region) {
    if (!state || !region) return -1;

    /* Update page table entries for this region */
    uint32_t num_pages = (region->length + MMAP_PAGE_SIZE - 1) / MMAP_PAGE_SIZE;

    for (uint32_t i = 0; i < num_pages; i++) {
        void* vaddr = (void*)((uint32_t)region->addr + i * MMAP_PAGE_SIZE);
        void* paddr = (void*)((uint32_t)region->backing + i * MMAP_PAGE_SIZE);

        uint32_t flags = 0;
        if (region->prot & PROT_READ)  flags |= VMM_FLAG_PRESENT;
        if (region->prot & PROT_WRITE) flags |= VMM_FLAG_WRITABLE;
        if (region->prot & PROT_EXEC)  flags |= VMM_FLAG_USER;

        vmm_map_page((uint32_t)vaddr, (uint32_t)paddr, flags);
    }

    return 0;
}
