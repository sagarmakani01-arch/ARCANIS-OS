/**
 * linker.h — ELF Linker
 *
 * Links object files into ELF executables.
 * Resolves symbols, relocations, and sections.
 */
#ifndef ARCANIS_LINKER_H
#define ARCANIS_LINKER_H

#include <arcanis/types.h>

#define LINKER_MAX_SECTIONS  64
#define LINKER_MAX_SYMBOLS   256
#define LINKER_MAX_RELOCS    256
#define LINKER_MAX_FILES     16
#define LINKER_MAX_OUTPUT    131072

typedef enum {
    SEC_NULL, SEC_CODE, SEC_DATA, SEC_BSS, SEC_RODATA, SEC_SYM_TAB, SEC_STR_TAB
} section_type_t;

typedef struct {
    char        name[64];
    section_type_t type;
    uint32_t    vaddr;
    uint32_t    size;
    uint32_t    offset;
    uint8_t*    data;
    uint32_t    alignment;
} linker_section_t;

typedef enum {
    SYM_LOCAL, SYM_GLOBAL, SYM_EXTERN
} symbol_binding_t;

typedef struct {
    char            name[64];
    symbol_binding_t binding;
    uint32_t        value;
    uint32_t        size;
    uint32_t        section;
    uint32_t        file_index;
} linker_symbol_t;

typedef enum {
    REL_NONE, REL_32, REL_PC32, REL_GOT32, REL_PLT32
} reloc_type_t;

typedef struct {
    uint32_t    symbol;
    uint32_t    offset;
    reloc_type_t type;
    int32_t     addend;
    uint32_t    section;
    uint32_t    file_index;
} linker_reloc_t;

typedef struct {
    char            name[256];
    linker_section_t sections[LINKER_MAX_SECTIONS];
    uint32_t        num_sections;
    linker_symbol_t symbols[LINKER_MAX_SYMBOLS];
    uint32_t        num_symbols;
    linker_reloc_t  relocs[LINKER_MAX_RELOCS];
    uint32_t        num_relocs;
    uint8_t*        data;
    uint32_t        data_size;
    uint32_t        entry_point;
    uint32_t        base_address;
    int             error;
    char            error_msg[256];
} linker_state_t;

/* Initialization */
void linker_init(linker_state_t* state);

/* Load an object file */
int  linker_load_object(linker_state_t* state, const char* filename, const uint8_t* data, uint32_t size);

/* Load an ELF binary */
int  linker_load_elf(linker_state_t* state, const char* filename, const uint8_t* data, uint32_t size);

/* Add a section */
int  linker_add_section(linker_state_t* state, const char* name, section_type_t type,
                        const uint8_t* data, uint32_t size, uint32_t alignment);

/* Add a symbol */
int  linker_add_symbol(linker_state_t* state, const char* name, symbol_binding_t binding,
                       uint32_t value, uint32_t size, uint32_t section);

/* Add a relocation */
int  linker_add_reloc(linker_state_t* state, uint32_t symbol, uint32_t offset,
                      reloc_type_t type, int32_t addend, uint32_t section);

/* Resolve all symbols */
int  linker_resolve_symbols(linker_state_t* state);

/* Apply relocations */
int  linker_apply_relocs(linker_state_t* state);

/* Link everything together */
int  linker_link(linker_state_t* state);

/* Generate ELF output */
int  linker_generate_elf(linker_state_t* state, uint8_t* output, uint32_t* output_size);

/* Set entry point */
void linker_set_entry(linker_state_t* state, uint32_t address);

/* Set base address */
void linker_set_base(linker_state_t* state, uint32_t address);

/* Find a symbol */
linker_symbol_t* linker_find_symbol(linker_state_t* state, const char* name);

/* Error handling */
const char* linker_get_error(linker_state_t* state);

#endif
