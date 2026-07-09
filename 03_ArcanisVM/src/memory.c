#include "memory.h"
#include <stdlib.h>

static void* defaultAlloc(void* ctx, size_t size) {
    (void)ctx;
    if (size == 0) return NULL;
    return malloc(size);
}

static void* defaultRealloc(void* ctx, void* ptr, size_t oldSize, size_t newSize) {
    (void)ctx;
    (void)oldSize;
    if (newSize == 0) { free(ptr); return NULL; }
    return realloc(ptr, newSize);
}

static void defaultFree(void* ctx, void* ptr) {
    (void)ctx;
    free(ptr);
}

static Allocator defaultAllocator = {
    defaultAlloc,
    defaultRealloc,
    defaultFree,
    NULL
};

void initMemoryManager(MemoryManager* mm, Allocator allocator) {
    mm->allocator = allocator;
    mm->objects = NULL;
    mm->bytesAllocated = 0;
    mm->nextGC = 1024 * 1024;
    mm->gcThreshold = 1024 * 1024;
    mm->numObjects = 0;
}

void* allocateObject(MemoryManager* mm, size_t size) {
    if (mm->bytesAllocated + size > mm->nextGC) {
        return NULL;
    }
    Obj* obj = mm->allocator.alloc(mm->allocator.context, size);
    if (!obj) return NULL;
    obj->type = 0;
    obj->isMarked = false;
    obj->next = mm->objects;
    mm->objects = obj;
    mm->bytesAllocated += (uint32_t)size;
    mm->numObjects++;
    return obj;
}

void freeObject(MemoryManager* mm, Obj* obj) {
    (void)mm;
    switch (obj->type) {
        case OBJ_STRING: break;
        case OBJ_ARRAY: freeValueArray(&((ObjArray*)obj)->items); break;
        case OBJ_MAP: {
            ObjMap* map = (ObjMap*)obj;
            if (map->entries) {
                struct Table tbl;
                tbl.entries = map->entries;
                tbl.capacity = map->capacity;
                tbl.count = map->count;
                freeTable(&tbl);
            }
            break;
        }
        case OBJ_FUNCTION: {
            ObjFunction* fn = (ObjFunction*)obj;
            free(fn->bytecode);
            free(fn->lines);
            freeValueArray(&fn->constants);
            break;
        }
        case OBJ_CLOSURE: free(((ObjClosure*)obj)->upvalues); break;
        case OBJ_CLASS: if (((ObjClass*)obj)->methods) { freeTable(((ObjClass*)obj)->methods); free(((ObjClass*)obj)->methods); } break;
        case OBJ_INSTANCE: if (((ObjInstance*)obj)->fields) { freeTable(((ObjInstance*)obj)->fields); free(((ObjInstance*)obj)->fields); } break;
        case OBJ_MODULE: if (((ObjModule*)obj)->globals) { freeTable(((ObjModule*)obj)->globals); free(((ObjModule*)obj)->globals); } break;
        case OBJ_FOREIGN: {
            ObjForeign* f = (ObjForeign*)obj;
            if (f->destructor) f->destructor(f->data);
            break;
        }
        default: break;
    }
    mm->allocator.freeFn(mm->allocator.context, obj);
}

void freeAllObjects(MemoryManager* mm) {
    Obj* obj = mm->objects;
    while (obj) {
        Obj* next = obj->next;
        freeObject(mm, obj);
        obj = next;
    }
    mm->objects = NULL;
    mm->bytesAllocated = 0;
    mm->numObjects = 0;
}

ObjString* allocateString(MemoryManager* mm, const char* chars, uint32_t length) {
    ObjString* str = allocateObject(mm, sizeof(ObjString) + length + 1);
    if (!str) return NULL;
    str->obj.type = OBJ_STRING;
    str->length = length;
    str->hash = hashString(chars, length);
    memcpy(str->chars, chars, length);
    str->chars[length] = '\0';
    return str;
}

ObjString* copyString(MemoryManager* mm, const char* chars, uint32_t length) {
    return allocateString(mm, chars, length);
}

ObjArray* allocateArray(MemoryManager* mm) {
    ObjArray* arr = allocateObject(mm, sizeof(ObjArray));
    if (!arr) return NULL;
    arr->obj.type = OBJ_ARRAY;
    initValueArray(&arr->items);
    return arr;
}

ObjMap* allocateMap(MemoryManager* mm) {
    ObjMap* map = allocateObject(mm, sizeof(ObjMap));
    if (!map) return NULL;
    map->obj.type = OBJ_MAP;
    map->entries = NULL;
    map->capacity = 0;
    map->count = 0;
    return map;
}

ObjFunction* allocateFunction(MemoryManager* mm) {
    ObjFunction* fn = allocateObject(mm, sizeof(ObjFunction));
    if (!fn) return NULL;
    fn->obj.type = OBJ_FUNCTION;
    fn->arity = 0;
    fn->upvalueCount = 0;
    initValueArray(&fn->constants);
    fn->bytecode = NULL;
    fn->bytecodeLen = 0;
    fn->bytecodeCap = 0;
    fn->name = NULL;
    fn->lineCount = 0;
    fn->lines = NULL;
    return fn;
}

ObjNative* allocateNative(MemoryManager* mm, NativeFn fn, void* context) {
    ObjNative* native = allocateObject(mm, sizeof(ObjNative));
    if (!native) return NULL;
    native->obj.type = OBJ_NATIVE;
    native->function = fn;
    native->context = context;
    native->name = NULL;
    return native;
}

ObjClosure* allocateClosure(MemoryManager* mm, ObjFunction* function) {
    ObjClosure* closure = allocateObject(mm, sizeof(ObjClosure));
    if (!closure) return NULL;
    closure->obj.type = OBJ_CLOSURE;
    closure->function = function;
    closure->upvalues = NULL;
    closure->upvalueCount = 0;
    return closure;
}

ObjUpvalue* allocateUpvalue(MemoryManager* mm, Value* location) {
    ObjUpvalue* upvalue = allocateObject(mm, sizeof(ObjUpvalue));
    if (!upvalue) return NULL;
    upvalue->obj.type = OBJ_UPVALUE;
    upvalue->location = location;
    upvalue->closed = NIL_VAL;
    upvalue->next = NULL;
    return upvalue;
}

ObjBoundMethod* allocateBoundMethod(MemoryManager* mm, Value receiver, ObjClosure* method) {
    ObjBoundMethod* bm = allocateObject(mm, sizeof(ObjBoundMethod));
    if (!bm) return NULL;
    bm->obj.type = OBJ_BOUND_METHOD;
    bm->receiver = receiver;
    bm->method = method;
    return bm;
}

ObjClass* allocateClass(MemoryManager* mm, ObjString* name) {
    ObjClass* klass = allocateObject(mm, sizeof(ObjClass));
    if (!klass) return NULL;
    klass->obj.type = OBJ_CLASS;
    klass->name = name;
    klass->methods = NULL;
    return klass;
}

ObjInstance* allocateInstance(MemoryManager* mm, ObjClass* klass) {
    ObjInstance* inst = allocateObject(mm, sizeof(ObjInstance));
    if (!inst) return NULL;
    inst->obj.type = OBJ_INSTANCE;
    inst->klass = klass;
    inst->fields = NULL;
    return inst;
}

ObjModule* allocateModule(MemoryManager* mm, ObjString* name) {
    ObjModule* mod = allocateObject(mm, sizeof(ObjModule));
    if (!mod) return NULL;
    mod->obj.type = OBJ_MODULE;
    mod->name = name;
    mod->globals = NULL;
    return mod;
}

ObjForeign* allocateForeign(MemoryManager* mm, void* data, void (*destructor)(void*)) {
    ObjForeign* f = allocateObject(mm, sizeof(ObjForeign));
    if (!f) return NULL;
    f->obj.type = OBJ_FOREIGN;
    f->data = data;
    f->destructor = destructor;
    return f;
}

void markObject(MemoryManager* mm, Obj* obj) {
    (void)mm;
    if (!obj || obj->isMarked) return;
    obj->isMarked = true;
}

void markValue(MemoryManager* mm, Value value) {
    if (value.as.obj) markObject(mm, value.as.obj);
}
