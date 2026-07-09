#include "utils/driver_memory.h"
#include <string.h>

void memory_init(MemoryManager* mgr) {
    if (!mgr) return;
    memset(mgr, 0, sizeof(MemoryManager));
}

DriverStatus memory_pool_create(MemoryManager* mgr, void* base, size_t size, size_t block_size) {
    if (!mgr || !base || size == 0 || block_size == 0) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (mgr->pool_count >= POOL_MAX_POOLS) {
        return DRIVER_STATUS_NO_MEMORY;
    }

    MemoryPool* pool = &mgr->pools[mgr->pool_count];
    pool->base = base;
    pool->total_size = size;
    pool->free_size = size;
    pool->block_size = block_size;
    pool->block_count = 0;
    pool->initialized = true;

    uint32_t max_blocks = size / block_size;
    if (max_blocks > POOL_MAX_BLOCKS) {
        max_blocks = POOL_MAX_BLOCKS;
    }

    for (uint32_t i = 0; i < max_blocks; i++) {
        pool->blocks[i].address = (uint8_t*)base + (i * block_size);
        pool->blocks[i].size = block_size;
        pool->blocks[i].free = true;
        pool->block_count++;
    }

    mgr->pool_count++;
    return DRIVER_STATUS_OK;
}

DriverStatus memory_pool_destroy(MemoryManager* mgr, uint32_t pool_id) {
    if (!mgr || pool_id >= mgr->pool_count) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    mgr->pools[pool_id].initialized = false;
    memset(&mgr->pools[pool_id], 0, sizeof(MemoryPool));

    return DRIVER_STATUS_OK;
}

void* memory_alloc(MemoryManager* mgr, size_t size) {
    if (!mgr || size == 0) return NULL;

    for (uint32_t p = 0; p < mgr->pool_count; p++) {
        MemoryPool* pool = &mgr->pools[p];
        if (!pool->initialized) continue;

        for (uint32_t i = 0; i < pool->block_count; i++) {
            if (pool->blocks[i].free && pool->blocks[i].size >= size) {
                pool->blocks[i].free = false;
                pool->free_size -= pool->blocks[i].size;
                return pool->blocks[i].address;
            }
        }
    }

    return NULL;
}

void memory_free(MemoryManager* mgr, void* ptr) {
    if (!mgr || !ptr) return;

    for (uint32_t p = 0; p < mgr->pool_count; p++) {
        MemoryPool* pool = &mgr->pools[p];
        if (!pool->initialized) continue;

        for (uint32_t i = 0; i < pool->block_count; i++) {
            if (pool->blocks[i].address == ptr && !pool->blocks[i].free) {
                pool->blocks[i].free = true;
                pool->free_size += pool->blocks[i].size;
                return;
            }
        }
    }
}

void* memory_alloc_aligned(MemoryManager* mgr, size_t size, size_t alignment) {
    if (!mgr || size == 0 || alignment == 0 || (alignment & (alignment - 1)) != 0) {
        return NULL;
    }

    for (uint32_t p = 0; p < mgr->pool_count; p++) {
        MemoryPool* pool = &mgr->pools[p];
        if (!pool->initialized) continue;

        for (uint32_t i = 0; i < pool->block_count; i++) {
            if (pool->blocks[i].free && pool->blocks[i].size >= size) {
                uintptr_t addr = (uintptr_t)pool->blocks[i].address;
                uintptr_t aligned_addr = (addr + alignment - 1) & ~(alignment - 1);
                size_t extra = aligned_addr - addr;

                if (pool->blocks[i].size >= size + extra) {
                    pool->blocks[i].free = false;
                    pool->free_size -= pool->blocks[i].size;
                    return (void*)aligned_addr;
                }
            }
        }
    }

    return NULL;
}

size_t memory_get_free(MemoryManager* mgr) {
    if (!mgr) return 0;

    size_t total_free = 0;
    for (uint32_t p = 0; p < mgr->pool_count; p++) {
        if (mgr->pools[p].initialized) {
            total_free += mgr->pools[p].free_size;
        }
    }

    return total_free;
}

size_t memory_get_used(MemoryManager* mgr) {
    if (!mgr) return 0;

    size_t total_used = 0;
    for (uint32_t p = 0; p < mgr->pool_count; p++) {
        if (mgr->pools[p].initialized) {
            total_used += mgr->pools[p].total_size - mgr->pools[p].free_size;
        }
    }

    return total_used;
}
