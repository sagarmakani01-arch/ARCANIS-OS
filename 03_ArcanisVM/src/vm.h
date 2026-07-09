#ifndef ARCANIS_VM_H
#define ARCANIS_VM_H

#include "bytecode.h"
#include "stack.h"
#include "gc.h"
#include "value.h"

struct Debugger;
struct Profiler;
struct Sandbox;
struct PluginSystem;

typedef struct VM {
    Stack stack;
    CallFrame frames[FRAMES_MAX];
    uint32_t frameCount;
    MemoryManager memory;
    GC gc;
    ValueArray globals;
    struct Table* modules;
    ObjString* currentModule;
    ObjUpvalue* openUpvalues;
    uint32_t sandboxLevel;
    uint32_t profileDepth;
    bool runtimeError;
    char errorMessage[512];
    struct Debugger* debugger;
    struct Profiler* profiler;
    struct Sandbox* sandbox;
    struct PluginSystem* plugins;
} VM;

void initVM(VM* vm);
void freeVM(VM* vm);
ExecResult vmInterpret(VM* vm, ObjFunction* function);
ExecResult vmRun(VM* vm);
void vmPush(VM* vm, Value value);
Value vmPop(VM* vm);
Value vmPeek(VM* vm, uint32_t distance);
void vmRuntimeError(VM* vm, const char* format, ...);
bool vmIsFalsey(Value value);
void vmDefineNative(VM* vm, const char* name, NativeFn fn, void* context);

#endif
