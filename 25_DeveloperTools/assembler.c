/**
 * assembler.c — x86 Assembler Implementation
 *
 * Single-pass assembler with label resolution.
 */
#include <arcanis/assembler.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

/* ---- Register table ---- */

typedef struct {
    const char* name;
    asm_reg_t   reg;
    uint8_t     encoding;
    uint8_t     size;
} asm_reg_info_t;

static const asm_reg_info_t reg_table[] = {
    {"al", REG_AL, 0, 1}, {"cl", REG_CL, 1, 1}, {"dl", REG_DL, 2, 1}, {"bl", REG_BL, 3, 1},
    {"ah", REG_AH, 4, 1}, {"ch", REG_CH, 5, 1}, {"dh", REG_DH, 6, 1}, {"bh", REG_BH, 7, 1},
    {"ax", REG_AX, 0, 2}, {"cx", REG_CX, 1, 2}, {"dx", REG_DX, 2, 2}, {"bx", REG_BX, 3, 2},
    {"sp", REG_SP, 4, 2}, {"bp", REG_BP, 5, 2}, {"si", REG_SI, 6, 2}, {"di", REG_DI, 7, 2},
    {"eax", REG_EAX, 0, 4}, {"ecx", REG_ECX, 1, 4}, {"edx", REG_EDX, 2, 4}, {"ebx", REG_EBX, 3, 4},
    {"esp", REG_ESP, 4, 4}, {"ebp", REG_EBP, 5, 4}, {"esi", REG_ESI, 6, 4}, {"edi", REG_EDI, 7, 4},
    {"cs", REG_CS, 1, 2}, {"ds", REG_DS, 3, 2}, {"es", REG_ES, 0, 2},
    {"fs", REG_FS, 4, 2}, {"gs", REG_GS, 5, 2}, {"ss", REG_SS, 2, 2},
    {NULL, REG_NONE, 0, 0}
};

int asm_parse_reg(const char* name, asm_reg_t* reg) {
    for (int i = 0; reg_table[i].name; i++) {
        if (string_compare(name, reg_table[i].name) == 0) {
            *reg = reg_table[i].reg;
            return 0;
        }
    }
    return -1;
}

uint8_t asm_reg_encoding(asm_reg_t reg) {
    for (int i = 0; reg_table[i].name; i++)
        if (reg_table[i].reg == reg) return reg_table[i].encoding;
    return 0;
}

uint8_t asm_reg_size(asm_reg_t reg) {
    for (int i = 0; reg_table[i].name; i++)
        if (reg_table[i].reg == reg) return reg_table[i].size;
    return 0;
}

/* ---- Opcode table ---- */

typedef struct {
    const char*   name;
    asm_opcode_t  opcode;
} asm_opcode_info_t;

static const asm_opcode_info_t opcode_table[] = {
    {"mov", OPCODE_MOV}, {"add", OPCODE_ADD}, {"sub", OPCODE_SUB},
    {"mul", OPCODE_MUL}, {"div", OPCODE_DIV},
    {"and", OPCODE_AND}, {"or", OPCODE_OR}, {"xor", OPCODE_XOR},
    {"not", OPCODE_NOT}, {"shl", OPCODE_SHL}, {"shr", OPCODE_SHR},
    {"cmp", OPCODE_CMP}, {"test", OPCODE_TEST},
    {"jmp", OPCODE_JMP}, {"je", OPCODE_JE}, {"jne", OPCODE_JNE},
    {"jg", OPCODE_JG}, {"jl", OPCODE_JL}, {"jge", OPCODE_JGE}, {"jle", OPCODE_JLE},
    {"call", OPCODE_CALL}, {"ret", OPCODE_RET},
    {"push", OPCODE_PUSH}, {"pop", OPCODE_POP},
    {"int", OPCODE_INT}, {"iret", OPCODE_IRET},
    {"nop", OPCODE_NOP}, {"hlt", OPCODE_HLT},
    {"cli", OPCODE_CLI}, {"sti", OPCODE_STI},
    {"inc", OPCODE_INC}, {"dec", OPCODE_DEC},
    {"lea", OPCODE_LEA}, {"in", OPCODE_IN}, {"out", OPCODE_OUT},
    {"cld", OPCODE_CLD}, {"std", OPCODE_STD},
    {"enter", OPCODE_ENTER}, {"leave", OPCODE_LEAVE},
    {"movsb", OPCODE_MOVSB}, {"movsw", OPCODE_MOVSW}, {"movsd", OPCODE_MOVSD},
    {NULL, OPCODE_NOT_IMPL}
};

asm_opcode_t asm_parse_opcode(const char* name) {
    for (int i = 0; opcode_table[i].name; i++)
        if (string_compare(name, opcode_table[i].name) == 0)
            return opcode_table[i].opcode;
    return OPCODE_NOT_IMPL;
}

/* ---- Initialization ---- */

void asm_init(asm_state_t* state) {
    if (!state) return;
    memset(state, 0, sizeof(asm_state_t));
    state->bits = 32;
}

/* ---- Encoding helpers ---- */

static void emit_byte(asm_state_t* state, uint8_t byte) {
    if (state->code_size < ASM_MAX_CODE) {
        state->code[state->code_size++] = byte;
    }
}

static void emit_word(asm_state_t* state, uint16_t word) {
    emit_byte(state, word & 0xFF);
    emit_byte(state, (word >> 8) & 0xFF);
}

static void emit_dword(asm_state_t* state, uint32_t dword) {
    emit_byte(state, dword & 0xFF);
    emit_byte(state, (dword >> 8) & 0xFF);
    emit_byte(state, (dword >> 16) & 0xFF);
    emit_byte(state, (dword >> 24) & 0xFF);
}

/* ModR/M byte encoding */
static void emit_modrm(asm_state_t* state, uint8_t mod, uint8_t reg, uint8_t rm) {
    emit_byte(state, (mod << 6) | (reg << 3) | rm);
}

/* ---- Instruction encoding ---- */

static int encode_mov_imm_to_reg(asm_state_t* state, asm_reg_t reg, uint32_t imm) {
    uint8_t enc = asm_reg_encoding(reg);
    uint8_t size = asm_reg_size(reg);
    if (size == 1) {
        emit_byte(state, 0xB0 + enc);
        emit_byte(state, imm & 0xFF);
    } else if (size == 2) {
        emit_byte(state, 0x66);
        emit_byte(state, 0xB8 + enc);
        emit_word(state, imm & 0xFFFF);
    } else {
        emit_byte(state, 0xB8 + enc);
        emit_dword(state, imm);
    }
    return 0;
}

static int encode_mov_reg_to_reg(asm_state_t* state, asm_reg_t dst, asm_reg_t src) {
    uint8_t size_dst = asm_reg_size(dst);
    uint8_t size_src = asm_reg_size(src);
    if (size_dst != size_src) return -1;
    uint8_t enc_dst = asm_reg_encoding(dst);
    uint8_t enc_src = asm_reg_encoding(src);
    if (size_dst == 1) {
        emit_byte(state, 0x88);
        emit_modrm(state, 3, enc_src, enc_dst);
    } else if (size_dst == 2) {
        emit_byte(state, 0x66);
        emit_byte(state, 0x89);
        emit_modrm(state, 3, enc_src, enc_dst);
    } else {
        emit_byte(state, 0x89);
        emit_modrm(state, 3, enc_src, enc_dst);
    }
    return 0;
}

static int encode_mov_mem_to_reg(asm_state_t* state, uint32_t addr, asm_reg_t reg) {
    uint8_t enc = asm_reg_encoding(reg);
    uint8_t size = asm_reg_size(reg);
    if (size == 2) {
        emit_byte(state, 0x66);
        emit_byte(state, 0x8B);
        emit_modrm(state, 0, enc, 5);
        emit_dword(state, addr);
    } else if (size == 4) {
        emit_byte(state, 0x8B);
        emit_modrm(state, 0, enc, 5);
        emit_dword(state, addr);
    } else return -1;
    return 0;
}

static int encode_mov_reg_to_mem(asm_state_t* state, asm_reg_t reg, uint32_t addr) {
    uint8_t enc = asm_reg_encoding(reg);
    uint8_t size = asm_reg_size(reg);
    if (size == 2) {
        emit_byte(state, 0x66);
        emit_byte(state, 0x89);
        emit_modrm(state, 0, enc, 5);
        emit_dword(state, addr);
    } else if (size == 4) {
        emit_byte(state, 0x89);
        emit_modrm(state, 0, enc, 5);
        emit_dword(state, addr);
    } else return -1;
    return 0;
}

static int encode_alu_reg_imm(asm_state_t* state, uint8_t opcode_base, asm_reg_t reg, uint32_t imm) {
    uint8_t enc = asm_reg_encoding(reg);
    uint8_t size = asm_reg_size(reg);
    if (size == 1) {
        emit_byte(state, opcode_base + 0);
        emit_modrm(state, 3, 0, enc);
        emit_byte(state, imm & 0xFF);
    } else if (size == 2) {
        emit_byte(state, 0x66);
        emit_byte(state, opcode_base + 1);
        emit_modrm(state, 3, 0, enc);
        emit_word(state, imm & 0xFFFF);
    } else {
        emit_byte(state, opcode_base + 1);
        emit_modrm(state, 3, 0, enc);
        emit_dword(state, imm);
    }
    return 0;
}

static int encode_push_reg(asm_state_t* state, asm_reg_t reg) {
    uint8_t enc = asm_reg_encoding(reg);
    uint8_t size = asm_reg_size(reg);
    if (size == 2) {
        emit_byte(state, 0x66);
        emit_byte(state, 0x50 + enc);
    } else {
        emit_byte(state, 0x50 + enc);
    }
    return 0;
}

static int encode_pop_reg(asm_state_t* state, asm_reg_t reg) {
    uint8_t enc = asm_reg_encoding(reg);
    uint8_t size = asm_reg_size(reg);
    if (size == 2) {
        emit_byte(state, 0x66);
        emit_byte(state, 0x58 + enc);
    } else {
        emit_byte(state, 0x58 + enc);
    }
    return 0;
}

static int encode_push_imm(asm_state_t* state, uint32_t imm) {
    if (imm <= 0xFF) {
        emit_byte(state, 0x6A);
        emit_byte(state, imm & 0xFF);
    } else {
        emit_byte(state, 0x68);
        emit_dword(state, imm);
    }
    return 0;
}

static int encode_int(asm_state_t* state, uint8_t vector) {
    emit_byte(state, 0xCD);
    emit_byte(state, vector);
    return 0;
}

static int encode_nop(asm_state_t* state) {
    emit_byte(state, 0x90);
    return 0;
}

static int encode_hlt(asm_state_t* state) {
    emit_byte(state, 0xF4);
    return 0;
}

static int encode_cli(asm_state_t* state) {
    emit_byte(state, 0xFA);
    return 0;
}

static int encode_sti(asm_state_t* state) {
    emit_byte(state, 0xFB);
    return 0;
}

static int encode_ret(asm_state_t* state) {
    emit_byte(state, 0xC3);
    return 0;
}

static int encode_call_rel(asm_state_t* state, int32_t offset) {
    emit_byte(state, 0xE8);
    emit_dword(state, (uint32_t)offset);
    return 0;
}

static int encode_jmp_rel(asm_state_t* state, int32_t offset) {
    if (offset >= -128 && offset <= 127) {
        emit_byte(state, 0xEB);
        emit_byte(state, (uint8_t)(int8_t)offset);
    } else {
        emit_byte(state, 0xE9);
        emit_dword(state, (uint32_t)offset);
    }
    return 0;
}

static int encode_jcc_rel(asm_state_t* state, uint8_t opcode, int32_t offset) {
    if (offset >= -128 && offset <= 127) {
        emit_byte(state, opcode);
        emit_byte(state, (uint8_t)(int8_t)offset);
    } else {
        emit_byte(state, 0x0F);
        emit_byte(state, opcode + 0x10);
        emit_dword(state, (uint32_t)offset);
    }
    return 0;
}

/* ---- Instruction encoding dispatcher ---- */

int asm_encode_instruction(asm_instruction_t* instr, asm_state_t* state) {
    switch (instr->opcode) {
        case OPCODE_MOV:
            if (instr->operands[0].type == OPERAND_REG && instr->operands[1].type == OPERAND_IMM)
                return encode_mov_imm_to_reg(state, instr->operands[0].reg, instr->operands[1].imm);
            if (instr->operands[0].type == OPERAND_REG && instr->operands[1].type == OPERAND_REG)
                return encode_mov_reg_to_reg(state, instr->operands[0].reg, instr->operands[1].reg);
            if (instr->operands[0].type == OPERAND_REG && instr->operands[1].type == OPERAND_MEM)
                return encode_mov_mem_to_reg(state, instr->operands[1].mem.offset, instr->operands[0].reg);
            if (instr->operands[0].type == OPERAND_MEM && instr->operands[1].type == OPERAND_REG)
                return encode_mov_reg_to_mem(state, instr->operands[1].reg, instr->operands[0].mem.offset);
            break;

        case OPCODE_ADD:
            if (instr->operands[0].type == OPERAND_REG && instr->operands[1].type == OPERAND_IMM)
                return encode_alu_reg_imm(state, 0x80, instr->operands[0].reg, instr->operands[1].imm);
            break;

        case OPCODE_SUB:
            if (instr->operands[0].type == OPERAND_REG && instr->operands[1].type == OPERAND_IMM)
                return encode_alu_reg_imm(state, 0x80 + 5, instr->operands[0].reg, instr->operands[1].imm);
            break;

        case OPCODE_PUSH:
            if (instr->operands[0].type == OPERAND_REG)
                return encode_push_reg(state, instr->operands[0].reg);
            if (instr->operands[0].type == OPERAND_IMM)
                return encode_push_imm(state, instr->operands[0].imm);
            break;

        case OPCODE_POP:
            if (instr->operands[0].type == OPERAND_REG)
                return encode_pop_reg(state, instr->operands[0].reg);
            break;

        case OPCODE_INT:
            if (instr->operands[0].type == OPERAND_IMM)
                return encode_int(state, instr->operands[0].imm & 0xFF);
            break;

        case OPCODE_NOP:  return encode_nop(state);
        case OPCODE_HLT:  return encode_hlt(state);
        case OPCODE_CLI:  return encode_cli(state);
        case OPCODE_STI:  return encode_sti(state);
        case OPCODE_RET:  return encode_ret(state);

        case OPCODE_CALL:
            if (instr->operands[0].type == OPERAND_LABEL)
                return encode_call_rel(state, 0); /* patched later */
            break;

        case OPCODE_JMP:
            if (instr->operands[0].type == OPERAND_LABEL)
                return encode_jmp_rel(state, 0); /* patched later */
            break;

        default:
            break;
    }
    return -1;
}

/* ---- Line parsing ---- */

static char* skip_whitespace(char* s) {
    while (*s == ' ' || *s == '\t') s++;
    return s;
}

static uint32_t parse_number(const char* str, int base) {
    uint32_t result = 0;
    while (*str) {
        char c = *str;
        if (c >= '0' && c <= '9') result = result * base + (c - '0');
        else if (c >= 'a' && c <= 'f') result = result * base + (c - 'a' + 10);
        else if (c >= 'A' && c <= 'F') result = result * base + (c - 'A' + 10);
        else break;
        str++;
    }
    return result;
}

int asm_parse_operand(const char* str, asm_operand_t* op) {
    if (!str || !op) return -1;
    memset(op, 0, sizeof(asm_operand_t));

    /* Check for register */
    asm_reg_t reg;
    if (asm_parse_reg(str, &reg) == 0) {
        op->type = OPERAND_REG;
        op->reg = reg;
        return 0;
    }

    /* Check for number */
    if (str[0] == '0' && str[1] == 'x') {
        op->type = OPERAND_IMM;
        op->imm = parse_number(str + 2, 16);
        return 0;
    }
    if (str[0] >= '0' && str[0] <= '9') {
        op->type = OPERAND_IMM;
        op->imm = parse_number(str, 10);
        return 0;
    }

    /* Check for memory [addr] */
    if (str[0] == '[') {
        str++;
        const char* end = str;
        while (*end && *end != ']') end++;
        char inner[64];
        uint32_t len = end - str;
        if (len >= 64) return -1;
        memcpy(inner, str, len);
        inner[len] = '\0';

        op->type = OPERAND_MEM;
        op->mem.size = 4;
        op->mem.base = REG_NONE;
        op->mem.offset = 0;

        /* Try parsing as number */
        if (inner[0] >= '0' && inner[0] <= '9') {
            op->mem.offset = parse_number(inner, inner[1] == 'x' ? 16 : 10);
            return 0;
        }

        /* Try parsing as [reg] */
        if (asm_parse_reg(inner, &reg) == 0) {
            op->mem.base = reg;
            return 0;
        }

        /* Try [reg+off] */
        char* plus = inner;
        while (*plus && *plus != '+') plus++;
        if (*plus == '+') {
            char reg_part[32];
            uint32_t plen = plus - inner;
            memcpy(reg_part, inner, plen);
            reg_part[plen] = '\0';
            if (asm_parse_reg(reg_part, &reg) == 0) {
                op->mem.base = reg;
                op->mem.offset = parse_number(plus + 1, plus[2] == 'x' ? 16 : 10);
                return 0;
            }
        }
        return -1;
    }

    /* Label */
    op->type = OPERAND_LABEL;
    op->label_id = 0;
    return 0;
}

int asm_parse_line(asm_state_t* state, const char* line) {
    if (!state || !line) return -1;

    char buf[ASM_MAX_LINE_LEN];
    string_copy(buf, line, ASM_MAX_LINE_LEN);
    char* ptr = skip_whitespace(buf);

    /* Skip empty lines and comments */
    if (*ptr == '\0' || *ptr == ';' || *ptr == '#') return 0;

    /* Check for label */
    char* colon = ptr;
    while (*colon && *colon != ':' && *colon != ' ') colon++;
    if (*colon == ':') {
        *colon = '\0';
        if (state->num_labels < ASM_MAX_LABELS) {
            string_copy(state->labels[state->num_labels].name, ptr, 64);
            state->labels[state->num_labels].address = state->current_address;
            state->labels[state->num_labels].defined = 1;
            state->num_labels++;
        }
        ptr = skip_whitespace(colon + 1);
    }
    if (*ptr == '\0') return 0;

    /* Parse opcode */
    char opcode_buf[32];
    uint32_t i = 0;
    while (ptr[i] && ptr[i] != ' ' && ptr[i] != '\t' && ptr[i] != ';' && i < 31)
        opcode_buf[i] = ptr[i++];
    opcode_buf[i] = '\0';

    asm_opcode_t opcode = asm_parse_opcode(opcode_buf);
    if (opcode == OPCODE_NOT_IMPL) {
        /* Check for data directives */
        if (string_compare(opcode_buf, "db") == 0 ||
            string_compare(opcode_buf, "dw") == 0 ||
            string_compare(opcode_buf, "dd") == 0 ||
            string_compare(opcode_buf, "resb") == 0 ||
            string_compare(opcode_buf, "resw") == 0 ||
            string_compare(opcode_buf, "resd") == 0) {
            ptr = skip_whitespace(ptr + i);
            uint32_t val = parse_number(ptr, ptr[0] == '0' && ptr[1] == 'x' ? 16 : 10);
            if (string_compare(opcode_buf, "db") == 0) {
                emit_byte(state, val & 0xFF);
                state->current_address++;
            } else if (string_compare(opcode_buf, "dw") == 0) {
                emit_word(state, val);
                state->current_address += 2;
            } else if (string_compare(opcode_buf, "dd") == 0) {
                emit_dword(state, val);
                state->current_address += 4;
            }
            return 0;
        }
        if (string_compare(opcode_buf, "bits") == 0) {
            ptr = skip_whitespace(ptr + i);
            state->bits = parse_number(ptr, 10);
            return 0;
        }
        if (string_compare(opcode_buf, "org") == 0) {
            ptr = skip_whitespace(ptr + i);
            state->current_address = parse_number(ptr, ptr[0] == '0' && ptr[1] == 'x' ? 16 : 10);
            return 0;
        }
        string_format(state->error_msg, "Unknown opcode: %s", opcode_buf);
        state->error = 1;
        return -1;
    }

    /* Parse operands */
    asm_instruction_t* instr = &state->instructions[state->num_instructions];
    memset(instr, 0, sizeof(asm_instruction_t));
    instr->opcode = opcode;
    instr->address = state->current_address;

    ptr = skip_whitespace(ptr + i);
    int op_count = 0;
    while (*ptr && *ptr != ';' && op_count < 3) {
        char op_buf[64];
        uint32_t j = 0;
        while (*ptr && *ptr != ',' && *ptr != ';' && j < 63)
            op_buf[j++] = *ptr++;
        op_buf[j] = '\0';

        /* Trim trailing spaces */
        int k = j - 1;
        while (k >= 0 && op_buf[k] == ' ') op_buf[k--] = '\0';

        if (op_buf[0] != '\0') {
            asm_operand_t* op = &instr->operands[op_count];
            if (asm_parse_operand(op_buf, op) == -1) {
                string_format(state->error_msg, "Invalid operand: %s", op_buf);
                state->error = 1;
                return -1;
            }
            op_count++;
        }
        if (*ptr == ',') ptr++;
        ptr = skip_whitespace(ptr);
    }

    state->num_instructions++;

    /* Estimate instruction size */
    uint8_t est = 1;
    if (op_count > 0 && instr->operands[0].type == OPERAND_IMM) est += 4;
    if (op_count > 1 && instr->operands[1].type == OPERAND_IMM) est += 4;
    state->current_address += est;

    return 0;
}

int asm_assemble(asm_state_t* state, const char* source) {
    if (!state || !source) return -1;

    asm_init(state);
    const char* line = source;
    int line_num = 1;

    while (*line) {
        /* Extract line */
        char buf[ASM_MAX_LINE_LEN];
        uint32_t i = 0;
        while (line[i] && line[i] != '\n' && i < ASM_MAX_LINE_LEN - 1)
            buf[i] = line[i++];
        buf[i] = '\0';
        line += i;
        if (*line == '\n') line++;

        if (asm_parse_line(state, buf) != 0) {
            string_format(state->error_msg + string_length(state->error_msg),
                          " at line %d", line_num);
            return -1;
        }
        line_num++;
    }

    return asm_resolve(state);
}

int asm_resolve(asm_state_t* state) {
    if (!state) return -1;

    /* Patch label references */
    for (uint32_t i = 0; i < state->num_instructions; i++) {
        asm_instruction_t* instr = &state->instructions[i];
        for (int j = 0; j < 3; j++) {
            if (instr->operands[j].type == OPERAND_LABEL) {
                /* Find label */
                for (uint32_t l = 0; l < state->num_labels; l++) {
                    if (string_compare(state->labels[l].name,
                                       state->labels[l].name) == 0) {
                        int32_t offset = (int32_t)state->labels[l].address -
                                         (int32_t)(instr->address + instr->size);
                        /* Patch the encoded instruction */
                        if (instr->opcode == OPCODE_JMP || instr->opcode == OPCODE_CALL) {
                            uint32_t patch_off = instr->size - 4;
                            state->code[instr->address + patch_off + 0] = offset & 0xFF;
                            state->code[instr->address + patch_off + 1] = (offset >> 8) & 0xFF;
                            state->code[instr->address + patch_off + 2] = (offset >> 16) & 0xFF;
                            state->code[instr->address + patch_off + 3] = (offset >> 24) & 0xFF;
                        }
                        break;
                    }
                }
            }
        }
    }
    return 0;
}

uint8_t* asm_get_code(asm_state_t* state) {
    return state ? state->code : NULL;
}

uint32_t asm_get_size(asm_state_t* state) {
    return state ? state->code_size : 0;
}

const char* asm_get_error(asm_state_t* state) {
    return state ? state->error_msg : "NULL state";
}
