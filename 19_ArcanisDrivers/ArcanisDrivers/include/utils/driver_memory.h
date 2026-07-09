#ifndef ARCANIS_DRIVER_MEMORY_H
#define ARCANIS_DRIVER_MEMORY_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#define POOL_MAX_POOLS      16
#define POOL_MAX_BLOCKS     1024

typedef struct {
    void* address;
    size_t size;
    bool free;
} MemoryBlock;

typedef struct {
    void* base;
    size_t total_size;
    size_t free_size;
    size_t block_size;
    MemoryBlock blocks[POOL_MAX_BLOCKS];
    uint32_t block_count;
    bool initialized;
} MemoryPool;

typedef struct {
    MemoryPool pools[POOL_MAX_POOLS];
    uint32_t pool_count;
} MemoryManager;

void memory_init(MemoryManager* mgr);
DriverStatus memory_pool_create(MemoryManager* mgr, void* base, size_t size, size_t block_size);
DriverStatus memory_pool_destroy(MemoryManager* mgr, uint32_t pool_id);
void* memory_alloc(MemoryManager* mgr, size_t size);
void memory_free(MemoryManager* mgr, void* ptr);
void* memory_alloc_aligned(MemoryManager* mgr, size_t size, size_t alignment);
size_t memory_get_free(MemoryManager* mgr);
size_t memory_get_used(MemoryManager* mgr);

#endif