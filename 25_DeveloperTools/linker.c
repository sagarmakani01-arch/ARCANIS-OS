/**
 * linker.c — ELF Linker Implementation
 *
 * Links object files and generates ELF executables.
 */
#include <arcanis/linker.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

void linker_init(linker_state_t* state) {
    if (!state) return;
    memset(state, 0, sizeof(linker_state_t));
    state->base_address = 0x08048000; /* Standard Linux base */
}

int linker_add_section(linker_state_t* state, const char* name, section_type_t type,
                        const uint8_t* data, uint32_t size, uint32_t alignment) {
    if (!state || state->num_sections >= LINKER_MAX_SECTIONS) return -1;

    linker_section_t* sec = &state->sections[state->num_sections];
    string_copy(sec->name, name, 64);
    sec->type = type;
    sec->size = size;
    sec->alignment = alignment ? alignment : 1;
    sec->offset = 0;
    sec->vaddr = 0;

    if (data && size > 0) {
        sec->data = (uint8_t*)kmalloc(size);
        if (!sec->data) return -1;
        memcpy(sec->data, data, size);
    } else {
        sec->data = NULL;
    }

    state->num_sections++;
    return 0;
}

int linker_add_symbol(linker_state_t* state, const char* name, symbol_binding_t binding,
                       uint32_t value, uint32_t size, uint32_t section) {
    if (!state || state->num_symbols >= LINKER_MAX_SYMBOLS) return -1;

    linker_symbol_t* sym = &state->symbols[state->num_symbols];
    string_copy(sym->name, name, 64);
    sym->binding = binding;
    sym->value = value;
    sym->size = size;
    sym->section = section;
    sym->file_index = 0;

    state->num_symbols++;
    return 0;
}

int linker_add_reloc(linker_state_t* state, uint32_t symbol, uint32_t offset,
                      reloc_type_t type, int32_t addend, uint32_t section) {
    if (!state || state->num_relocs >= LINKER_MAX_RELOCS) return -1;

    linker_reloc_t* rel = &state->relocs[state->num_relocs];
    rel->symbol = symbol;
    rel->offset = offset;
    rel->type = type;
    rel->addend = addend;
    rel->section = section;
    rel->file_index = 0;

    state->num_relocs++;
    return 0;
}

linker_symbol_t* linker_find_symbol(linker_state_t* state, const char* name) {
    if (!state || !name) return NULL;
    for (uint32_t i = 0; i < state->num_symbols; i++) {
        if (string_compare(state->symbols[i].name, name) == 0)
            return &state->symbols[i];
    }
    return NULL;
}

int linker_load_object(linker_state_t* state, const char* filename, const uint8_t* data, uint32_t size) {
    if (!state || !data) return -1;

    linker_section_t* sec = &state->sections[state->num_sections];
    string_copy(sec->name, filename, 64);
    sec->type = SEC_CODE;
    sec->size = size;
    sec->data = (uint8_t*)kmalloc(size);
    if (!sec->data) return -1;
    memcpy(sec->data, data, size);
    sec->alignment = 16;
    sec->offset = 0;
    sec->vaddr = 0;
    state->num_sections++;

    return 0;
}

int linker_load_elf(linker_state_t* state, const char* filename, const uint8_t* data, uint32_t size) {
    if (!state || !data || size < 52) return -1;

    /* Verify ELF magic */
    if (data[0] != 0x7F || data[1] != 'E' || data[2] != 'L' || data[3] != 'F') {
        string_copy(state->error_msg, "Not an ELF file", 256);
        state->error = 1;
        return -1;
    }

    uint16_t e_phoff = *(uint16_t*)(data + 28);
    uint16_t e_phnum = *(uint16_t*)(data + 44);

    /* Parse program headers */
    for (int i = 0; i < e_phnum; i++) {
        uint32_t off = e_phoff + i * 32;
        uint32_t p_type = *(uint32_t*)(data + off);
        uint32_t p_offset = *(uint32_t*)(data + off + 4);
        uint32_t p_vaddr = *(uint32_t*)(data + off + 8);
        uint32_t p_filesz = *(uint32_t*)(data + off + 16);
        uint32_t p_memsz = *(uint32_t*)(data + off + 20);

        if (p_type == 1 && p_filesz > 0) { /* PT_LOAD */
            linker_section_t* sec = &state->sections[state->num_sections];
            string_copy(sec->name, filename, 64);
            sec->type = SEC_CODE;
            sec->size = p_memsz;
            sec->vaddr = p_vaddr;
            sec->alignment = 4096;
            sec->data = (uint8_t*)kmalloc(p_memsz);
            if (!sec->data) return -1;
            memcpy(sec->data, data + p_offset, p_filesz);
            if (p_memsz > p_filesz)
                memset(sec->data + p_filesz, 0, p_memsz - p_filesz);
            state->num_sections++;
        }
    }

    return 0;
}

int linker_resolve_symbols(linker_state_t* state) {
    if (!state) return -1;

    for (uint32_t i = 0; i < state->num_symbols; i++) {
        linker_symbol_t* sym = &state->symbols[i];
        if (sym->binding == SYM_EXTERN && sym->value == 0) {
            /* Look for definition */
            linker_symbol_t* def = linker_find_symbol(state, sym->name);
            if (def && def->binding != SYM_EXTERN) {
                sym->value = def->value;
            } else {
                string_format(state->error_msg, "Undefined symbol: %s", sym->name);
                state->error = 1;
                return -1;
            }
        }
    }
    return 0;
}

int linker_apply_relocs(linker_state_t* state) {
    if (!state) return -1;

    for (uint32_t i = 0; i < state->num_relocs; i++) {
        linker_reloc_t* rel = &state->relocs[i];
        linker_symbol_t* sym = &state->symbols[rel->symbol];
        if (!sym) continue;

        uint32_t addr = sym->value + rel->addend;

        /* Find section to patch */
        linker_section_t* sec = &state->sections[rel->section];
        if (!sec || !sec->data) continue;

        uint32_t offset = rel->offset;
        if (offset + 4 > sec->size) continue;

        switch (rel->type) {
            case REL_32:
                sec->data[offset + 0] = addr & 0xFF;
                sec->data[offset + 1] = (addr >> 8) & 0xFF;
                sec->data[offset + 2] = (addr >> 16) & 0xFF;
                sec->data[offset + 3] = (addr >> 24) & 0xFF;
                break;

            case REL_PC32: {
                uint32_t pc = sec->vaddr + offset;
                uint32_t val = addr - pc;
                sec->data[offset + 0] = val & 0xFF;
                sec->data[offset + 1] = (val >> 8) & 0xFF;
                sec->data[offset + 2] = (val >> 16) & 0xFF;
                sec->data[offset + 3] = (val >> 24) & 0xFF;
                break;
            }

            default:
                break;
        }
    }
    return 0;
}

int linker_link(linker_state_t* state) {
    if (!state) return -1;

    /* Layout sections */
    uint32_t current_addr = state->base_address;
    uint32_t current_offset = 0;

    for (uint32_t i = 0; i < state->num_sections; i++) {
        linker_section_t* sec = &state->sections[i];
        uint32_t align = sec->alignment;
        if (align > 1) {
            uint32_t pad = (align - (current_offset % align)) % align;
            current_offset += pad;
            current_addr += pad;
        }
        sec->vaddr = current_addr;
        sec->offset = current_offset;
        current_addr += sec->size;
        current_offset += sec->size;
    }

    /* Resolve symbols */
    if (linker_resolve_symbols(state) != 0) return -1;

    /* Apply relocations */
    if (linker_apply_relocs(state) != 0) return -1;

    /* Allocate output buffer */
    state->data_size = current_offset;
    state->data = (uint8_t*)kmalloc(state->data_size);
    if (!state->data) return -1;
    memset(state->data, 0, state->data_size);

    /* Copy sections to output */
    for (uint32_t i = 0; i < state->num_sections; i++) {
        linker_section_t* sec = &state->sections[i];
        if (sec->data && sec->size > 0) {
            memcpy(state->data + sec->offset, sec->data, sec->size);
        }
    }

    return 0;
}

int linker_generate_elf(linker_state_t* state, uint8_t* output, uint32_t* output_size) {
    if (!state || !output || !output_size) return -1;

    /* Calculate total size */
    uint32_t total_size = 52; /* ELF header */
    total_size += state->num_sections * 40; /* Section headers */
    total_size += state->data_size;

    /* Section name string table */
    uint32_t shstrtab_size = 1;
    for (uint32_t i = 0; i < state->num_sections; i++)
        shstrtab_size += string_length(state->sections[i].name) + 1;
    total_size += shstrtab_size;

    *output_size = total_size;
    memset(output, 0, total_size);

    /* ELF Header */
    output[0] = 0x7F; output[1] = 'E'; output[2] = 'L'; output[3] = 'F';
    output[4] = 1;    /* 32-bit */
    output[5] = 1;    /* Little endian */
    output[6] = 1;    /* ELF version */
    output[7] = 0;    /* OS/ABI */
    *(uint16_t*)(output + 16) = 2;    /* ET_EXEC */
    *(uint16_t*)(output + 18) = 0x3C; /* EM_386 */
    *(uint32_t*)(output + 20) = 1;    /* EV_CURRENT */
    *(uint32_t*)(output + 24) = state->base_address; /* e_entry */
    *(uint32_t*)(output + 28) = 52;   /* e_phoff */
    *(uint32_t*)(output + 32) = 52 + state->num_sections * 40; /* e_shoff */
    *(uint32_t*)(output + 36) = 0;    /* e_flags */
    *(uint16_t*)(output + 40) = 52;   /* e_ehsize */
    *(uint16_t*)(output + 42) = 32;   /* e_phentsize */
    *(uint16_t*)(output + 44) = 0;    /* e_phnum */
    *(uint16_t*)(output + 46) = 40;   /* e_shentsize */
    *(uint16_t*)(output + 48) = state->num_sections + 1; /* e_shnum */
    *(uint16_t*)(output + 50) = state->num_sections;     /* e_shstrndx */

    /* Section headers */
    uint32_t sh_off = 52;
    uint32_t str_off = 1;

    /* NULL section */
    sh_off += 40;

    for (uint32_t i = 0; i < state->num_sections; i++) {
        linker_section_t* sec = &state->sections[i];
        uint32_t sh = sh_off + i * 40;

        /* sh_name */
        output[sh + 0] = str_off & 0xFF;
        output[sh + 1] = (str_off >> 8) & 0xFF;
        output[sh + 2] = (str_off >> 16) & 0xFF;
        output[sh + 3] = (str_off >> 24) & 0xFF;
        str_off += string_length(sec->name) + 1;

        /* sh_type */
        uint32_t sh_type = 1; /* SHT_PROGBITS */
        if (sec->type == SEC_BSS) sh_type = 8; /* SHT_NOBITS */
        if (sec->type == SEC_SYM_TAB) sh_type = 2; /* SHT_SYMTAB */
        if (sec->type == SEC_STR_TAB) sh_type = 3; /* SHT_STRTAB */
        *(uint32_t*)(output + sh + 4) = sh_type;

        /* sh_flags */
        *(uint32_t*)(output + sh + 8) = 2 | 4; /* alloc + execinstr */

        /* sh_addr, sh_offset, sh_size */
        *(uint32_t*)(output + sh + 12) = sec->vaddr;
        *(uint32_t*)(output + sh + 16) = sec->offset + 52 + state->num_sections * 40;
        *(uint32_t*)(output + sh + 20) = sec->size;
        *(uint32_t*)(output + sh + 24) = 0; /* sh_link */
        *(uint32_t*)(output + sh + 28) = 0; /* sh_info */
        *(uint32_t*)(output + sh + 32) = sec->alignment;
        *(uint32_t*)(output + sh + 36) = 0; /* sh_entsize */
    }

    /* Copy section data */
    uint32_t data_offset = 52 + state->num_sections * 40;
    for (uint32_t i = 0; i < state->num_sections; i++) {
        linker_section_t* sec = &state->sections[i];
        if (sec->data && sec->size > 0) {
            memcpy(output + data_offset + sec->offset, sec->data, sec->size);
        }
    }

    return 0;
}

void linker_set_entry(linker_state_t* state, uint32_t address) {
    if (state) state->entry_point = address;
}

void linker_set_base(linker_state_t* state, uint32_t address) {
    if (state) state->base_address = address;
}

const char* linker_get_error(linker_state_t* state) {
    return state ? state->error_msg : "NULL state";
}
