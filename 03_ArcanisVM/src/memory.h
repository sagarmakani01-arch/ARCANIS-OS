#ifndef ARCANIS_MEMORY_H
#define ARCANIS_MEMORY_H

#include "value.h"
#include <stddef.h>

typedef struct Allocator {
    void* (*alloc)(void* ctx, size_t size);
    void* (*reallocFn)(void* ctx, void* ptr, size_t oldSize, size_t newSize);
    void (*freeFn)(void* ctx, void* ptr);
    void* context;
} Allocator;

typedef struct MemoryManager {
    Allocator allocator;
    Obj* objects;
    uint32_t bytesAllocated;
    uint32_t nextGC;
    uint32_t gcThreshold;
    uint32_t numObjects;
} MemoryManager;

void initMemoryManager(MemoryManager* mm, Allocator allocator);
void* allocateObject(MemoryManager* mm, size_t size);
void freeObject(MemoryManager* mm, Obj* obj);
void freeAllObjects(MemoryManager* mm);

ObjString* allocateString(MemoryManager* mm, const char* chars, uint32_t length);
ObjString* copyString(MemoryManager* mm, const char* chars, uint32_t length);
ObjArray* allocateArray(MemoryManager* mm);
ObjMap* allocateMap(MemoryManager* mm);
ObjFunction* allocateFunction(MemoryManager* mm);
ObjNative* allocateNative(MemoryManager* mm, NativeFn fn, void* context);
ObjClosure* allocateClosure(MemoryManager* mm, ObjFunction* function);
ObjUpvalue* allocateUpvalue(MemoryManager* mm, Value* location);
ObjBoundMethod* allocateBoundMethod(MemoryManager* mm, Value receiver, ObjClosure* method);
ObjClass* allocateClass(MemoryManager* mm, ObjString* name);
ObjInstance* allocateInstance(MemoryManager* mm, ObjClass* klass);
ObjModule* allocateModule(MemoryManager* mm, ObjString* name);
ObjForeign* allocateForeign(MemoryManager* mm, void* data, void (*destructor)(void*));

void markObject(MemoryManager* mm, Obj* obj);
void markValue(MemoryManager* mm, Value value);

#endif
