#ifndef ARCANIS_GC_H
#define ARCANIS_GC_H

#include "memory.h"
#include "stack.h"

typedef struct GC {
    MemoryManager* mm;
    Stack* stack;
    struct Table* roots;
    uint32_t gcCount;
    uint32_t gcGeneration;
    bool gcEnabled;
    void (*gcCallback)(struct GC* gc, uint32_t freed, uint32_t remaining);
} GC;

typedef struct GCRoot {
    Value* location;
    struct GCRoot* next;
} GCRoot;

void initGC(GC* gc, MemoryManager* mm, Stack* stack);
void setGCStack(GC* gc, Stack* stack);
void addGCRoot(GC* gc, Value* location);
void removeGCRoot(GC* gc, Value* location);
void gcMarkRoots(GC* gc);
void gcMarkObject(GC* gc, Obj* obj);
void gcMarkValue(GC* gc, Value value);
void gcSweep(GC* gc);
void gcCollect(GC* gc);
void gcEnable(GC* gc);
void gcDisable(GC* gc);

#endif
