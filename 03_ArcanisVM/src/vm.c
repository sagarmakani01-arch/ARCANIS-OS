#include "vm.h"
#include "runtime.h"
#include "debugger.h"
#include "profiler.h"
#include "sandbox.h"
#include "plugin.h"
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

void initVM(VM* vm) {
    memset(vm, 0, sizeof(VM));
    initStack(&vm->stack);
    vm->globals.values = NULL;
    vm->globals.capacity = 0;
    vm->globals.count = 0;
    vm->modules = NULL;
    vm->currentModule = NULL;
    vm->openUpvalues = NULL;
    vm->sandboxLevel = 0;
    vm->profileDepth = 0;
    vm->runtimeError = false;
    vm->errorMessage[0] = '\0';
    vm->debugger = NULL;
    vm->profiler = NULL;
    vm->sandbox = NULL;
    vm->plugins = NULL;
    {
        Allocator a = { NULL, NULL, NULL, NULL };
        initMemoryManager(&vm->memory, a);
    }
    initGC(&vm->gc, &vm->memory, &vm->stack);
    initRuntime(vm);
}

void freeVM(VM* vm) {
    vm->openUpvalues = NULL;
    if (vm->modules) { freeTable(vm->modules); free(vm->modules); vm->modules = NULL; }
    freeValueArray(&vm->globals);
    freeStack(&vm->stack);
    freeAllObjects(&vm->memory);
}

void vmPush(VM* vm, Value value) {
    stackPush(&vm->stack, value);
}

Value vmPop(VM* vm) {
    return stackPop(&vm->stack);
}

Value vmPeek(VM* vm, uint32_t distance) {
    return stackPeek(&vm->stack, distance);
}

bool vmIsFalsey(Value value) {
    switch (value.type) {
        case VAL_NIL: return true;
        case VAL_BOOL: return !AS_BOOL(value);
        case VAL_INT: return AS_INT(value) == 0;
        case VAL_FLOAT: return AS_FLOAT(value) == 0.0;
        default: return false;
    }
}

void vmRuntimeError(VM* vm, const char* format, ...) {
    va_list args;
    va_start(args, format);
    vsnprintf(vm->errorMessage, sizeof(vm->errorMessage), format, args);
    va_end(args);
    vm->runtimeError = true;
    fprintf(stderr, "Runtime Error: %s\n", vm->errorMessage);
    if (vm->frameCount > 0) {
        CallFrame* frame = &vm->frames[vm->frameCount - 1];
        if (frame->closure && frame->closure->function) {
            ObjFunction* f = frame->closure->function;
            uint32_t line = 0;
            if (frame->ip > 1 && f->lines && (frame->ip - 1) < f->lineCount)
                line = f->lines[frame->ip - 1];
            fprintf(stderr, "[line %d in ", line);
            if (f->name) fprintf(stderr, "%s", f->name->chars);
            else fprintf(stderr, "script");
            fprintf(stderr, "]\n");
        }
    }
}

static ObjUpvalue* captureUpvalue(VM* vm, Value* location) {
    ObjUpvalue* prev = NULL;
    ObjUpvalue* up = vm->openUpvalues;
    while (up && up->location > location) {
        prev = up;
        up = up->next;
    }
    if (up && up->location == location) return up;
    ObjUpvalue* created = allocateUpvalue(&vm->memory, location);
    created->next = up;
    if (prev == NULL) vm->openUpvalues = created;
    else prev->next = created;
    return created;
}

static void closeUpvalues(VM* vm, Value* last) {
    while (vm->openUpvalues && vm->openUpvalues->location >= last) {
        ObjUpvalue* up = vm->openUpvalues;
        up->closed = *up->location;
        up->location = &up->closed;
        vm->openUpvalues = up->next;
    }
}

void vmDefineNative(VM* vm, const char* name, NativeFn fn, void* context) {
    ObjString* str = copyString(&vm->memory, name, (uint32_t)strlen(name));
    ObjNative* native = allocateNative(&vm->memory, fn, context);
    native->name = str;
    while ((uint32_t)vm->globals.count <= (uint32_t)(uintptr_t)str) {
        writeValueArray(&vm->globals, NIL_VAL);
    }
    if (!vm->modules) {
        vm->modules = malloc(sizeof(struct Table));
        initTable(vm->modules);
    }
    tableSet(vm->modules, STRING_VAL(str), NATIVE_VAL(native));
}

static inline ObjFunction* getFrameFunction(CallFrame* frame) {
    return frame->closure->function;
}

ExecResult vmInterpret(VM* vm, ObjFunction* function) {
    ObjClosure* closure = allocateClosure(&vm->memory, function);
    if (!closure) return EXEC_OUT_OF_MEMORY;
    vmPush(vm, CLOSURE_VAL(closure));
    if (vm->frameCount < FRAMES_MAX) {
        CallFrame* frame = &vm->frames[vm->frameCount++];
        frame->closure = closure;
        frame->ip = 0;
        frame->slots = vm->stack.stackTop - 1;
        frame->depth = vm->frameCount - 1;
    } else {
        vmRuntimeError(vm, "Call stack overflow");
        return EXEC_STACK_OVERFLOW;
    }
    return vmRun(vm);
}

ExecResult vmRun(VM* vm) {
    CallFrame* frame = &vm->frames[vm->frameCount - 1];

    for (;;) {
        if (vm->debugger) {
            CheckResult cr = debuggerCheck(vm->debugger, vm);
            if (cr == CHECK_BREAK) {
                ExecResult dr = debuggerBreak(vm->debugger, vm);
                if (dr != EXEC_OK) return dr;
            } else if (cr == CHECK_ERROR) {
                return EXEC_RUNTIME_ERROR;
            }
        }

        ObjFunction* fn = getFrameFunction(frame);
        if (frame->ip >= fn->bytecodeLen) return EXEC_HALTED;

        uint32_t instruction = fn->bytecode[frame->ip++];
        uint32_t op = getOp(instruction);
        uint32_t arg = getArg(instruction);

        if (vm->profiler) {
            profilerTick(vm->profiler, vm, op);
        }

        if (vm->sandbox && vm->sandboxLevel > 0) {
            if (!sandboxCheck(vm->sandbox, vm, op)) {
                vmRuntimeError(vm, "Sandbox violation: opcode %d not allowed", op);
                return EXEC_SANDBOX_VIOLATION;
            }
        }

        switch (op) {
            case OP_HALT: return EXEC_HALTED;
            case OP_NOP: break;

            case OP_LOAD_CONST:
                vmPush(vm, fn->constants.values[arg]);
                break;

            case OP_LOAD_NIL: vmPush(vm, NIL_VAL); break;
            case OP_LOAD_TRUE: vmPush(vm, BOOL_VAL(true)); break;
            case OP_LOAD_FALSE: vmPush(vm, BOOL_VAL(false)); break;
            case OP_LOAD_INT_0: vmPush(vm, INT_VAL(0)); break;
            case OP_LOAD_INT_1: vmPush(vm, INT_VAL(1)); break;

            case OP_LOAD_LOCAL:
                vmPush(vm, frame->slots[arg]);
                break;

            case OP_STORE_LOCAL:
                frame->slots[arg] = vmPeek(vm, 0);
                break;

            case OP_LOAD_GLOBAL:
                if (arg < vm->globals.count) {
                    vmPush(vm, vm->globals.values[arg]);
                } else {
                    vmRuntimeError(vm, "Undefined global variable");
                    return EXEC_RUNTIME_ERROR;
                }
                break;

            case OP_STORE_GLOBAL:
                if (arg < vm->globals.count) {
                    vm->globals.values[arg] = vmPeek(vm, 0);
                } else {
                    vmRuntimeError(vm, "Undefined global variable");
                    return EXEC_RUNTIME_ERROR;
                }
                break;

            case OP_DEFINE_GLOBAL:
                while ((uint32_t)vm->globals.count <= arg)
                    writeValueArray(&vm->globals, NIL_VAL);
                vm->globals.values[arg] = vmPeek(vm, 0);
                vmPop(vm);
                break;

            case OP_LOAD_UPVALUE:
                vmPush(vm, *frame->closure->upvalues[arg]->location);
                break;

            case OP_STORE_UPVALUE:
                *frame->closure->upvalues[arg]->location = vmPeek(vm, 0);
                break;

            case OP_LOAD_MODULE: {
                if (vm->modules) {
                    Value result;
                    if (tableGet(vm->modules, fn->constants.values[arg], &result))
                        vmPush(vm, result);
                    else {
                        vmRuntimeError(vm, "Module not found");
                        return EXEC_RUNTIME_ERROR;
                    }
                } else {
                    vmRuntimeError(vm, "No modules loaded");
                    return EXEC_RUNTIME_ERROR;
                }
                break;
            }

            case OP_STORE_MODULE:
                if (vm->modules)
                    tableSet(vm->modules, fn->constants.values[arg], vmPeek(vm, 0));
                vmPop(vm);
                break;

            case OP_ADD: {
                Value b = vmPop(vm); Value a = vmPop(vm);
                if (IS_INT(a) && IS_INT(b)) vmPush(vm, INT_VAL(AS_INT(a) + AS_INT(b)));
                else if (IS_NUMBER(a) && IS_NUMBER(b)) vmPush(vm, FLOAT_VAL(AS_NUMBER(a) + AS_NUMBER(b)));
                else if (IS_STRING(a) && IS_STRING(b)) {
                    ObjString* sa = AS_STRING(a); ObjString* sb = AS_STRING(b);
                    uint32_t len = sa->length + sb->length;
                    char* chars = malloc(len + 1);
                    memcpy(chars, sa->chars, sa->length);
                    memcpy(chars + sa->length, sb->chars, sb->length);
                    chars[len] = '\0';
                    ObjString* result = allocateString(&vm->memory, chars, len);
                    free(chars);
                    vmPush(vm, STRING_VAL(result));
                } else { vmRuntimeError(vm, "Operands must be numbers or strings for +"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_SUB: {
                Value b = vmPop(vm); Value a = vmPop(vm);
                if (IS_INT(a) && IS_INT(b)) vmPush(vm, INT_VAL(AS_INT(a) - AS_INT(b)));
                else if (IS_NUMBER(a) && IS_NUMBER(b)) vmPush(vm, FLOAT_VAL(AS_NUMBER(a) - AS_NUMBER(b)));
                else { vmRuntimeError(vm, "Operands must be numbers for -"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_MUL: {
                Value b = vmPop(vm); Value a = vmPop(vm);
                if (IS_INT(a) && IS_INT(b)) vmPush(vm, INT_VAL(AS_INT(a) * AS_INT(b)));
                else if (IS_NUMBER(a) && IS_NUMBER(b)) vmPush(vm, FLOAT_VAL(AS_NUMBER(a) * AS_NUMBER(b)));
                else { vmRuntimeError(vm, "Operands must be numbers for *"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_DIV: {
                Value b = vmPop(vm); Value a = vmPop(vm);
                if (IS_NUMBER(a) && IS_NUMBER(b)) {
                    double db = AS_NUMBER(b);
                    if (db == 0.0) { vmRuntimeError(vm, "Division by zero"); return EXEC_RUNTIME_ERROR; }
                    vmPush(vm, FLOAT_VAL(AS_NUMBER(a) / db));
                } else { vmRuntimeError(vm, "Operands must be numbers for /"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_MOD: {
                Value b = vmPop(vm); Value a = vmPop(vm);
                if (IS_INT(a) && IS_INT(b)) {
                    if (AS_INT(b) == 0) { vmRuntimeError(vm, "Division by zero"); return EXEC_RUNTIME_ERROR; }
                    vmPush(vm, INT_VAL(AS_INT(a) % AS_INT(b)));
                } else { vmRuntimeError(vm, "Operands must be integers for %%"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_NEG: {
                Value a = vmPop(vm);
                if (IS_INT(a)) vmPush(vm, INT_VAL(-AS_INT(a)));
                else if (IS_FLOAT(a)) vmPush(vm, FLOAT_VAL(-AS_FLOAT(a)));
                else { vmRuntimeError(vm, "Operand must be a number for negation"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_EQ: { Value b = vmPop(vm); Value a = vmPop(vm); vmPush(vm, BOOL_VAL(valuesEqual(a, b))); break; }
            case OP_NE: { Value b = vmPop(vm); Value a = vmPop(vm); vmPush(vm, BOOL_VAL(!valuesEqual(a, b))); break; }

            case OP_LT: {
                Value b = vmPop(vm); Value a = vmPop(vm);
                if (IS_INT(a) && IS_INT(b)) vmPush(vm, BOOL_VAL(AS_INT(a) < AS_INT(b)));
                else if (IS_NUMBER(a) && IS_NUMBER(b)) vmPush(vm, BOOL_VAL(AS_NUMBER(a) < AS_NUMBER(b)));
                else { vmRuntimeError(vm, "Operands must be numbers for <"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_GT: {
                Value b = vmPop(vm); Value a = vmPop(vm);
                if (IS_INT(a) && IS_INT(b)) vmPush(vm, BOOL_VAL(AS_INT(a) > AS_INT(b)));
                else if (IS_NUMBER(a) && IS_NUMBER(b)) vmPush(vm, BOOL_VAL(AS_NUMBER(a) > AS_NUMBER(b)));
                else { vmRuntimeError(vm, "Operands must be numbers for >"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_LE: {
                Value b = vmPop(vm); Value a = vmPop(vm);
                if (IS_INT(a) && IS_INT(b)) vmPush(vm, BOOL_VAL(AS_INT(a) <= AS_INT(b)));
                else if (IS_NUMBER(a) && IS_NUMBER(b)) vmPush(vm, BOOL_VAL(AS_NUMBER(a) <= AS_NUMBER(b)));
                else { vmRuntimeError(vm, "Operands must be numbers for <="); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_GE: {
                Value b = vmPop(vm); Value a = vmPop(vm);
                if (IS_INT(a) && IS_INT(b)) vmPush(vm, BOOL_VAL(AS_INT(a) >= AS_INT(b)));
                else if (IS_NUMBER(a) && IS_NUMBER(b)) vmPush(vm, BOOL_VAL(AS_NUMBER(a) >= AS_NUMBER(b)));
                else { vmRuntimeError(vm, "Operands must be numbers for >="); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_NOT: { Value a = vmPop(vm); vmPush(vm, BOOL_VAL(vmIsFalsey(a))); break; }

            case OP_AND: {
                Value a = vmPop(vm);
                if (vmIsFalsey(a)) vmPush(vm, BOOL_VAL(false));
                else { Value b = vmPop(vm); vmPush(vm, b); }
                break;
            }

            case OP_OR: {
                Value a = vmPop(vm);
                if (!vmIsFalsey(a)) vmPush(vm, a);
                else { Value b = vmPop(vm); vmPush(vm, b); }
                break;
            }

            case OP_JMP: frame->ip += arg; break;
            case OP_JMP_IF_FALSE: if (vmIsFalsey(vmPeek(vm, 0))) frame->ip += arg; break;
            case OP_JMP_IF_TRUE: if (!vmIsFalsey(vmPeek(vm, 0))) frame->ip += arg; break;
            case OP_JMP_IF_FALSE_POP: { Value val = vmPop(vm); if (vmIsFalsey(val)) frame->ip += arg; } break;
            case OP_LOOP: frame->ip -= arg; break;

            case OP_CALL: {
                Value callee = vmPeek(vm, arg);
                if (IS_CLOSURE(callee)) {
                    ObjClosure* closure = AS_CLOSURE(callee);
                    if (vm->frameCount >= FRAMES_MAX) {
                        vmRuntimeError(vm, "Call stack overflow");
                        return EXEC_STACK_OVERFLOW;
                    }
                    CallFrame* newFrame = &vm->frames[vm->frameCount++];
                    newFrame->closure = closure;
                    newFrame->ip = 0;
                    newFrame->slots = vm->stack.stackTop - arg - 1;
                    newFrame->depth = vm->frameCount - 1;
                    frame = newFrame;
                } else if (IS_NATIVE(callee)) {
                    ObjNative* native = AS_NATIVE(callee);
                    Value* args = vm->stack.stackTop - arg;
                    Value result = native->function((int)arg, args, native->context);
                    vm->stack.stackTop -= arg + 1;
                    vmPush(vm, result);
                } else if (IS_BOUND_METHOD(callee)) {
                    ObjBoundMethod* bm = AS_BOUND_METHOD(callee);
                    vm->stack.stackTop[-arg - 1] = bm->receiver;
                    if (vm->frameCount >= FRAMES_MAX) {
                        vmRuntimeError(vm, "Call stack overflow");
                        return EXEC_STACK_OVERFLOW;
                    }
                    CallFrame* newFrame = &vm->frames[vm->frameCount++];
                    newFrame->closure = bm->method;
                    newFrame->ip = 0;
                    newFrame->slots = vm->stack.stackTop - arg - 1;
                    newFrame->depth = vm->frameCount - 1;
                    frame = newFrame;
                } else if (IS_CLASS(callee)) {
                    ObjClass* klass = AS_CLASS(callee);
                    ObjInstance* inst = allocateInstance(&vm->memory, klass);
                    if (!inst) return EXEC_OUT_OF_MEMORY;
                    vm->stack.stackTop[-arg - 1] = INSTANCE_VAL(inst);
                    Value init;
                    struct Table* tbl = klass->methods;
                    if (tbl) {
                        ObjString* initName = copyString(&vm->memory, "init", 4);
                        if (tableGet(tbl, STRING_VAL(initName), &init) && IS_CLOSURE(init)) {
                            ObjClosure* initCl = AS_CLOSURE(init);
                            if (vm->frameCount >= FRAMES_MAX) {
                                vmRuntimeError(vm, "Call stack overflow");
                                return EXEC_STACK_OVERFLOW;
                            }
                            CallFrame* newFrame = &vm->frames[vm->frameCount++];
                            newFrame->closure = initCl;
                            newFrame->ip = 0;
                            newFrame->slots = vm->stack.stackTop - arg - 1;
                            newFrame->depth = vm->frameCount - 1;
                            frame = newFrame;
                        }
                    }
                } else {
                    vmRuntimeError(vm, "Can only call functions and classes");
                    return EXEC_RUNTIME_ERROR;
                }
                break;
            }

            case OP_CALL_TAIL: {
                Value callee = vmPeek(vm, arg);
                if (IS_CLOSURE(callee)) {
                    ObjClosure* closure = AS_CLOSURE(callee);
                    frame->closure = closure;
                    frame->ip = 0;
                    frame->slots = vm->stack.stackTop - arg - 1;
                    frame->depth = vm->frameCount - 1;
                } else if (IS_NATIVE(callee)) {
                    ObjNative* native = AS_NATIVE(callee);
                    Value* args = vm->stack.stackTop - arg;
                    Value result = native->function((int)arg, args, native->context);
                    vm->stack.stackTop -= arg + 2;
                    vmPush(vm, result);
                    vm->frameCount--;
                    if (vm->frameCount == 0) return EXEC_HALTED;
                    frame = &vm->frames[vm->frameCount - 1];
                } else {
                    vmRuntimeError(vm, "Can only call functions for tail call");
                    return EXEC_RUNTIME_ERROR;
                }
                break;
            }

            case OP_RETURN: {
                Value result = NIL_VAL;
                closeUpvalues(vm, frame->slots);
                vm->frameCount--;
                vm->stack.stackTop = frame->slots;
                if (vm->frameCount == 0) { vm->stack.stackTop--; return EXEC_OK; }
                vmPush(vm, result);
                frame = &vm->frames[vm->frameCount - 1];
                break;
            }

            case OP_RETURN_VALUE: {
                Value result = vmPop(vm);
                closeUpvalues(vm, frame->slots);
                vm->frameCount--;
                vm->stack.stackTop = frame->slots;
                if (vm->frameCount == 0) { vm->stack.stackTop--; return EXEC_OK; }
                vmPush(vm, result);
                frame = &vm->frames[vm->frameCount - 1];
                break;
            }

            case OP_CLOSURE: {
                ObjFunction* func = AS_FUNCTION(fn->constants.values[arg]);
                ObjClosure* closure = allocateClosure(&vm->memory, func);
                if (!closure) return EXEC_OUT_OF_MEMORY;
                closure->upvalues = calloc(func->upvalueCount, sizeof(ObjUpvalue*));
                closure->upvalueCount = func->upvalueCount;
                for (uint32_t i = 0; i < func->upvalueCount; i++) {
                    uint32_t isLocal = getArg(fn->bytecode[frame->ip++]);
                    uint32_t index = getArg(fn->bytecode[frame->ip++]);
                    if (isLocal) closure->upvalues[i] = captureUpvalue(vm, frame->slots + index);
                    else closure->upvalues[i] = frame->closure->upvalues[index];
                }
                vmPush(vm, CLOSURE_VAL(closure));
                break;
            }

            case OP_CLOSE_UPVALUE:
                closeUpvalues(vm, vm->stack.stackTop - 1);
                vmPop(vm);
                break;

            case OP_NEW_ARRAY: {
                ObjArray* arr = allocateArray(&vm->memory);
                if (!arr) return EXEC_OUT_OF_MEMORY;
                for (uint32_t i = 0; i < arg; i++)
                    writeValueArray(&arr->items, vm->stack.stackTop[-arg + i]);
                vm->stack.stackTop -= arg;
                vmPush(vm, ARRAY_VAL(arr));
                break;
            }

            case OP_NEW_MAP: {
                ObjMap* map = allocateMap(&vm->memory);
                if (!map) return EXEC_OUT_OF_MEMORY;
                if (!map->entries) {
                    map->capacity = (arg + 1) * 2;
                    map->entries = calloc(map->capacity, sizeof(struct MapEntry));
                }
                for (uint32_t i = 0; i < arg; i++) {
                    Value val = vmPop(vm);
                    Value key = vmPop(vm);
                    struct Table tbl;
                    tbl.entries = map->entries;
                    tbl.capacity = map->capacity;
                    tbl.count = map->count;
                    tableSet(&tbl, key, val);
                    map->count = tbl.count;
                }
                vmPush(vm, MAP_VAL(map));
                break;
            }

            case OP_INDEX_GET: {
                Value index = vmPop(vm);
                Value target = vmPop(vm);
                if (IS_ARRAY(target)) {
                    ObjArray* arr = AS_ARRAY(target);
                    if (!IS_INT(index)) { vmRuntimeError(vm, "Array index must be an integer"); return EXEC_RUNTIME_ERROR; }
                    int64_t i = AS_INT(index);
                    if (i < 0 || (uint64_t)i >= arr->items.count) { vmRuntimeError(vm, "Array index out of bounds"); return EXEC_RUNTIME_ERROR; }
                    vmPush(vm, arr->items.values[(uint32_t)i]);
                } else if (IS_MAP(target)) {
                    ObjMap* map = AS_MAP(target);
                    struct Table tbl;
                    tbl.entries = map->entries;
                    tbl.capacity = map->capacity;
                    tbl.count = map->count;
                    Value result;
                    if (tableGet(&tbl, index, &result)) vmPush(vm, result);
                    else vmPush(vm, NIL_VAL);
                } else if (IS_STRING(target)) {
                    ObjString* str = AS_STRING(target);
                    if (!IS_INT(index)) { vmRuntimeError(vm, "String index must be an integer"); return EXEC_RUNTIME_ERROR; }
                    int64_t i = AS_INT(index);
                    if (i < 0 || (uint64_t)i >= str->length) { vmRuntimeError(vm, "String index out of bounds"); return EXEC_RUNTIME_ERROR; }
                    char buf[2] = {str->chars[i], '\0'};
                    ObjString* ch = allocateString(&vm->memory, buf, 1);
                    vmPush(vm, STRING_VAL(ch));
                } else { vmRuntimeError(vm, "Can only index arrays, maps, and strings"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_INDEX_SET: {
                Value value = vmPop(vm);
                Value index = vmPop(vm);
                Value target = vmPop(vm);
                if (IS_ARRAY(target)) {
                    ObjArray* arr = AS_ARRAY(target);
                    if (!IS_INT(index)) { vmRuntimeError(vm, "Array index must be an integer"); return EXEC_RUNTIME_ERROR; }
                    int64_t i = AS_INT(index);
                    if (i < 0 || (uint64_t)i >= arr->items.count) { vmRuntimeError(vm, "Array index out of bounds"); return EXEC_RUNTIME_ERROR; }
                    arr->items.values[(uint32_t)i] = value;
                } else if (IS_MAP(target)) {
                    ObjMap* map = AS_MAP(target);
                    struct Table tbl;
                    tbl.entries = map->entries;
                    tbl.capacity = map->capacity;
                    tbl.count = map->count;
                    tableSet(&tbl, index, value);
                    map->count = tbl.count;
                } else { vmRuntimeError(vm, "Can only index arrays and maps"); return EXEC_RUNTIME_ERROR; }
                vmPush(vm, value);
                break;
            }

            case OP_NEW_OBJECT:
                if (arg < vm->globals.count) {
                    Value klassVal = vm->globals.values[arg];
                    if (IS_CLASS(klassVal)) {
                        ObjInstance* inst = allocateInstance(&vm->memory, AS_CLASS(klassVal));
                        if (!inst) return EXEC_OUT_OF_MEMORY;
                        vmPush(vm, INSTANCE_VAL(inst));
                    } else { vmRuntimeError(vm, "Class not found"); return EXEC_RUNTIME_ERROR; }
                } else { vmRuntimeError(vm, "Class not found"); return EXEC_RUNTIME_ERROR; }
                break;

            case OP_PROP_GET: {
                Value target = vmPeek(vm, 0);
                ObjString* name = AS_STRING(fn->constants.values[arg]);
                if (IS_INSTANCE(target)) {
                    ObjInstance* inst = AS_INSTANCE(target);
                    Value result;
                    if (inst->fields) {
                        struct Table ftbl;
                        ftbl.entries = inst->fields->entries;
                        ftbl.capacity = inst->fields->capacity;
                        ftbl.count = inst->fields->count;
                        if (tableGet(&ftbl, STRING_VAL(name), &result)) {
                            vmPop(vm); vmPush(vm, result); break;
                        }
                    }
                    if (inst->klass && inst->klass->methods) {
                        struct Table mtbl;
                        mtbl.entries = inst->klass->methods->entries;
                        mtbl.capacity = inst->klass->methods->capacity;
                        mtbl.count = inst->klass->methods->count;
                        if (tableGet(&mtbl, STRING_VAL(name), &result)) {
                            if (IS_CLOSURE(result)) {
                                ObjBoundMethod* bm = allocateBoundMethod(&vm->memory, target, AS_CLOSURE(result));
                                vmPop(vm); vmPush(vm, OBJ_VAL((Obj*)bm));
                            } else { vmPop(vm); vmPush(vm, result); }
                            break;
                        }
                    }
                    vmRuntimeError(vm, "Undefined property '%s'", name->chars);
                    return EXEC_RUNTIME_ERROR;
                } else { vmRuntimeError(vm, "Only instances have properties"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_PROP_SET: {
                Value target = vmPeek(vm, 1);
                ObjString* name = AS_STRING(fn->constants.values[arg]);
                if (IS_INSTANCE(target)) {
                    ObjInstance* inst = AS_INSTANCE(target);
                    if (!inst->fields) { inst->fields = malloc(sizeof(struct Table)); initTable(inst->fields); }
                    tableSet(inst->fields, STRING_VAL(name), vmPeek(vm, 0));
                } else { vmRuntimeError(vm, "Only instances have properties"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_METHOD: {
                ObjString* name = AS_STRING(fn->constants.values[arg]);
                Value method = vmPeek(vm, 0);
                Value klassVal = vmPeek(vm, 1);
                if (!IS_CLASS(klassVal)) { vmRuntimeError(vm, "Methods can only be defined on classes"); return EXEC_RUNTIME_ERROR; }
                ObjClass* klass = AS_CLASS(klassVal);
                if (!klass->methods) { klass->methods = malloc(sizeof(struct Table)); initTable(klass->methods); }
                tableSet(klass->methods, STRING_VAL(name), method);
                vmPop(vm);
                break;
            }

            case OP_INVOKE: {
                ObjString* name = AS_STRING(fn->constants.values[arg]);
                uint32_t ac = arg;
                Value receiver = vmPeek(vm, ac);
                if (IS_INSTANCE(receiver)) {
                    ObjInstance* inst = AS_INSTANCE(receiver);
                    if (inst->klass && inst->klass->methods) {
                        struct Table mtbl;
                        mtbl.entries = inst->klass->methods->entries;
                        mtbl.capacity = inst->klass->methods->capacity;
                        mtbl.count = inst->klass->methods->count;
                        Value method;
                        if (tableGet(&mtbl, STRING_VAL(name), &method)) {
                            if (IS_CLOSURE(method)) {
                                ObjClosure* closure = AS_CLOSURE(method);
                                if (vm->frameCount >= FRAMES_MAX) {
                                    vmRuntimeError(vm, "Call stack overflow");
                                    return EXEC_STACK_OVERFLOW;
                                }
                                CallFrame* newFrame = &vm->frames[vm->frameCount++];
                                newFrame->closure = closure;
                                newFrame->ip = 0;
                                newFrame->slots = vm->stack.stackTop - ac - 1;
                                newFrame->depth = vm->frameCount - 1;
                                frame = newFrame;
                            } else if (IS_NATIVE(method)) {
                                ObjNative* native = AS_NATIVE(method);
                                Value* args = vm->stack.stackTop - ac;
                                Value result = native->function((int)ac, args, native->context);
                                vm->stack.stackTop -= ac + 1;
                                vmPush(vm, result);
                            } else { vmRuntimeError(vm, "Method is not callable"); return EXEC_RUNTIME_ERROR; }
                            break;
                        }
                    }
                    vmRuntimeError(vm, "Undefined method '%s'", name->chars);
                    return EXEC_RUNTIME_ERROR;
                } else { vmRuntimeError(vm, "Only instances have methods"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_INHERIT: {
                Value super = vmPeek(vm, 1);
                Value sub = vmPeek(vm, 0);
                if (!IS_CLASS(super) || !IS_CLASS(sub)) { vmRuntimeError(vm, "Superclass must be a class"); return EXEC_RUNTIME_ERROR; }
                ObjClass* subClass = AS_CLASS(sub);
                ObjClass* superClass = AS_CLASS(super);
                if (superClass->methods) {
                    if (!subClass->methods) { subClass->methods = malloc(sizeof(struct Table)); initTable(subClass->methods); }
                    for (uint32_t i = 0; i < superClass->methods->capacity; i++) {
                        if (!IS_NIL(superClass->methods->entries[i].key))
                            tableSet(subClass->methods, superClass->methods->entries[i].key, superClass->methods->entries[i].value);
                    }
                }
                vmPop(vm);
                break;
            }

            case OP_GET_SUPER: {
                ObjString* name = AS_STRING(fn->constants.values[arg]);
                Value super = vmPop(vm);
                Value receiver = vmPeek(vm, 0);
                if (!IS_CLASS(super)) { vmRuntimeError(vm, "Super must be a class"); return EXEC_RUNTIME_ERROR; }
                ObjClass* superClass = AS_CLASS(super);
                if (superClass->methods) {
                    struct Table mtbl;
                    mtbl.entries = superClass->methods->entries;
                    mtbl.capacity = superClass->methods->capacity;
                    mtbl.count = superClass->methods->count;
                    Value method;
                    if (tableGet(&mtbl, STRING_VAL(name), &method)) {
                        if (IS_CLOSURE(method)) {
                            ObjBoundMethod* bm = allocateBoundMethod(&vm->memory, receiver, AS_CLOSURE(method));
                            vmPop(vm); vmPush(vm, OBJ_VAL((Obj*)bm));
                        } else { vmPop(vm); vmPush(vm, method); }
                    } else { vmRuntimeError(vm, "Undefined super method '%s'", name->chars); return EXEC_RUNTIME_ERROR; }
                } else { vmRuntimeError(vm, "Undefined super method '%s'", name->chars); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_SCOPE_ENTER: break;
            case OP_SCOPE_EXIT: closeUpvalues(vm, vm->stack.stackTop); break;
            case OP_POP: vmPop(vm); break;
            case OP_DUP: { Value a = vmPeek(vm, 0); vmPush(vm, a); } break;
            case OP_SWAP: { Value a = vmPeek(vm, 0); Value b = vmPeek(vm, 1); vm->stack.stackTop[-1] = b; vm->stack.stackTop[-2] = a; } break;

            case OP_BUILD_STRING: {
                uint32_t totalLen = 0;
                for (uint32_t i = 0; i < arg; i++) {
                    Value v = vm->stack.stackTop[-arg + i];
                    if (IS_STRING(v)) totalLen += AS_STRING(v)->length;
                    else totalLen += 16;
                }
                char* buf = malloc(totalLen + 1);
                uint32_t pos = 0;
                for (uint32_t i = 0; i < arg; i++) {
                    Value v = vm->stack.stackTop[-arg + i];
                    if (IS_STRING(v)) {
                        memcpy(buf + pos, AS_CSTRING(v), AS_STRING(v)->length);
                        pos += AS_STRING(v)->length;
                    } else {
                        char tmp[64]; int len = snprintf(tmp, sizeof(tmp), "%lld", (long long)AS_INT(v));
                        memcpy(buf + pos, tmp, (uint32_t)len); pos += (uint32_t)len;
                    }
                }
                buf[pos] = '\0';
                ObjString* str = allocateString(&vm->memory, buf, pos);
                free(buf);
                vm->stack.stackTop -= arg;
                vmPush(vm, STRING_VAL(str));
                break;
            }

            case OP_IMPORT: {
                if (vm->plugins) {
                    ObjString* modName = AS_STRING(fn->constants.values[arg]);
                    Value result;
                    if (pluginImport(vm->plugins, vm, modName, &result))
                        vmPush(vm, result);
                    else { vmRuntimeError(vm, "Module '%s' not found", modName->chars); return EXEC_RUNTIME_ERROR; }
                } else { vmRuntimeError(vm, "Plugin system not available"); return EXEC_RUNTIME_ERROR; }
                break;
            }

            case OP_EXPORT: {
                Value value = vmPop(vm);
                ObjString* name = AS_STRING(fn->constants.values[arg]);
                if (!vm->modules) { vm->modules = malloc(sizeof(struct Table)); initTable(vm->modules); }
                tableSet(vm->modules, STRING_VAL(name), value);
                break;
            }

            case OP_DEBUG_BREAK:
                if (vm->debugger) { ExecResult dr = debuggerCheckBreak(vm->debugger, vm); if (dr != EXEC_OK) return dr; }
                break;

            case OP_PROFILE_START:
                if (vm->profiler) profilerStart(vm->profiler, vm, op);
                vm->profileDepth++;
                break;

            case OP_PROFILE_END:
                vm->profileDepth--;
                if (vm->profiler && vm->profileDepth == 0) profilerStop(vm->profiler, vm);
                break;

            case OP_SANDBOX_ENTER: vm->sandboxLevel++; break;
            case OP_SANDBOX_EXIT: if (vm->sandboxLevel > 0) vm->sandboxLevel--; break;

            default:
                vmRuntimeError(vm, "Unknown opcode %d", op);
                return EXEC_RUNTIME_ERROR;
        }
    }
}
