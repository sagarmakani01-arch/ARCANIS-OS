#ifndef ARCANIS_PMM_H
#define ARCANIS_PMM_H

#include <arcanis/types.h>

#define PMM_BLOCK_SIZE  4096
#define PMM_BLOCKS_PER_BYTE 8

void pmm_initialize(uint32_t total_memory);
void* pmm_alloc_block(void);
void  pmm_free_block(void* block);
void* pmm_alloc_blocks(size_t count);
void  pmm_free_blocks(void* base, size_t count);
uint32_t pmm_get_free_blocks(void);
uint32_t pmm_get_total_blocks(void);

#endif
