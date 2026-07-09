/**
 * mmap.h — Memory-Mapped File I/O
 *
 * Map files into process address space for direct access.
 * Supports read-only, read-write, and private mappings.
 */
#ifndef ARCANIS_MMAP_H
#define ARCANIS_MMAP_H

#include <arcanis/types.h>

#define MMAP_MAX_MAPPINGS  64
#define MMAP_PAGE_SIZE     4096

typedef enum {
    MAP_SHARED  = 0x01,
    MAP_PRIVATE = 0x02,
    MAP_ANONYMOUS = 0x20
} mmap_flags_t;

typedef enum {
    PROT_NONE  = 0,
    PROT_READ  = 1,
    PROT_WRITE = 2,
    PROT_EXEC  = 4
} mmap_prot_t;

typedef struct {
    void*    addr;       /* Mapped address */
    uint32_t offset;     /* File offset */
    uint32_t length;     /* Mapping length */
    uint32_t file_size;  /* Original file size */
    int      prot;       /* Protection flags */
    int      flags;      /* Mapping flags */
    int      fd;         /* File descriptor (-1 if anonymous) */
    int      dirty;      /* Has been modified */
    int      active;     /* Is this mapping in use */
    uint8_t* backing;    /* Backing store (file data or anon pages) */
} mmap_region_t;

typedef struct {
    mmap_region_t regions[MMAP_MAX_MAPPINGS];
    uint32_t      num_regions;
    uint32_t      total_mapped;
} mmap_state_t;

/* Initialize mmap subsystem */
void mmap_init(mmap_state_t* state);

/* Map a file into memory */
void* mmap_map(mmap_state_t* state, int fd, uint32_t offset, uint32_t length,
               int prot, int flags, void* addr_hint);

/* Unmap a region */
int   mmap_unmap(mmap_state_t* state, void* addr);

/* Sync a region to disk */
int   mmap_sync(mmap_state_t* state, void* addr, uint32_t length);

/* Protect a region */
int   mmap_protect(mmap_state_t* state, void* addr, uint32_t length, int prot);

/* Move a region (remap) */
void* mmap_remap(mmap_state_t* state, void* old_addr, uint32_t old_length,
                 uint32_t new_length, int flags, void* new_addr);

/* Create anonymous mapping */
void* mmap_anonymous(mmap_state_t* state, uint32_t length, int prot, int flags);

/* Find mapping by address */
mmap_region_t* mmap_find(mmap_state_t* state, void* addr);

/* Update page table entries */
int mmap_update_pte(mmap_state_t* state, mmap_region_t* region);

#endif
