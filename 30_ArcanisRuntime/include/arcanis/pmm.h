#ifndef ARCANIS_PMM_H
#define ARCANIS_PMM_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#define PMM_BLOCK_SIZE 4096
#define PMM_BITMAP_ALIGN 4

void arc_pmm_init(uint32_t total_memory, uint32_t kernel_start, uint32_t kernel_end);
void* arc_pmm_alloc_block(void);
void* arc_pmm_alloc_blocks(size_t count);
void arc_pmm_free_block(void* block);
void arc_pmm_free_blocks(void* base, size_t count);
uint32_t arc_pmm_get_free_blocks(void);
uint32_t arc_pmm_get_total_blocks(void);
bool arc_pmm_is_block_used(uint32_t block_num);

#endif
