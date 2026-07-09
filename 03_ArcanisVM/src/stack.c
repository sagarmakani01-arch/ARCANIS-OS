#include "stack.h"
#include <stdlib.h>

void initStack(Stack* stack) {
    stack->slots = NULL;
    stack->stackTop = NULL;
    stack->capacity = 0;
}

void freeStack(Stack* stack) {
    free(stack->slots);
    stack->slots = NULL;
    stack->stackTop = NULL;
    stack->capacity = 0;
}

bool stackPush(Stack* stack, Value value) {
    uint32_t count = stackCount(stack);
    if (count >= STACK_MAX) return false;
    if (count >= stack->capacity) {
        uint32_t newCap = stack->capacity < 8 ? 8 : stack->capacity * 2;
        if (newCap > STACK_MAX) newCap = STACK_MAX;
        Value* newSlots = realloc(stack->slots, newCap * sizeof(Value));
        if (!newSlots) return false;
        uint32_t offset = stack->stackTop - stack->slots;
        stack->slots = newSlots;
        stack->stackTop = stack->slots + offset;
        stack->capacity = newCap;
    }
    *stack->stackTop = value;
    stack->stackTop++;
    return true;
}

Value stackPop(Stack* stack) {
    stack->stackTop--;
    return *stack->stackTop;
}

Value stackPeek(Stack* stack, uint32_t distance) {
    return stack->stackTop[-1 - distance];
}

bool stackSet(Stack* stack, uint32_t index, Value value) {
    if (index >= stackCount(stack)) return false;
    stack->slots[index] = value;
    return true;
}

Value stackGet(Stack* stack, uint32_t index) {
    return stack->slots[index];
}

void stackMark(Stack* stack) {
    for (Value* slot = stack->slots; slot < stack->stackTop; slot++) {
        if (slot->as.obj) slot->as.obj->isMarked = true;
    }
}

uint32_t stackCount(Stack* stack) {
    return (uint32_t)(stack->stackTop - stack->slots);
}
