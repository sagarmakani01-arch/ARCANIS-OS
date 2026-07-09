/**
 * elf.c — ELF Binary Loader
 *
 * Loads 32-bit statically-linked ELF executables into process address space.
 * Maps PT_LOAD segments into virtual memory with correct permissions.
 */
#include <arcanis/elf.h>
#include <arcanis/string.h>
#include <arcanis/vmm.h>
#include <arcanis/pmm.h>
#include <arcanis/process.h>

int elf_validate(const uint8_t* data, uint32_t size) {
    if (size < sizeof(elf32_header_t)) return ELF_ERR_MAGIC;

    const elf32_header_t* hdr = (const elf32_header_t*)data;

    /* Check magic */
    if (hdr->e_ident[0] != ELF_MAGIC0 || hdr->e_ident[1] != ELF_MAGIC1 ||
        hdr->e_ident[2] != ELF_MAGIC2 || hdr->e_ident[3] != ELF_MAGIC3)
        return ELF_ERR_MAGIC;

    /* Check class (32-bit) */
    if (hdr->e_ident[4] != ELF_CLASS_32) return ELF_ERR_CLASS;

    /* Check type (executable) */
    if (hdr->e_type != ELF_ET_EXEC) return ELF_ERR_TYPE;

    /* Check machine (i386) */
    if (hdr->e_machine != ELF_EM_386) return ELF_ERR_MACHINE;

    return ELF_OK;
}

uint32_t elf_get_entry(const uint8_t* data) {
    const elf32_header_t* hdr = (const elf32_header_t*)data;
    return hdr->e_entry;
}

int32_t elf_load(const uint8_t* data, uint32_t size) {
    /* Validate first */
    int err = elf_validate(data, size);
    if (err != ELF_OK) return err;

    const elf32_header_t* hdr = (const elf32_header_t*)data;
    process_t* proc = process_get_current();
    if (!proc) return ELF_ERR_NOMEM;

    /* Iterate program headers */
    const elf32_phdr_t* phdr = (const elf32_phdr_t*)(data + hdr->e_phoff);

    for (uint16_t i = 0; i < hdr->e_phnum; i++) {
        if (phdr[i].p_type != ELF_PT_LOAD) continue;

        uint32_t vaddr = phdr[i].p_vaddr;
        uint32_t memsz = phdr[i].p_memsz;
        uint32_t filesz = phdr[i].p_filesz;

        /* Calculate pages needed */
        uint32_t start_page = vaddr & ~0xFFF;
        uint32_t end_page = (vaddr + memsz + 0xFFF) & ~0xFFF;
        uint32_t num_pages = (end_page - start_page) / 0x1000;

        /* Map pages */
        for (uint32_t p = 0; p < num_pages; p++) {
            uint32_t page_addr = start_page + p * 0x1000;
            void* phys = pmm_alloc_block();
            if (!phys) return ELF_ERR_NOMEM;

            uint32_t flags = VMM_USER | VMM_PRESENT;
            if (phdr[i].p_flags & ELF_PF_W) flags |= VMM_WRITE;

            vmm_map_page(proc->page_directory, page_addr, (uint32_t)phys, flags);

            /* Zero the page */
            memset(phys, 0, 0x1000);
        }

        /* Copy segment data */
        if (filesz > 0) {
            uint32_t offset = 0;
            while (offset < filesz) {
                uint32_t page_offset = (vaddr + offset) & 0xFFF;
                uint32_t page_idx = (vaddr + offset) >> 12;
                uint32_t page_vaddr = page_idx << 12;

                /* Find the physical page */
                /* TODO: use vmm_get_physical() */
                uint32_t phys = vmm_get_physical(proc->page_directory, page_vaddr);
                if (!phys) return ELF_ERR_LOAD;

                uint32_t chunk = 0x1000 - page_offset;
                if (chunk > filesz - offset) chunk = filesz - offset;

                memcpy((void*)(phys + page_offset), data + phdr[i].p_offset + offset, chunk);
                offset += chunk;
            }
        }
    }

    return (int32_t)hdr->e_entry;
}
