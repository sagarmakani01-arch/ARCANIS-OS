#ifndef ARCANIS_BYTECODE_H
#define ARCANIS_BYTECODE_H

#include "value.h"
#include <stdint.h>

typedef enum {
    OP_HALT,
    OP_NOP,
    OP_LOAD_CONST,
    OP_LOAD_NIL,
    OP_LOAD_TRUE,
    OP_LOAD_FALSE,
    OP_LOAD_INT_0,
    OP_LOAD_INT_1,
    OP_LOAD_LOCAL,
    OP_STORE_LOCAL,
    OP_LOAD_GLOBAL,
    OP_STORE_GLOBAL,
    OP_LOAD_UPVALUE,
    OP_STORE_UPVALUE,
    OP_LOAD_MODULE,
    OP_STORE_MODULE,
    OP_ADD,
    OP_SUB,
    OP_MUL,
    OP_DIV,
    OP_MOD,
    OP_NEG,
    OP_EQ,
    OP_NE,
    OP_LT,
    OP_GT,
    OP_LE,
    OP_GE,
    OP_AND,
    OP_OR,
    OP_NOT,
    OP_JMP,
    OP_JMP_IF_FALSE,
    OP_JMP_IF_TRUE,
    OP_JMP_IF_FALSE_POP,
    OP_LOOP,
    OP_CALL,
    OP_CALL_TAIL,
    OP_RETURN,
    OP_RETURN_VALUE,
    OP_CLOSURE,
    OP_CLOSE_UPVALUE,
    OP_NEW_ARRAY,
    OP_NEW_MAP,
    OP_INDEX_GET,
    OP_INDEX_SET,
    OP_NEW_OBJECT,
    OP_PROP_GET,
    OP_PROP_SET,
    OP_METHOD,
    OP_INVOKE,
    OP_INHERIT,
    OP_GET_SUPER,
    OP_SCOPE_ENTER,
    OP_SCOPE_EXIT,
    OP_DEFINE_GLOBAL,
    OP_POP,
    OP_DUP,
    OP_SWAP,
    OP_BUILD_STRING,
    OP_IMPORT,
    OP_EXPORT,
    OP_DEBUG_BREAK,
    OP_PROFILE_START,
    OP_PROFILE_END,
    OP_SANDBOX_ENTER,
    OP_SANDBOX_EXIT,
} OpCode;

typedef enum {
    EXEC_OK,
    EXEC_RUNTIME_ERROR,
    EXEC_HALTED,
    EXEC_DEBUG_BREAK,
    EXEC_SANDBOX_VIOLATION,
    EXEC_STACK_OVERFLOW,
    EXEC_OUT_OF_MEMORY,
} ExecResult;

typedef struct {
    uint32_t* bytecode;
    uint32_t capacity;
    uint32_t count;
    ValueArray constants;
    uint32_t* lines;
    uint32_t lineCapacity;
    uint32_t lineCount;
} BytecodeChunk;

void initChunk(BytecodeChunk* chunk);
void freeChunk(BytecodeChunk* chunk);
void writeChunk(BytecodeChunk* chunk, uint32_t instruction, uint32_t line);
uint32_t addConstant(BytecodeChunk* chunk, Value value);
uint32_t getLine(BytecodeChunk* chunk, uint32_t offset);
void disassembleChunk(BytecodeChunk* chunk, const char* name);
uint32_t disassembleInstruction(BytecodeChunk* chunk, uint32_t offset);

static inline uint32_t makeOp(uint32_t op, uint32_t arg) { return (op & 0xFF) | (arg << 8); }
static inline uint32_t getOp(uint32_t instr) { return instr & 0xFF; }
static inline uint32_t getArg(uint32_t instr) { return instr >> 8; }

#endif
