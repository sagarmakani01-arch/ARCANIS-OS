#ifndef ARCANIS_RUNTIME_H
#define ARCANIS_RUNTIME_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#define ARCANIS_VERSION_MAJOR 0
#define ARCANIS_VERSION_MINOR 1
#define ARCANIS_VERSION_PATCH 0

#define ARCANIS_BLOCK_SIZE 4096
#define ARCANIS_PAGE_SIZE 4096
#define ARCANIS_MAX_MEMORY (1ULL << 32)

#define ARCANIS_OK 0
#define ARCANIS_ERR_NOMEM -1
#define ARCANIS_ERR_INVAL -2
#define ARCANIS_ERR_ALIGN -3
#define ARCANIS_ERR_RANGE -4

typedef int32_t arc_status_t;

typedef struct {
    uint32_t total_memory;
    uint32_t free_blocks;
    uint32_t used_blocks;
    uint32_t total_blocks;
    void* heap_start;
    size_t heap_size;
    bool initialized;
} arc_runtime_info_t;

arc_status_t arc_runtime_init(uint32_t mem_map_base, uint32_t mem_map_size);
arc_status_t arc_runtime_shutdown(void);
const arc_runtime_info_t* arc_runtime_get_info(void);

void* arc_aligned_alloc(size_t size, size_t alignment);
void* arc_calloc(size_t count, size_t size);
void* arc_realloc(void* ptr, size_t new_size);
void arc_free(void* ptr);
size_t arc_get_used_memory(void);
size_t arc_get_free_memory(void);

#endif
