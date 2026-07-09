#include <arcanis/heap.h>
#include <arcanis/types.h>
#include <arcanis/string.h>

static heap_block_t* heap_head = NULL;
static uint32_t heap_start_addr = 0;
static size_t heap_total_size = 0;

void heap_initialize(uint32_t start, size_t size) {
    heap_start_addr = start;
    heap_total_size = size;

    heap_head = (heap_block_t*)start;
    heap_head->size = size - sizeof(heap_block_t);
    heap_head->free = true;
    heap_head->next = NULL;
}

void* kmalloc(size_t size) {
    heap_block_t* current = heap_head;

    while (current) {
        if (current->free && current->size >= size) {
            if (current->size > size + sizeof(heap_block_t) + 16) {
                heap_block_t* new_block = (heap_block_t*)((uint32_t)current + sizeof(heap_block_t) + size);
                new_block->size = current->size - size - sizeof(heap_block_t);
                new_block->free = true;
                new_block->next = current->next;

                current->next = new_block;
                current->size = size;
            }
            current->free = false;
            return (void*)((uint32_t)current + sizeof(heap_block_t));
        }
        current = current->next;
    }

    return NULL;
}

void* kmalloc_aligned(size_t size) {
    uint32_t addr = (uint32_t)kmalloc(size + 4096);
    if (!addr) return NULL;

    uint32_t aligned = (addr + 4095) & ~4095;
    heap_block_t* block = (heap_block_t*)(aligned - sizeof(heap_block_t));
    block->size = size;
    block->free = false;

    return (void*)aligned;
}

void kfree(void* ptr) {
    if (!ptr) return;

    heap_block_t* block = (heap_block_t*)((uint32_t)ptr - sizeof(heap_block_t));
    block->free = true;

    heap_block_t* current = heap_head;
    while (current && current->next) {
        if (current->free && current->next->free) {
            current->size += sizeof(heap_block_t) + current->next->size;
            current->next = current->next->next;
        } else {
            current = current->next;
        }
    }
}

size_t heap_get_used(void) {
    size_t used = 0;
    heap_block_t* current = heap_head;
    while (current) {
        if (!current->free) used += current->size + sizeof(heap_block_t);
        current = current->next;
    }
    return used;
}

size_t heap_get_free(void) {
    return heap_total_size - heap_get_used();
}
