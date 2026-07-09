#include <arcanis/runtime.h>
#include <arcanis/pmm.h>
#include <arcanis/vmm.h>
#include <arcanis/heap.h>
#include <arcanis/string.h>

#define KERNEL_BASE 0xC0000000
#define HEAP_START  0x08000000
#define HEAP_SIZE   (64 * 1024 * 1024)

static arc_runtime_info_t runtime_info;

arc_status_t arc_runtime_init(uint32_t mem_map_base, uint32_t mem_map_size) {
    arc_memset(&runtime_info, 0, sizeof(arc_runtime_info_t));

    uint32_t total_mem = mem_map_size;
    if (total_mem < 1024 * 1024) total_mem = 1024 * 1024;

    uint32_t kernel_start = (uint32_t)&mem_map_base;
    uint32_t kernel_end = mem_map_base + mem_map_size;

    arc_pmm_init(total_mem, kernel_start, kernel_end);

    runtime_info.total_memory = total_mem;
    runtime_info.total_blocks = arc_pmm_get_total_blocks();
    runtime_info.free_blocks = arc_pmm_get_free_blocks();
    runtime_info.used_blocks = runtime_info.total_blocks - runtime_info.free_blocks;

    arc_vmm_init();

    arc_heap_init(HEAP_START, HEAP_SIZE);
    runtime_info.heap_start = (void*)HEAP_START;
    runtime_info.heap_size = HEAP_SIZE;

    runtime_info.initialized = true;
    return ARCANIS_OK;
}

arc_status_t arc_runtime_shutdown(void) {
    runtime_info.initialized = false;
    return ARCANIS_OK;
}

const arc_runtime_info_t* arc_runtime_get_info(void) {
    return &runtime_info;
}

void* arc_aligned_alloc(size_t size, size_t alignment) {
    if (!runtime_info.initialized) return (void*)0;
    return arc_kmalign(size, alignment);
}

void* arc_calloc(size_t count, size_t size) {
    if (!runtime_info.initialized) return (void*)0;
    return arc_kcalloc(count, size);
}

void* arc_realloc(void* ptr, size_t new_size) {
    if (!runtime_info.initialized) return (void*)0;
    return arc_krealloc(ptr, new_size);
}

void arc_free(void* ptr) {
    if (!runtime_info.initialized) return;
    arc_kfree(ptr);
}

size_t arc_get_used_memory(void) {
    if (!runtime_info.initialized) return 0;
    return arc_heap_get_used();
}

size_t arc_get_free_memory(void) {
    if (!runtime_info.initialized) return 0;
    return arc_heap_get_free();
}
