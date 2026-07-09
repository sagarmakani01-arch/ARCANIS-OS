#include <arcanis/pmm.h>
#include <arcanis/string.h>

static uint32_t* pmm_bitmap = (void*)0;
static uint32_t  pmm_total_blocks = 0;
static uint32_t  pmm_used_blocks = 0;
static uint32_t  pmm_bitmap_size = 0;

static void pmm_set_block(uint32_t block) {
    pmm_bitmap[block / 32] |= (1U << (block % 32));
}

static void pmm_clear_block(uint32_t block) {
    pmm_bitmap[block / 32] &= ~(1U << (block % 32));
}

static int pmm_test_block(uint32_t block) {
    return pmm_bitmap[block / 32] & (1U << (block % 32));
}

static int32_t pmm_find_free_block(void) {
    for (uint32_t i = 0; i < (pmm_bitmap_size + 31) / 32; i++) {
        if (pmm_bitmap[i] != 0xFFFFFFFF) {
            for (uint32_t j = 0; j < 32; j++) {
                if (!(pmm_bitmap[i] & (1U << j))) {
                    return (int32_t)(i * 32 + j);
                }
            }
        }
    }
    return -1;
}

void arc_pmm_init(uint32_t total_memory, uint32_t kernel_start, uint32_t kernel_end) {
    pmm_total_blocks = total_memory / PMM_BLOCK_SIZE;
    pmm_bitmap_size = pmm_total_blocks;
    pmm_used_blocks = pmm_total_blocks;

    uint32_t bitmap_bytes = (pmm_bitmap_size + 7) / 8;
    uint32_t bitmap_end = (kernel_end + PMM_BLOCK_SIZE - 1) & ~(PMM_BLOCK_SIZE - 1);
    pmm_bitmap = (uint32_t*)bitmap_end;

    uint32_t bitmap_end_aligned = bitmap_end + ((bitmap_bytes + 3) & ~3U);
    uint32_t reserved_end = bitmap_end_aligned > kernel_end ? bitmap_end_aligned : kernel_end;

    arc_memset(pmm_bitmap, 0xFF, bitmap_bytes);

    uint32_t kernel_start_block = kernel_start / PMM_BLOCK_SIZE;
    uint32_t kernel_end_block = (reserved_end + PMM_BLOCK_SIZE - 1) / PMM_BLOCK_SIZE;

    for (uint32_t i = 0; i < pmm_total_blocks; i++) {
        uint32_t addr = i * PMM_BLOCK_SIZE;
        if (addr >= kernel_start && i < kernel_end_block) continue;
        if (i < kernel_start_block) continue;
        pmm_clear_block(i);
        pmm_used_blocks--;
    }

    if (pmm_used_blocks > pmm_total_blocks)
        pmm_used_blocks = pmm_total_blocks;
}

void* arc_pmm_alloc_block(void) {
    int32_t block = pmm_find_free_block();
    if (block == -1) return (void*)0;
    pmm_set_block((uint32_t)block);
    pmm_used_blocks++;
    return (void*)((uint32_t)block * PMM_BLOCK_SIZE);
}

void* arc_pmm_alloc_blocks(size_t count) {
    if (count == 0) return (void*)0;
    if (count == 1) return arc_pmm_alloc_block();

    uint32_t found = 0;
    int32_t start = -1;

    for (uint32_t i = 0; i < pmm_total_blocks; i++) {
        if (!pmm_test_block(i)) {
            if (found == 0) start = (int32_t)i;
            found++;
            if (found == count) {
                for (size_t j = 0; j < count; j++) {
                    pmm_set_block((uint32_t)(start + j));
                }
                pmm_used_blocks += count;
                return (void*)((uint32_t)start * PMM_BLOCK_SIZE);
            }
        } else {
            found = 0;
            start = -1;
        }
    }
    return (void*)0;
}

void arc_pmm_free_block(void* block) {
    if (!block) return;
    uint32_t block_num = (uint32_t)block / PMM_BLOCK_SIZE;
    if (block_num < pmm_total_blocks && pmm_test_block(block_num)) {
        pmm_clear_block(block_num);
        pmm_used_blocks--;
    }
}

void arc_pmm_free_blocks(void* base, size_t count) {
    if (!base || count == 0) return;
    uint32_t start = (uint32_t)base / PMM_BLOCK_SIZE;
    for (size_t i = 0; i < count; i++) {
        if ((start + i) < pmm_total_blocks && pmm_test_block(start + i)) {
            pmm_clear_block(start + i);
            pmm_used_blocks--;
        }
    }
}

uint32_t arc_pmm_get_free_blocks(void) {
    return pmm_total_blocks - pmm_used_blocks;
}

uint32_t arc_pmm_get_total_blocks(void) {
    return pmm_total_blocks;
}

bool arc_pmm_is_block_used(uint32_t block_num) {
    if (block_num >= pmm_total_blocks) return true;
    return pmm_test_block(block_num) != 0;
}
