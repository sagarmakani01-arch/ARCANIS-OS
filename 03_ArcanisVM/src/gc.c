#include "gc.h"
#include <stdlib.h>

void initGC(GC* gc, MemoryManager* mm, Stack* stack) {
    gc->mm = mm;
    gc->stack = stack;
    gc->roots = NULL;
    gc->gcCount = 0;
    gc->gcGeneration = 0;
    gc->gcEnabled = true;
    gc->gcCallback = NULL;
}

void setGCStack(GC* gc, Stack* stack) {
    gc->stack = stack;
}

static void markObjectInternal(GC* gc, Obj* obj);

static void markTable(GC* gc, struct Table* table) {
    if (!table || !table->entries) return;
    for (uint32_t i = 0; i < table->capacity; i++) {
        struct MapEntry* entry = &table->entries[i];
        if (!IS_NIL(entry->key)) {
            if (entry->key.as.obj) markObjectInternal(gc, entry->key.as.obj);
            if (entry->value.as.obj) markObjectInternal(gc, entry->value.as.obj);
        }
    }
}

static void markValueInternal(GC* gc, Value value) {
    if (value.as.obj) markObjectInternal(gc, value.as.obj);
}

static void markObjectInternal(GC* gc, Obj* obj) {
    if (!obj || obj->isMarked) return;
    gc->gcCount++;
    obj->isMarked = true;
    switch (obj->type) {
        case OBJ_STRING:
        case OBJ_FOREIGN:
            break;
        case OBJ_ARRAY: {
            ObjArray* arr = (ObjArray*)obj;
            for (uint32_t i = 0; i < arr->items.count; i++) {
                markValueInternal(gc, arr->items.values[i]);
            }
            break;
        }
        case OBJ_MAP: {
            ObjMap* map = (ObjMap*)obj;
            if (map->entries) {
                for (uint32_t i = 0; i < map->capacity; i++) {
                    if (!IS_NIL(map->entries[i].key)) {
                        markValueInternal(gc, map->entries[i].key);
                        markValueInternal(gc, map->entries[i].value);
                    }
                }
            }
            break;
        }
        case OBJ_FUNCTION: {
            ObjFunction* fn = (ObjFunction*)obj;
            if (fn->name) markObjectInternal(gc, (Obj*)fn->name);
            for (uint32_t i = 0; i < fn->constants.count; i++) {
                markValueInternal(gc, fn->constants.values[i]);
            }
            break;
        }
        case OBJ_NATIVE:
            break;
        case OBJ_CLOSURE: {
            ObjClosure* closure = (ObjClosure*)obj;
            markObjectInternal(gc, (Obj*)closure->function);
            for (uint32_t i = 0; i < closure->upvalueCount; i++) {
                if (closure->upvalues[i])
                    markObjectInternal(gc, (Obj*)closure->upvalues[i]);
            }
            break;
        }
        case OBJ_UPVALUE: {
            ObjUpvalue* up = (ObjUpvalue*)obj;
            if (up->closed.as.obj) markObjectInternal(gc, up->closed.as.obj);
            break;
        }
        case OBJ_BOUND_METHOD: {
            ObjBoundMethod* bm = (ObjBoundMethod*)obj;
            markValueInternal(gc, bm->receiver);
            if (bm->method) markObjectInternal(gc, (Obj*)bm->method);
            break;
        }
        case OBJ_CLASS: {
            ObjClass* klass = (ObjClass*)obj;
            if (klass->name) markObjectInternal(gc, (Obj*)klass->name);
            markTable(gc, klass->methods);
            break;
        }
        case OBJ_INSTANCE: {
            ObjInstance* inst = (ObjInstance*)obj;
            if (inst->klass) markObjectInternal(gc, (Obj*)inst->klass);
            markTable(gc, inst->fields);
            break;
        }
        case OBJ_MODULE: {
            ObjModule* mod = (ObjModule*)obj;
            if (mod->name) markObjectInternal(gc, (Obj*)mod->name);
            markTable(gc, mod->globals);
            break;
        }
    }
}

void gcMarkRoots(GC* gc) {
    GCRoot* root = gc->roots;
    while (root) {
        if (root->location && root->location->as.obj)
            markObjectInternal(gc, root->location->as.obj);
        root = root->next;
    }
}

void gcMarkObject(GC* gc, Obj* obj) {
    if (gc->gcEnabled) markObjectInternal(gc, obj);
}

void gcMarkValue(GC* gc, Value value) {
    if (gc->gcEnabled && value.as.obj) markObjectInternal(gc, value.as.obj);
}

void gcSweep(GC* gc) {
    uint32_t freed = 0;
    Obj** prev = &gc->mm->objects;
    Obj* obj = gc->mm->objects;
    while (obj) {
        if (!obj->isMarked) {
            Obj* unreached = obj;
            *prev = obj->next;
            obj = obj->next;
            freeObject(gc->mm, unreached);
            gc->mm->numObjects--;
            freed++;
        } else {
            obj->isMarked = false;
            prev = &obj->next;
            obj = obj->next;
        }
    }
    gc->gcCount = 0;
    if (gc->gcCallback) gc->gcCallback(gc, freed, gc->mm->numObjects);
}

void gcCollect(GC* gc) {
    if (!gc->gcEnabled) return;
    gc->gcGeneration++;
    if (gc->stack) stackMark(gc->stack);
    gcMarkRoots(gc);
    gcSweep(gc);
    gc->mm->nextGC = gc->mm->bytesAllocated * 2;
    if (gc->mm->nextGC < 1024 * 1024) gc->mm->nextGC = 1024 * 1024;
}

void gcEnable(GC* gc) { gc->gcEnabled = true; }
void gcDisable(GC* gc) { gc->gcEnabled = false; }
