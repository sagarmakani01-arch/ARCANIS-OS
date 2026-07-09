#include "runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <sys/time.h>
#endif

static double getCurrentTime(void) {
#ifdef _WIN32
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    return (double)(((ULONGLONG)ft.dwHighDateTime << 32) | ft.dwLowDateTime) / 10000000.0;
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (double)tv.tv_sec + (double)tv.tv_usec / 1000000.0;
#endif
}

Value nativePrint(int argCount, Value* args, void* context) {
    (void)context;
    for (int i = 0; i < argCount; i++) {
        if (i > 0) printf(" ");
        printValue(stdout, args[i]);
    }
    printf("\n");
    return NIL_VAL;
}

Value nativeInput(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount > 0) printValue(stdout, args[0]);
    char buf[1024];
    if (fgets(buf, sizeof(buf), stdin)) {
        size_t len = strlen(buf);
        while (len > 0 && (buf[len-1] == '\n' || buf[len-1] == '\r')) buf[--len] = '\0';
        VM* vm = (VM*)context;
        ObjString* str = copyString(&vm->memory, buf, (uint32_t)len);
        return STRING_VAL(str);
    }
    return NIL_VAL;
}

Value nativeLen(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount < 1) return INT_VAL(0);
    if (IS_STRING(args[0])) return INT_VAL((int64_t)AS_STRING(args[0])->length);
    if (IS_ARRAY(args[0])) return INT_VAL((int64_t)AS_ARRAY(args[0])->items.count);
    if (IS_MAP(args[0])) {
        ObjMap* map = AS_MAP(args[0]);
        Value v;
        return INT_VAL((int64_t)map->count);
    }
    return INT_VAL(0);
}

Value nativeType(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount < 1) return STRING_VAL(((VM*)context) ? NULL : NULL);
    VM* vm = (VM*)context;
    const char* typeName = "unknown";
    switch (args[0].type) {
        case VAL_NIL: typeName = "nil"; break;
        case VAL_BOOL: typeName = "bool"; break;
        case VAL_INT: typeName = "int"; break;
        case VAL_FLOAT: typeName = "float"; break;
        case VAL_STRING: typeName = "string"; break;
        case VAL_ARRAY: typeName = "array"; break;
        case VAL_MAP: typeName = "map"; break;
        case VAL_FUNCTION: typeName = "function"; break;
        case VAL_NATIVE: typeName = "native"; break;
        case VAL_CLOSURE: typeName = "function"; break;
        case VAL_CLASS: typeName = "class"; break;
        case VAL_INSTANCE: typeName = "instance"; break;
        case VAL_BOUND_METHOD: typeName = "method"; break;
        case VAL_MODULE: typeName = "module"; break;
        default: typeName = "unknown"; break;
    }
    return STRING_VAL(copyString(&((VM*)context)->memory, typeName, (uint32_t)strlen(typeName)));
}

#define GET_VM() ((VM*)context)

Value nativeToInt(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount < 1) return INT_VAL(0);
    if (IS_INT(args[0])) return args[0];
    if (IS_FLOAT(args[0])) return INT_VAL((int64_t)AS_FLOAT(args[0]));
    if (IS_BOOL(args[0])) return INT_VAL(AS_BOOL(args[0]) ? 1 : 0);
    if (IS_STRING(args[0])) return INT_VAL((int64_t)atoll(AS_CSTRING(args[0])));
    return INT_VAL(0);
}

Value nativeToFloat(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount < 1) return FLOAT_VAL(0.0);
    if (IS_FLOAT(args[0])) return args[0];
    if (IS_INT(args[0])) return FLOAT_VAL((double)AS_INT(args[0]));
    if (IS_BOOL(args[0])) return FLOAT_VAL(AS_BOOL(args[0]) ? 1.0 : 0.0);
    if (IS_STRING(args[0])) return FLOAT_VAL(atof(AS_CSTRING(args[0])));
    return FLOAT_VAL(0.0);
}

static void sprintValue(char* buf, size_t size, Value value) {
    char tmp[256];
    switch (value.type) {
        case VAL_NIL: snprintf(buf, size, "nil"); break;
        case VAL_BOOL: snprintf(buf, size, "%s", AS_BOOL(value) ? "true" : "false"); break;
        case VAL_INT: snprintf(buf, size, "%lld", (long long)AS_INT(value)); break;
        case VAL_FLOAT: snprintf(buf, size, "%g", AS_FLOAT(value)); break;
        case VAL_STRING: snprintf(buf, size, "%s", AS_CSTRING(value)); break;
        case VAL_FUNCTION: snprintf(buf, size, "<fn %s>", AS_FUNCTION(value)->name ? AS_FUNCTION(value)->name->chars : "script"); break;
        case VAL_CLOSURE: snprintf(buf, size, "<fn %s>", AS_CLOSURE(value)->function->name ? AS_CLOSURE(value)->function->name->chars : "script"); break;
        case VAL_CLASS: snprintf(buf, size, "<class %s>", AS_CLASS(value)->name->chars); break;
        case VAL_INSTANCE: snprintf(buf, size, "<instance of %s>", AS_INSTANCE(value)->klass->name->chars); break;
        default: snprintf(buf, size, "<%s>", "unknown");
    }
}

Value nativeToString(int argCount, Value* args, void* context) {
    if (argCount < 1) return STRING_VAL(copyString(&GET_VM()->memory, "", 0));
    char buf[256];
    sprintValue(buf, sizeof(buf), args[0]);
    return STRING_VAL(copyString(&GET_VM()->memory, buf, (uint32_t)strlen(buf)));
}

Value nativeArrayPush(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount < 2 || !IS_ARRAY(args[0])) return NIL_VAL;
    ObjArray* arr = AS_ARRAY(args[0]);
    writeValueArray(&arr->items, args[1]);
    return args[0];
}

Value nativeArrayPop(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount < 1 || !IS_ARRAY(args[0])) return NIL_VAL;
    ObjArray* arr = AS_ARRAY(args[0]);
    if (arr->items.count == 0) return NIL_VAL;
    return arr->items.values[--arr->items.count];
}

Value nativeArrayInsert(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount < 3 || !IS_ARRAY(args[0]) || !IS_INT(args[1])) return NIL_VAL;
    ObjArray* arr = AS_ARRAY(args[0]);
    uint32_t idx = (uint32_t)AS_INT(args[1]);
    if (idx > arr->items.count) idx = arr->items.count;
    writeValueArray(&arr->items, NIL_VAL);
    for (uint32_t i = arr->items.count - 1; i > idx; i--)
        arr->items.values[i] = arr->items.values[i-1];
    arr->items.values[idx] = args[2];
    return args[0];
}

Value nativeArrayRemove(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount < 2 || !IS_ARRAY(args[0]) || !IS_INT(args[1])) return NIL_VAL;
    ObjArray* arr = AS_ARRAY(args[0]);
    uint32_t idx = (uint32_t)AS_INT(args[1]);
    if (idx >= arr->items.count) return NIL_VAL;
    Value removed = arr->items.values[idx];
    for (uint32_t i = idx; i < arr->items.count - 1; i++)
        arr->items.values[i] = arr->items.values[i+1];
    arr->items.count--;
    return removed;
}

Value nativeArraySort(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount < 1 || !IS_ARRAY(args[0])) return args[0];
    ObjArray* arr = AS_ARRAY(args[0]);
    for (uint32_t i = 0; i < arr->items.count; i++) {
        for (uint32_t j = i + 1; j < arr->items.count; j++) {
            if (IS_INT(arr->items.values[i]) && IS_INT(arr->items.values[j])) {
                if (AS_INT(arr->items.values[i]) > AS_INT(arr->items.values[j])) {
                    Value tmp = arr->items.values[i];
                    arr->items.values[i] = arr->items.values[j];
                    arr->items.values[j] = tmp;
                }
            } else if (IS_NUMBER(arr->items.values[i]) && IS_NUMBER(arr->items.values[j])) {
                if (AS_NUMBER(arr->items.values[i]) > AS_NUMBER(arr->items.values[j])) {
                    Value tmp = arr->items.values[i];
                    arr->items.values[i] = arr->items.values[j];
                    arr->items.values[j] = tmp;
                }
            }
        }
    }
    return args[0];
}

Value nativeArraySlice(int argCount, Value* args, void* context) {
    if (argCount < 2 || !IS_ARRAY(args[0]) || !IS_INT(args[1])) return NIL_VAL;
    ObjArray* src = AS_ARRAY(args[0]);
    uint32_t start = (uint32_t)AS_INT(args[1]);
    uint32_t end = src->items.count;
    if (argCount >= 3 && IS_INT(args[2])) end = (uint32_t)AS_INT(args[2]);
    if (start > src->items.count) start = (uint32_t)src->items.count;
    if (end > src->items.count) end = (uint32_t)src->items.count;
    ObjArray* result = allocateArray(&GET_VM()->memory);
    for (uint32_t i = start; i < end; i++)
        writeValueArray(&result->items, src->items.values[i]);
    return ARRAY_VAL(result);
}

Value nativeMapKeys(int argCount, Value* args, void* context) {
    if (argCount < 1 || !IS_MAP(args[0])) return NIL_VAL;
    ObjMap* map = AS_MAP(args[0]);
    ObjArray* result = allocateArray(&GET_VM()->memory);
    for (uint32_t i = 0; i < map->capacity; i++)
        if (!IS_NIL(map->entries[i].key))
            writeValueArray(&result->items, map->entries[i].key);
    return ARRAY_VAL(result);
}

Value nativeMapValues(int argCount, Value* args, void* context) {
    if (argCount < 1 || !IS_MAP(args[0])) return NIL_VAL;
    ObjMap* map = AS_MAP(args[0]);
    ObjArray* result = allocateArray(&GET_VM()->memory);
    for (uint32_t i = 0; i < map->capacity; i++)
        if (!IS_NIL(map->entries[i].key))
            writeValueArray(&result->items, map->entries[i].value);
    return ARRAY_VAL(result);
}

Value nativeMapHas(int argCount, Value* args, void* context) {
    if (argCount < 2 || !IS_MAP(args[0])) return BOOL_VAL(false);
    ObjMap* map = AS_MAP(args[0]);
    struct Table tbl;
    tbl.entries = map->entries;
    tbl.capacity = map->capacity;
    tbl.count = map->count;
    Value result;
    return BOOL_VAL(tableGet(&tbl, args[1], &result));
}

Value nativeClock(int argCount, Value* args, void* context) {
    (void)argCount; (void)args; (void)context;
    return FLOAT_VAL(getCurrentTime());
}

Value nativeExit(int argCount, Value* args, void* context) {
    (void)context;
    int code = (argCount > 0 && IS_INT(args[0])) ? (int)AS_INT(args[0]) : 0;
    exit(code);
    return NIL_VAL;
}

Value nativeAssert(int argCount, Value* args, void* context) {
    (void)context;
    if (argCount < 1) return NIL_VAL;
    if (vmIsFalsey(args[0])) {
        fprintf(stderr, "Assertion failed");
        if (argCount > 1) { fprintf(stderr, ": "); printValue(stderr, args[1]); }
        fprintf(stderr, "\n");
        exit(1);
    }
    return NIL_VAL;
}

Value nativeError(int argCount, Value* args, void* context) {
    (void)context;
    fprintf(stderr, "Error: ");
    if (argCount > 0) printValue(stderr, args[0]);
    fprintf(stderr, "\n");
    if (((VM*)context)->runtimeError) return NIL_VAL;
    return NIL_VAL;
}

Value nativeGC(int argCount, Value* args, void* context) {
    (void)argCount;
    VM* vm = (VM*)context;
    gcCollect(&vm->gc);
    return NIL_VAL;
}

void initRuntime(VM* vm) {
    vmDefineNative(vm, "print", nativePrint, vm);
    vmDefineNative(vm, "input", nativeInput, vm);
    vmDefineNative(vm, "len", nativeLen, vm);
    vmDefineNative(vm, "type", nativeType, vm);
    vmDefineNative(vm, "toInt", nativeToInt, vm);
    vmDefineNative(vm, "toFloat", nativeToFloat, vm);
    vmDefineNative(vm, "toString", nativeToString, vm);
    vmDefineNative(vm, "arrayPush", nativeArrayPush, vm);
    vmDefineNative(vm, "arrayPop", nativeArrayPop, vm);
    vmDefineNative(vm, "arrayInsert", nativeArrayInsert, vm);
    vmDefineNative(vm, "arrayRemove", nativeArrayRemove, vm);
    vmDefineNative(vm, "arraySort", nativeArraySort, vm);
    vmDefineNative(vm, "arraySlice", nativeArraySlice, vm);
    vmDefineNative(vm, "mapKeys", nativeMapKeys, vm);
    vmDefineNative(vm, "mapValues", nativeMapValues, vm);
    vmDefineNative(vm, "mapHas", nativeMapHas, vm);
    vmDefineNative(vm, "clock", nativeClock, vm);
    vmDefineNative(vm, "exit", nativeExit, vm);
    vmDefineNative(vm, "assert", nativeAssert, vm);
    vmDefineNative(vm, "error", nativeError, vm);
    vmDefineNative(vm, "gc", nativeGC, vm);
}
