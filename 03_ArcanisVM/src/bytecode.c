#include "bytecode.h"
#include <stdlib.h>

void initChunk(BytecodeChunk* chunk) {
    chunk->bytecode = NULL;
    chunk->capacity = 0;
    chunk->count = 0;
    initValueArray(&chunk->constants);
    chunk->lines = NULL;
    chunk->lineCapacity = 0;
    chunk->lineCount = 0;
}

void freeChunk(BytecodeChunk* chunk) {
    free(chunk->bytecode);
    free(chunk->lines);
    freeValueArray(&chunk->constants);
    chunk->bytecode = NULL;
    chunk->capacity = 0;
    chunk->count = 0;
    chunk->lineCapacity = 0;
    chunk->lineCount = 0;
}

void writeChunk(BytecodeChunk* chunk, uint32_t instruction, uint32_t line) {
    if (chunk->capacity < chunk->count + 1) {
        uint32_t old = chunk->capacity;
        chunk->capacity = old < 8 ? 8 : old * 2;
        chunk->bytecode = realloc(chunk->bytecode, chunk->capacity * sizeof(uint32_t));
    }
    chunk->bytecode[chunk->count++] = instruction;
    if (chunk->lineCapacity < chunk->lineCount + 1) {
        uint32_t old = chunk->lineCapacity;
        chunk->lineCapacity = old < 8 ? 8 : old * 2;
        chunk->lines = realloc(chunk->lines, chunk->lineCapacity * sizeof(uint32_t));
    }
    chunk->lines[chunk->lineCount++] = line;
}

uint32_t addConstant(BytecodeChunk* chunk, Value value) {
    writeValueArray(&chunk->constants, value);
    return chunk->constants.count - 1;
}

uint32_t getLine(BytecodeChunk* chunk, uint32_t offset) {
    if (offset < chunk->lineCount) return chunk->lines[offset];
    return 0;
}

static const char* opName(uint32_t op) {
    switch (op) {
        case OP_HALT: return "OP_HALT";
        case OP_NOP: return "OP_NOP";
        case OP_LOAD_CONST: return "OP_LOAD_CONST";
        case OP_LOAD_NIL: return "OP_LOAD_NIL";
        case OP_LOAD_TRUE: return "OP_LOAD_TRUE";
        case OP_LOAD_FALSE: return "OP_LOAD_FALSE";
        case OP_LOAD_INT_0: return "OP_LOAD_INT_0";
        case OP_LOAD_INT_1: return "OP_LOAD_INT_1";
        case OP_LOAD_LOCAL: return "OP_LOAD_LOCAL";
        case OP_STORE_LOCAL: return "OP_STORE_LOCAL";
        case OP_LOAD_GLOBAL: return "OP_LOAD_GLOBAL";
        case OP_STORE_GLOBAL: return "OP_STORE_GLOBAL";
        case OP_LOAD_UPVALUE: return "OP_LOAD_UPVALUE";
        case OP_STORE_UPVALUE: return "OP_STORE_UPVALUE";
        case OP_LOAD_MODULE: return "OP_LOAD_MODULE";
        case OP_STORE_MODULE: return "OP_STORE_MODULE";
        case OP_ADD: return "OP_ADD";
        case OP_SUB: return "OP_SUB";
        case OP_MUL: return "OP_MUL";
        case OP_DIV: return "OP_DIV";
        case OP_MOD: return "OP_MOD";
        case OP_NEG: return "OP_NEG";
        case OP_EQ: return "OP_EQ";
        case OP_NE: return "OP_NE";
        case OP_LT: return "OP_LT";
        case OP_GT: return "OP_GT";
        case OP_LE: return "OP_LE";
        case OP_GE: return "OP_GE";
        case OP_AND: return "OP_AND";
        case OP_OR: return "OP_OR";
        case OP_NOT: return "OP_NOT";
        case OP_JMP: return "OP_JMP";
        case OP_JMP_IF_FALSE: return "OP_JMP_IF_FALSE";
        case OP_JMP_IF_TRUE: return "OP_JMP_IF_TRUE";
        case OP_JMP_IF_FALSE_POP: return "OP_JMP_IF_FALSE_POP";
        case OP_LOOP: return "OP_LOOP";
        case OP_CALL: return "OP_CALL";
        case OP_CALL_TAIL: return "OP_CALL_TAIL";
        case OP_RETURN: return "OP_RETURN";
        case OP_RETURN_VALUE: return "OP_RETURN_VALUE";
        case OP_CLOSURE: return "OP_CLOSURE";
        case OP_CLOSE_UPVALUE: return "OP_CLOSE_UPVALUE";
        case OP_NEW_ARRAY: return "OP_NEW_ARRAY";
        case OP_NEW_MAP: return "OP_NEW_MAP";
        case OP_INDEX_GET: return "OP_INDEX_GET";
        case OP_INDEX_SET: return "OP_INDEX_SET";
        case OP_NEW_OBJECT: return "OP_NEW_OBJECT";
        case OP_PROP_GET: return "OP_PROP_GET";
        case OP_PROP_SET: return "OP_PROP_SET";
        case OP_METHOD: return "OP_METHOD";
        case OP_INVOKE: return "OP_INVOKE";
        case OP_INHERIT: return "OP_INHERIT";
        case OP_GET_SUPER: return "OP_GET_SUPER";
        case OP_SCOPE_ENTER: return "OP_SCOPE_ENTER";
        case OP_SCOPE_EXIT: return "OP_SCOPE_EXIT";
        case OP_DEFINE_GLOBAL: return "OP_DEFINE_GLOBAL";
        case OP_POP: return "OP_POP";
        case OP_DUP: return "OP_DUP";
        case OP_SWAP: return "OP_SWAP";
        case OP_BUILD_STRING: return "OP_BUILD_STRING";
        case OP_IMPORT: return "OP_IMPORT";
        case OP_EXPORT: return "OP_EXPORT";
        case OP_DEBUG_BREAK: return "OP_DEBUG_BREAK";
        case OP_PROFILE_START: return "OP_PROFILE_START";
        case OP_PROFILE_END: return "OP_PROFILE_END";
        case OP_SANDBOX_ENTER: return "OP_SANDBOX_ENTER";
        case OP_SANDBOX_EXIT: return "OP_SANDBOX_EXIT";
        default: return "UNKNOWN";
    }
}

static uint32_t simpleInstruction(const char* name, uint32_t offset) {
    printf("%s\n", name);
    return offset + 1;
}

static uint32_t constantInstruction(const char* name, BytecodeChunk* chunk, uint32_t offset) {
    uint32_t constant = chunk->bytecode[offset + 1];
    printf("%-16s %4d '", name, constant);
    printValue(stdout, chunk->constants.values[constant]);
    printf("'\n");
    return offset + 2;
}

static uint32_t byteInstruction(const char* name, BytecodeChunk* chunk, uint32_t offset) {
    uint32_t slot = chunk->bytecode[offset + 1];
    printf("%-16s %4d\n", name, slot);
    return offset + 2;
}

static uint32_t jumpInstruction(const char* name, int sign, BytecodeChunk* chunk, uint32_t offset) {
    uint32_t jump = chunk->bytecode[offset + 1];
    printf("%-16s %4d -> %d\n", name, jump, offset + 3 + sign * (int)jump);
    return offset + 2;
}

void disassembleChunk(BytecodeChunk* chunk, const char* name) {
    printf("== %s ==\n", name);
    for (uint32_t offset = 0; offset < chunk->count;) {
        offset = disassembleInstruction(chunk, offset);
    }
}

uint32_t disassembleInstruction(BytecodeChunk* chunk, uint32_t offset) {
    printf("%04d ", offset);
    if (offset > 0 && getLine(chunk, offset) == getLine(chunk, offset - 1))
        printf("   | ");
    else
        printf("%4d ", getLine(chunk, offset));
    uint32_t instruction = chunk->bytecode[offset];
    uint32_t op = getOp(instruction);
    uint32_t arg = getArg(instruction);
    switch (op) {
        case OP_HALT:
        case OP_NOP:
        case OP_LOAD_NIL:
        case OP_LOAD_TRUE:
        case OP_LOAD_FALSE:
        case OP_LOAD_INT_0:
        case OP_LOAD_INT_1:
        case OP_ADD:
        case OP_SUB:
        case OP_MUL:
        case OP_DIV:
        case OP_MOD:
        case OP_NEG:
        case OP_EQ:
        case OP_NE:
        case OP_LT:
        case OP_GT:
        case OP_LE:
        case OP_GE:
        case OP_AND:
        case OP_OR:
        case OP_NOT:
        case OP_RETURN:
        case OP_RETURN_VALUE:
        case OP_CLOSE_UPVALUE:
        case OP_NEW_ARRAY:
        case OP_NEW_MAP:
        case OP_INDEX_GET:
        case OP_POP:
        case OP_DUP:
        case OP_SWAP:
        case OP_SCOPE_ENTER:
        case OP_SCOPE_EXIT:
        case OP_DEBUG_BREAK:
        case OP_PROFILE_START:
        case OP_PROFILE_END:
        case OP_SANDBOX_ENTER:
        case OP_SANDBOX_EXIT:
            return simpleInstruction(opName(op), offset);
        case OP_LOAD_CONST:
        case OP_IMPORT:
            return constantInstruction(opName(op), chunk, offset);
        case OP_LOAD_LOCAL:
        case OP_STORE_LOCAL:
        case OP_LOAD_GLOBAL:
        case OP_STORE_GLOBAL:
        case OP_LOAD_UPVALUE:
        case OP_STORE_UPVALUE:
        case OP_LOAD_MODULE:
        case OP_STORE_MODULE:
        case OP_CALL:
        case OP_CALL_TAIL:
        case OP_CLOSURE:
        case OP_DEFINE_GLOBAL:
        case OP_EXPORT:
        case OP_BUILD_STRING:
        case OP_PROP_GET:
        case OP_PROP_SET:
        case OP_NEW_OBJECT:
        case OP_INDEX_SET:
        case OP_METHOD:
        case OP_INVOKE:
        case OP_GET_SUPER:
            return byteInstruction(opName(op), chunk, offset);
        case OP_JMP:
        case OP_LOOP:
            return jumpInstruction(opName(op), op == OP_LOOP ? -1 : 1, chunk, offset);
        case OP_JMP_IF_FALSE:
        case OP_JMP_IF_TRUE:
        case OP_JMP_IF_FALSE_POP:
            return jumpInstruction(opName(op), 1, chunk, offset);
        default:
            printf("Unknown opcode %d\n", op);
            return offset + 1;
    }
}
