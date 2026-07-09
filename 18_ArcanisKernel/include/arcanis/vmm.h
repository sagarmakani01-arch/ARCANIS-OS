#ifndef ARCANIS_VMM_H
#define ARCANIS_VMM_H

#include <arcanis/types.h>

#define VMM_PRESENT   0x01
#define VMM_WRITE     0x02
#define VMM_USER      0x04
#define VMM_WRITETHRU 0x08
#define VMM_CACHE_DIS 0x10
#define VMM_ACCESSED  0x20
#define VMM_DIRTY     0x40
#define VMM_PAGE_SIZE 0x80
#define VMM_GLOBAL    0x100

#define VMM_PRESENT_BIT 0
#define VMM_WRITE_BIT   1
#define VMM_USER_BIT    2

typedef uint32_t page_directory_entry_t;
typedef uint32_t page_table_entry_t;

typedef struct {
    page_directory_entry_t entries[1024];
} __attribute__((aligned(4096))) page_directory_t;

typedef struct {
    page_table_entry_t entries[1024];
} __attribute__((aligned(4096))) page_table_t;

void vmm_initialize(void);
page_directory_t* vmm_create_address_space(void);
void vmm_map_page(page_directory_t* dir, uint32_t virt, uint32_t phys, uint32_t flags);
void vmm_unmap_page(page_directory_t* dir, uint32_t virt);
uint32_t vmm_get_physical(page_directory_t* dir, uint32_t virt);
void vmm_switch_directory(page_directory_t* dir);
page_directory_t* vmm_get_current_directory(void);

#endif
