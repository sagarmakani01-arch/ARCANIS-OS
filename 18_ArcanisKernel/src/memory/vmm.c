#include <arcanis/vmm.h>
#include <arcanis/pmm.h>
#include <arcanis/string.h>
#include <arcanis/defs.h>
#include <arcanis/io.h>

static page_directory_t* current_directory = NULL;
static page_directory_t* kernel_directory = NULL;

extern uint32_t __kernel_start;
extern uint32_t __kernel_end;

void vmm_initialize(void) {
    kernel_directory = (page_directory_t*)pmm_alloc_block();
    memset(kernel_directory, 0, sizeof(page_directory_t));

    page_table_t* kernel_tables[4] = { NULL };

    uint32_t kernel_start = (uint32_t)&__kernel_start;
    uint32_t kernel_end = (uint32_t)&__kernel_end;
    uint32_t addr = 0;

    while (addr < kernel_end + PAGE_SIZE * 256) {
        uint32_t pd_index = addr >> 22;
        uint32_t pt_index = (addr >> 12) & 0x3FF;

        if (!kernel_directory->entries[pd_index]) {
            page_table_t* table = (page_table_t*)pmm_alloc_block();
            memset(table, 0, sizeof(page_table_t));
            kernel_directory->entries[pd_index] =
                (uint32_t)table | VMM_PRESENT | VMM_WRITE | VMM_USER;
            kernel_tables[pd_index] = table;
        } else {
            kernel_tables[pd_index] = (page_table_t*)(kernel_directory->entries[pd_index] & ~0xFFF);
        }

        kernel_tables[pd_index]->entries[pt_index] = addr | VMM_PRESENT | VMM_WRITE;
        addr += PAGE_SIZE;
    }

    current_directory = kernel_directory;
    set_cr3((uint32_t)current_directory);

    uint32_t cr0;
    asm volatile("mov %%cr0, %0" : "=r"(cr0));
    cr0 |= 0x80000000;
    asm volatile("mov %0, %%cr0" : : "r"(cr0));
}

page_directory_t* vmm_create_address_space(void) {
    page_directory_t* dir = (page_directory_t*)pmm_alloc_block();
    memset(dir, 0, sizeof(page_directory_t));

    uint32_t kernel_pd = (uint32_t)kernel_directory;
    uint32_t user_pd = (uint32_t)dir;

    for (int i = 0; i < 1024; i++) {
        if (kernel_directory->entries[i] & VMM_USER) {
            dir->entries[i] = kernel_directory->entries[i];
        }
    }

    return dir;
}

static page_table_t* vmm_get_table(page_directory_t* dir, uint32_t virt, bool create) {
    uint32_t pd_index = virt >> 22;

    if (dir->entries[pd_index]) {
        return (page_table_t*)(dir->entries[pd_index] & ~0xFFF);
    }

    if (!create) return NULL;

    page_table_t* table = (page_table_t*)pmm_alloc_block();
    memset(table, 0, sizeof(page_table_t));
    dir->entries[pd_index] = (uint32_t)table | VMM_PRESENT | VMM_WRITE | VMM_USER;

    return table;
}

void vmm_map_page(page_directory_t* dir, uint32_t virt, uint32_t phys, uint32_t flags) {
    page_table_t* table = vmm_get_table(dir, virt, true);
    uint32_t pt_index = (virt >> 12) & 0x3FF;

    table->entries[pt_index] = (phys & ~0xFFF) | (flags | VMM_PRESENT);

    asm volatile("invlpg (%0)" : : "r"(virt) : "memory");
}

void vmm_unmap_page(page_directory_t* dir, uint32_t virt) {
    page_table_t* table = vmm_get_table(dir, virt, false);
    if (!table) return;

    uint32_t pt_index = (virt >> 12) & 0x3FF;
    table->entries[pt_index] = 0;

    asm volatile("invlpg (%0)" : : "r"(virt) : "memory");
}

uint32_t vmm_get_physical(page_directory_t* dir, uint32_t virt) {
    page_table_t* table = vmm_get_table(dir, virt, false);
    if (!table) return 0;

    uint32_t pt_index = (virt >> 12) & 0x3FF;
    if (!(table->entries[pt_index] & VMM_PRESENT)) return 0;

    return table->entries[pt_index] & ~0xFFF;
}

void vmm_switch_directory(page_directory_t* dir) {
    current_directory = dir;
    set_cr3((uint32_t)dir);
}

page_directory_t* vmm_get_current_directory(void) {
    return current_directory;
}
