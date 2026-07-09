/**
 * assembler.h — x86-16/32 Assembler
 *
 * Simple single-pass assembler for x86 instructions.
 * Supports most common integer, memory, and control flow instructions.
 */
#ifndef ARCANIS_ASSEMBLER_H
#define ARCANIS_ASSEMBLER_H

#include <arcanis/types.h>

#define ASM_MAX_CODE      65536
#define ASM_MAX_LABELS    1024
#define ASM_MAX_SYMBOLS   1024
#define ASM_MAX_LINE_LEN  256

typedef enum {
    /* Register types */
    REG_AL, REG_CL, REG_DL, REG_BL, REG_AH, REG_CH, REG_DH, REG_BH,
    REG_AX, REG_CX, REG_DX, REG_BX, REG_SP, REG_BP, REG_SI, REG_DI,
    REG_EAX, REG_ECX, REG_EDX, REG_EBX, REG_ESP, REG_EBP, REG_ESI, REG_EDI,
    /* Segment registers */
    REG_CS, REG_DS, REG_ES, REG_FS, REG_GS, REG_SS,
    /* Special */
    REG_NONE
} asm_reg_t;

typedef enum {
    OPCODE_MOV, OPCODE_ADD, OPCODE_SUB, OPCODE_MUL, OPCODE_DIV,
    OPCODE_AND, OPCODE_OR, OPCODE_XOR, OPCODE_NOT, OPCODE_SHL, OPCODE_SHR,
    OPCODE_CMP, OPCODE_TEST,
    OPCODE_JMP, OPCODE_JE, OPCODE_JNE, OPCODE_JG, OPCODE_JL, OPCODE_JGE, OPCODE_JLE,
    OPCODE_CALL, OPCODE_RET, OPCODE_PUSH, OPCODE_POP,
    OPCODE_INT, OPCODE_IRET,
    OPCODE_NOP, OPCODE_HLT, OPCODE_CLI, OPCODE_STI,
    OPCODE_INC, OPCODE_DEC,
    OPCODE_LEA, OPCODE_MOVSB, OPCODE_MOVSW, OPCODE_MOVSD,
    OPCODE_IN, OPCODE_OUT,
    OPCODE_CLD, OPCODE_STD,
    OPCODE_ENTER, OPCODE_LEAVE,
    OPCODE_NOT_IMPL
} asm_opcode_t;

typedef enum {
    OPERAND_NONE,
    OPERAND_REG,
    OPERAND_IMM,
    OPERAND_MEM,
    OPERAND_MEM_REG,
    OPERAND_LABEL
} asm_operand_type_t;

typedef struct {
    asm_operand_type_t type;
    union {
        asm_reg_t reg;
        uint32_t  imm;
        struct {
            asm_reg_t base;
            int32_t   offset;
            uint8_t   size; /* 1, 2, or 4 */
        } mem;
        uint32_t label_id;
    };
} asm_operand_t;

typedef struct {
    char     name[64];
    uint32_t address;
    int      defined;
} asm_label_t;

typedef struct {
    asm_opcode_t  opcode;
    asm_operand_t operands[3];
    uint32_t      address;
    uint8_t       size; /* instruction size in bytes */
    uint8_t       encoded[15];
} asm_instruction_t;

typedef struct {
    uint8_t              code[ASM_MAX_CODE];
    uint32_t             code_size;
    asm_instruction_t    instructions[4096];
    uint32_t             num_instructions;
    asm_label_t          labels[ASM_MAX_LABELS];
    uint32_t             num_labels;
    uint32_t             current_address;
    uint32_t             data_offset;
    int                  error;
    char                 error_msg[128];
    int                  bits; /* 16 or 32 */
} asm_state_t;

/* Initialize assembler */
void     asm_init(asm_state_t* state);

/* Parse and assemble a single line */
int      asm_parse_line(asm_state_t* state, const char* line);

/* Assemble multiple lines */
int      asm_assemble(asm_state_t* state, const char* source);

/* Resolve labels and patch jumps */
int      asm_resolve(asm_state_t* state);

/* Get generated code */
uint8_t* asm_get_code(asm_state_t* state);
uint32_t asm_get_size(asm_state_t* state);

/* Encode individual instructions */
int      asm_encode_instruction(asm_instruction_t* instr, asm_state_t* state);

/* Register encoding */
int      asm_parse_reg(const char* name, asm_reg_t* reg);
uint8_t  asm_reg_encoding(asm_reg_t reg);
uint8_t  asm_reg_size(asm_reg_t reg);

/* Operand parsing */
int      asm_parse_operand(const char* str, asm_operand_t* op);

/* Opcodes */
asm_opcode_t asm_parse_opcode(const char* name);

/* Error handling */
const char* asm_get_error(asm_state_t* state);

#endif
