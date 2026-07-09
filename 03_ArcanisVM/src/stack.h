#ifndef ARCANIS_STACK_H
#define ARCANIS_STACK_H

#include "value.h"
#include <stdint.h>

#define STACK_MAX 16384
#define FRAMES_MAX 1024

typedef struct {
    Value* slots;
    Value* stackTop;
    uint32_t capacity;
} Stack;

typedef struct {
    ObjClosure* closure;
    Value* slots;
    uint32_t ip;
    uint32_t depth;
} CallFrame;

void initStack(Stack* stack);
void freeStack(Stack* stack);
bool stackPush(Stack* stack, Value value);
Value stackPop(Stack* stack);
Value stackPeek(Stack* stack, uint32_t distance);
bool stackSet(Stack* stack, uint32_t index, Value value);
Value stackGet(Stack* stack, uint32_t index);
void stackMark(Stack* stack);
uint32_t stackCount(Stack* stack);

#endif
