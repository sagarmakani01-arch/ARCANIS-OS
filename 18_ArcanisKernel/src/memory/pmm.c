#include <arcanis/pmm.h>
#include <arcanis/types.h>
#include <arcanis/string.h>
#include <arcanis/defs.h>

static uint32_t* pmm_bitmap = NULL;
static uint32_t  pmm_total_blocks = 0;
static uint32_t  pmm_used_blocks = 0;
static uint32_t  pmm_bitmap_size = 0;

extern uint32_t __kernel_start;
extern uint32_t __kernel_end;

static void pmm_set_block(uint32_t block) {
    pmm_bitmap[block / 32] |= (1 << (block % 32));
}

static void pmm_clear_block(uint32_t block) {
    pmm_bitmap[block / 32] &= ~(1 << (block % 32));
}

static bool pmm_test_block(uint32_t block) {
    return pmm_bitmap[block / 32] & (1 << (block % 32));
}

static int32_t pmm_find_free_block(void) {
    for (uint32_t i = 0; i < pmm_bitmap_size / 4; i++) {
        if (pmm_bitmap[i] != 0xFFFFFFFF) {
            for (uint32_t j = 0; j < 32; j++) {
                if (!(pmm_bitmap[i] & (1 << j))) {
                    return i * 32 + j;
                }
            }
        }
    }
    return -1;
}

void pmm_initialize(uint32_t total_memory) {
    pmm_total_blocks = total_memory / PMM_BLOCK_SIZE;
    pmm_bitmap_size = (pmm_total_blocks / 32) + 1;
    pmm_used_blocks = pmm_total_blocks;

    pmm_bitmap = (uint32_t*)&__kernel_end;
    memset(pmm_bitmap, 0xFF, pmm_bitmap_size);

    uint32_t kernel_start = (uint32_t)&__kernel_start;
    uint32_t kernel_end = (uint32_t)&__kernel_end + pmm_bitmap_size;

    for (uint32_t i = 0; i < pmm_total_blocks; i++) {
        uint32_t addr = i * PMM_BLOCK_SIZE;
        if (addr >= kernel_start && addr < kernel_end + PMM_BLOCK_SIZE) {
            continue;
        }
        pmm_clear_block(i);
        pmm_used_blocks--;
    }

    pmm_used_blocks = pmm_total_blocks - pmm_used_blocks;
}

void* pmm_alloc_block(void) {
    int32_t block = pmm_find_free_block();
    if (block == -1) return NULL;

    pmm_set_block(block);
    pmm_used_blocks++;
    return (void*)(block * PMM_BLOCK_SIZE);
}

void pmm_free_block(void* block) {
    uint32_t addr = (uint32_t)block;
    uint32_t block_num = addr / PMM_BLOCK_SIZE;

    if (pmm_test_block(block_num)) {
        pmm_clear_block(block_num);
        pmm_used_blocks--;
    }
}

void* pmm_alloc_blocks(size_t count) {
    void* first = NULL;
    size_t found = 0;

    for (uint32_t i = 0; i < pmm_total_blocks; i++) {
        if (!pmm_test_block(i)) {
            if (found == 0) first = (void*)(i * PMM_BLOCK_SIZE);
            found++;
            if (found == count) {
                for (size_t j = 0; j < count; j++) {
                    pmm_set_block(i - count + 1 + j);
                }
                pmm_used_blocks += count;
                return first;
            }
        } else {
            found = 0;
        }
    }
    return NULL;
}

void pmm_free_blocks(void* base, size_t count) {
    uint32_t start = (uint32_t)base / PMM_BLOCK_SIZE;
    for (size_t i = 0; i < count; i++) {
        if (pmm_test_block(start + i)) {
            pmm_clear_block(start + i);
            pmm_used_blocks--;
        }
    }
}

uint32_t pmm_get_free_blocks(void) {
    return pmm_total_blocks - pmm_used_blocks;
}

uint32_t pmm_get_total_blocks(void) {
    return pmm_total_blocks;
}
