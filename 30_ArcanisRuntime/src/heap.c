#include <arcanis/heap.h>
#include <arcanis/string.h>

static heap_block_t* heap_head = (void*)0;
static uint32_t heap_start_addr = 0;
static size_t heap_total_size = 0;
static uint32_t heap_block_count = 0;

void arc_heap_init(uint32_t start, size_t size) {
    heap_start_addr = start;
    heap_total_size = size;
    heap_block_count = 1;

    heap_head = (heap_block_t*)start;
    heap_head->magic = HEAP_MAGIC;
    heap_head->size = size - sizeof(heap_block_t);
    heap_head->free = true;
    heap_head->next = (void*)0;
    heap_head->prev = (void*)0;
}

static heap_block_t* find_best_fit(size_t size) {
    heap_block_t* best = (void*)0;
    heap_block_t* current = heap_head;

    while (current) {
        if (current->magic != HEAP_MAGIC) break;
        if (current->free && current->size >= size) {
            if (!best || current->size < best->size) {
                best = current;
            }
        }
        current = current->next;
    }
    return best;
}

static void split_block(heap_block_t* block, size_t size) {
    if (block->size <= size + sizeof(heap_block_t) + HEAP_MIN_BLOCK_SIZE) return;

    heap_block_t* new_block = (heap_block_t*)((uint32_t)block + sizeof(heap_block_t) + size);
    new_block->magic = HEAP_MAGIC;
    new_block->size = block->size - size - sizeof(heap_block_t);
    new_block->free = true;
    new_block->next = block->next;
    new_block->prev = block;

    if (block->next) block->next->prev = new_block;
    block->next = new_block;
    block->size = size;
    heap_block_count++;
}

static void merge_free_blocks(void) {
    heap_block_t* current = heap_head;
    while (current && current->next) {
        if (current->free && current->next->free &&
            current->magic == HEAP_MAGIC && current->next->magic == HEAP_MAGIC) {
            current->size += sizeof(heap_block_t) + current->next->size;
            current->next = current->next->next;
            if (current->next) current->next->prev = current;
            heap_block_count--;
        } else {
            current = current->next;
        }
    }
}

void* arc_kmalloc(size_t size) {
    if (size == 0) return (void*)0;
    if (size < HEAP_MIN_BLOCK_SIZE) size = HEAP_MIN_BLOCK_SIZE;

    heap_block_t* block = find_best_fit(size);
    if (!block) return (void*)0;

    split_block(block, size);
    block->free = false;
    return (void*)((uint32_t)block + sizeof(heap_block_t));
}

void* arc_kmalign(size_t size, size_t alignment) {
    if (size == 0 || alignment == 0) return (void*)0;
    if (alignment < sizeof(void*)) alignment = sizeof(void*);

    size_t total = size + alignment + sizeof(heap_block_t);
    void* raw = arc_kmalloc(total);
    if (!raw) return (void*)0;

    uint32_t raw_addr = (uint32_t)raw;
    uint32_t aligned = (raw_addr + alignment - 1) & ~(alignment - 1);

    if (aligned == raw_addr) return raw;

    heap_block_t* header = (heap_block_t*)(aligned - sizeof(heap_block_t));
    header->magic = HEAP_MAGIC;
    header->size = size;
    header->free = false;
    header->next = (void*)0;
    header->prev = (void*)0;

    return (void*)aligned;
}

void* arc_kcalloc(size_t count, size_t size) {
    size_t total = count * size;
    if (count != 0 && total / count != size) return (void*)0;

    void* ptr = arc_kmalloc(total);
    if (ptr) arc_memset(ptr, 0, total);
    return ptr;
}

void* arc_krealloc(void* ptr, size_t new_size) {
    if (!ptr) return arc_kmalloc(new_size);
    if (new_size == 0) { arc_kfree(ptr); return (void*)0; }

    heap_block_t* block = (heap_block_t*)((uint32_t)ptr - sizeof(heap_block_t));
    if (block->magic != HEAP_MAGIC) return (void*)0;

    if (block->size >= new_size) return ptr;

    void* new_ptr = arc_kmalloc(new_size);
    if (!new_ptr) return (void*)0;

    arc_memcpy(new_ptr, ptr, block->size);
    arc_kfree(ptr);
    return new_ptr;
}

void arc_kfree(void* ptr) {
    if (!ptr) return;

    heap_block_t* block = (heap_block_t*)((uint32_t)ptr - sizeof(heap_block_t));
    if (block->magic != HEAP_MAGIC) return;

    block->free = true;
    merge_free_blocks();
}

size_t arc_heap_get_used(void) {
    size_t used = 0;
    heap_block_t* current = heap_head;
    while (current) {
        if (current->magic != HEAP_MAGIC) break;
        if (!current->free) used += sizeof(heap_block_t) + current->size;
        current = current->next;
    }
    return used;
}

size_t arc_heap_get_free(void) {
    return heap_total_size - arc_heap_get_used();
}

size_t arc_heap_get_total(void) {
    return heap_total_size;
}

uint32_t arc_heap_get_block_count(void) {
    return heap_block_count;
}
