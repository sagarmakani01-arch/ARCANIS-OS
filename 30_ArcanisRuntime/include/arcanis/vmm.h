#ifndef ARCANIS_VMM_H
#define ARCANIS_VMM_H

#include <stdint.h>
#include <stdbool.h>

#define VMM_PAGE_PRESENT 0x01
#define VMM_PAGE_WRITABLE 0x02
#define VMM_PAGE_USER 0x04
#define VMM_PAGE_WRITETHROUGH 0x08
#define VMM_PAGE_CACHE_DISABLE 0x10
#define VMM_PAGE_ACCESSED 0x20
#define VMM_PAGE_DIRTY 0x40
#define VMM_PAGE_SIZE_4MB 0x80
#define VMM_PAGE_GLOBAL 0x100

#define VMM_KERNEL_BASE 0xC0000000
#define VMM_USER_BASE 0x40000000

typedef struct {
    uint32_t entries[1024];
} __attribute__((aligned(4096))) vmm_page_directory_t;

typedef struct {
    uint32_t entries[1024];
} __attribute__((aligned(4096))) vmm_page_table_t;

void arc_vmm_init(void);
vmm_page_directory_t* arc_vmm_create_directory(void);
void arc_vmm_destroy_directory(vmm_page_directory_t* dir);
bool arc_vmm_map_page(vmm_page_directory_t* dir, uint32_t virt, uint32_t phys, uint32_t flags);
void arc_vmm_unmap_page(vmm_page_directory_t* dir, uint32_t virt);
uint32_t arc_vmm_get_physical(vmm_page_directory_t* dir, uint32_t virt);
void arc_vmm_switch_directory(vmm_page_directory_t* dir);

#endif
