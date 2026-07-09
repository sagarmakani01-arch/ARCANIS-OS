#ifndef ARCANIS_ELF_H
#define ARCANIS_ELF_H

#include <arcanis/types.h>

/* ELF magic */
#define ELF_MAGIC0 0x7f
#define ELF_MAGIC1 'E'
#define ELF_MAGIC2 'L'
#define ELF_MAGIC3 'F'

/* ELF types */
#define ELF_ET_NONE   0
#define ELF_ET_EXEC   2
#define ELF_ET_DYN    3

/* ELF machine */
#define ELF_EM_386    3

/* ELF class */
#define ELF_CLASS_32  1
#define ELF_CLASS_64  2

/* Program header types */
#define ELF_PT_NULL    0
#define ELF_PT_LOAD    1
#define ELF_PT_DYNAMIC 2
#define ELF_PT_INTERP  3
#define ELF_PT_NOTE    4

/* Program header flags */
#define ELF_PF_X       0x1
#define ELF_PF_W       0x2
#define ELF_PF_R       0x4

/* Section header types */
#define ELF_SHT_NULL    0
#define ELF_SHT_PROGBITS 1
#define ELF_SHT_SYMTAB  2
#define ELF_SHT_STRTAB  3

#pragma pack(push, 1)

typedef struct {
    uint8_t  e_ident[16];
    uint16_t e_type;
    uint16_t e_machine;
    uint32_t e_version;
    uint32_t e_entry;
    uint32_t e_phoff;
    uint32_t e_shoff;
    uint32_t e_flags;
    uint16_t e_ehsize;
    uint16_t e_phentsize;
    uint16_t e_phnum;
    uint16_t e_shentsize;
    uint16_t e_shnum;
    uint16_t e_shstrndx;
} elf32_header_t;

typedef struct {
    uint32_t p_type;
    uint32_t p_offset;
    uint32_t p_vaddr;
    uint32_t p_paddr;
    uint32_t p_filesz;
    uint32_t p_memsz;
    uint32_t p_flags;
    uint32_t p_align;
} elf32_phdr_t;

typedef struct {
    uint32_t sh_name;
    uint32_t sh_type;
    uint32_t sh_flags;
    uint32_t sh_addr;
    uint32_t sh_offset;
    uint32_t sh_size;
    uint32_t sh_link;
    uint32_t sh_info;
    uint32_t sh_addralign;
    uint32_t sh_entsize;
} elf32_shdr_t;

#pragma pack(pop)

/* Return codes */
#define ELF_OK           0
#define ELF_ERR_MAGIC   -1
#define ELF_ERR_CLASS   -2
#define ELF_ERR_TYPE    -3
#define ELF_ERR_MACHINE -4
#define ELF_ERR_LOAD    -5
#define ELF_ERR_NOMEM   -6

/**
 * Load an ELF binary from memory buffer into current process address space.
 * Returns entry point address on success, or negative error code.
 */
int32_t elf_load(const uint8_t* data, uint32_t size);

/**
 * Validate ELF header without loading.
 * Returns ELF_OK or error code.
 */
int elf_validate(const uint8_t* data, uint32_t size);

/**
 * Get entry point from ELF header (without loading).
 */
uint32_t elf_get_entry(const uint8_t* data);

#endif
