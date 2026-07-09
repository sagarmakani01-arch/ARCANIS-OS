#include <arcanis/vmm.h>
#include <arcanis/pmm.h>
#include <arcanis/string.h>

static vmm_page_directory_t* current_directory = (void*)0;

static inline void invlpg(uint32_t addr) {
    __asm__ volatile ("invlpg (%0)" : : "r"(addr) : "memory");
}

static inline void load_cr3(uint32_t dir) {
    __asm__ volatile ("mov %0, %%cr3" : : "r"(dir) : "memory");
}

static inline uint32_t read_cr3(void) {
    uint32_t val;
    __asm__ volatile ("mov %%cr3, %0" : "=r"(val));
    return val;
}

static inline void enable_paging(void) {
    uint32_t cr0;
    __asm__ volatile ("mov %%cr0, %0" : "=r"(cr0));
    cr0 |= 0x80000000;
    __asm__ volatile ("mov %0, %%cr0" : : "r"(cr0));
}

static vmm_page_table_t* vmm_get_or_create_table(vmm_page_directory_t* dir, uint32_t index, uint32_t flags) {
    if (dir->entries[index] & VMM_PAGE_PRESENT) {
        return (vmm_page_table_t*)(dir->entries[index] & ~0xFFF);
    }

    void* table_phys = arc_pmm_alloc_block();
    if (!table_phys) return (void*)0;

    arc_memset(table_phys, 0, sizeof(vmm_page_table_t));
    dir->entries[index] = (uint32_t)table_phys | (flags | VMM_PAGE_PRESENT);
    return (vmm_page_table_t*)table_phys;
}

void arc_vmm_init(void) {
    current_directory = (vmm_page_directory_t*)read_cr3();
}

vmm_page_directory_t* arc_vmm_create_directory(void) {
    void* phys = arc_pmm_alloc_block();
    if (!phys) return (void*)0;

    vmm_page_directory_t* dir = (vmm_page_directory_t*)phys;
    arc_memset(dir, 0, sizeof(vmm_page_directory_t));
    return dir;
}

void arc_vmm_destroy_directory(vmm_page_directory_t* dir) {
    if (!dir) return;

    for (uint32_t i = 0; i < 1024; i++) {
        if (dir->entries[i] & VMM_PAGE_PRESENT) {
            vmm_page_table_t* table = (vmm_page_table_t*)(dir->entries[i] & ~0xFFF);
            for (uint32_t j = 0; j < 1024; j++) {
                if (table->entries[j] & VMM_PAGE_PRESENT) {
                    arc_pmm_free_block((void*)(table->entries[j] & ~0xFFF));
                }
            }
            arc_pmm_free_block(table);
        }
    }
    arc_pmm_free_block(dir);
}

bool arc_vmm_map_page(vmm_page_directory_t* dir, uint32_t virt, uint32_t phys, uint32_t flags) {
    uint32_t dir_index = (virt >> 22) & 0x3FF;
    uint32_t table_index = (virt >> 12) & 0x3FF;

    vmm_page_table_t* table = vmm_get_or_create_table(dir, dir_index, flags);
    if (!table) return false;

    table->entries[table_index] = (phys & ~0xFFF) | (flags | VMM_PAGE_PRESENT);
    invlpg(virt);
    return true;
}

void arc_vmm_unmap_page(vmm_page_directory_t* dir, uint32_t virt) {
    uint32_t dir_index = (virt >> 22) & 0x3FF;
    uint32_t table_index = (virt >> 12) & 0x3FF;

    if (!(dir->entries[dir_index] & VMM_PAGE_PRESENT)) return;

    vmm_page_table_t* table = (vmm_page_table_t*)(dir->entries[dir_index] & ~0xFFF);
    table->entries[table_index] = 0;
    invlpg(virt);
}

uint32_t arc_vmm_get_physical(vmm_page_directory_t* dir, uint32_t virt) {
    uint32_t dir_index = (virt >> 22) & 0x3FF;
    uint32_t table_index = (virt >> 12) & 0x3FF;
    uint32_t offset = virt & 0xFFF;

    if (!(dir->entries[dir_index] & VMM_PAGE_PRESENT)) return 0;

    vmm_page_table_t* table = (vmm_page_table_t*)(dir->entries[dir_index] & ~0xFFF);
    if (!(table->entries[table_index] & VMM_PAGE_PRESENT)) return 0;

    return (table->entries[table_index] & ~0xFFF) | offset;
}

void arc_vmm_switch_directory(vmm_page_directory_t* dir) {
    if (!dir) return;
    current_directory = dir;
    load_cr3((uint32_t)dir);
    enable_paging();
}
