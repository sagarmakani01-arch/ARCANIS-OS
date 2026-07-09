#include "value.h"
#include <stdlib.h>

uint32_t hashString(const char* chars, uint32_t length) {
    uint32_t hash = 2166136261u;
    for (uint32_t i = 0; i < length; i++) {
        hash ^= (uint8_t)chars[i];
        hash *= 16777619;
    }
    return hash;
}

void initValueArray(ValueArray* array) {
    array->values = NULL;
    array->capacity = 0;
    array->count = 0;
}

void writeValueArray(ValueArray* array, Value value) {
    if (array->capacity < array->count + 1) {
        uint32_t old = array->capacity;
        array->capacity = old < 8 ? 8 : old * 2;
        array->values = realloc(array->values, array->capacity * sizeof(Value));
    }
    array->values[array->count++] = value;
}

void freeValueArray(ValueArray* array) {
    free(array->values);
    array->values = NULL;
    array->capacity = 0;
    array->count = 0;
}

void initTable(struct Table* table) {
    table->entries = NULL;
    table->capacity = 0;
    table->count = 0;
}

void freeTable(struct Table* table) {
    free(table->entries);
    table->entries = NULL;
    table->capacity = 0;
    table->count = 0;
}

static struct MapEntry* findEntry(struct MapEntry* entries, uint32_t capacity, Value key, uint32_t hash) {
    uint32_t index = hash & (capacity - 1);
    struct MapEntry* tombstone = NULL;
    for (;;) {
        struct MapEntry* entry = &entries[index];
        if (IS_NIL(entry->key) && entry->hash == 0) {
            if (tombstone == NULL) return entry;
            for (uint32_t i = 1; i <= capacity; i++) {
                entry = &entries[(index + i) & (capacity - 1)];
                if (IS_NIL(entry->key) && entry->hash == 0) return tombstone;
                if (entry->key.as.obj == key.as.obj && entry->hash == hash) return entry;
                if (IS_NIL(entry->key)) return entry;
            }
            return tombstone;
        }
        if (entry->hash == hash && valuesEqual(entry->key, key)) return entry;
        if (IS_NIL(entry->key) && tombstone == NULL) tombstone = entry;
        index = (index + 1) & (capacity - 1);
    }
}

static void adjustCapacity(struct Table* table, uint32_t newCap) {
    struct MapEntry* newEntries = calloc(newCap, sizeof(struct MapEntry));
    uint32_t oldCap = table->capacity;
    struct MapEntry* oldEntries = table->entries;
    table->capacity = newCap;
    table->entries = newEntries;
    table->count = 0;
    for (uint32_t i = 0; i < oldCap; i++) {
        struct MapEntry* entry = &oldEntries[i];
        if (!IS_NIL(entry->key)) {
            struct MapEntry* dest = findEntry(newEntries, newCap, entry->key, entry->hash);
            dest->key = entry->key;
            dest->value = entry->value;
            dest->hash = entry->hash;
            table->count++;
        }
    }
    free(oldEntries);
}

bool tableSet(struct Table* table, Value key, Value value) {
    if (table->count + 1 > table->capacity * 0.75) {
        uint32_t newCap = table->capacity < 8 ? 8 : table->capacity * 2;
        adjustCapacity(table, newCap);
    }
    uint32_t hash;
    if (IS_STRING(key)) hash = AS_STRING(key)->hash;
    else if (IS_INT(key)) { uint64_t v = (uint64_t)AS_INT(key); hash = (uint32_t)(v ^ (v >> 32)); }
    else hash = (uint32_t)(uintptr_t)key.as.obj;
    struct MapEntry* entry = findEntry(table->entries, table->capacity, key, hash);
    bool isNew = IS_NIL(entry->key);
    if (isNew) table->count++;
    entry->key = key;
    entry->value = value;
    entry->hash = hash;
    return isNew;
}

bool tableGet(struct Table* table, Value key, Value* value) {
    if (table->count == 0) return false;
    uint32_t hash;
    if (IS_STRING(key)) hash = AS_STRING(key)->hash;
    else if (IS_INT(key)) { uint64_t v = (uint64_t)AS_INT(key); hash = (uint32_t)(v ^ (v >> 32)); }
    else hash = (uint32_t)(uintptr_t)key.as.obj;
    struct MapEntry* entry = findEntry(table->entries, table->capacity, key, hash);
    if (IS_NIL(entry->key)) return false;
    *value = entry->value;
    return true;
}

bool tableDelete(struct Table* table, Value key) {
    if (table->count == 0) return false;
    uint32_t hash;
    if (IS_STRING(key)) hash = AS_STRING(key)->hash;
    else if (IS_INT(key)) { uint64_t v = (uint64_t)AS_INT(key); hash = (uint32_t)(v ^ (v >> 32)); }
    else hash = (uint32_t)(uintptr_t)key.as.obj;
    struct MapEntry* entry = findEntry(table->entries, table->capacity, key, hash);
    if (IS_NIL(entry->key)) return false;
    entry->key = NIL_VAL;
    entry->hash = 0;
    entry->value = NIL_VAL;
    return true;
}

void tableMarkAll(struct Table* table) {
    for (uint32_t i = 0; i < table->capacity; i++) {
        struct MapEntry* entry = &table->entries[i];
        if (!IS_NIL(entry->key)) {
            if (entry->key.as.obj) entry->key.as.obj->isMarked = true;
            if (entry->value.as.obj) entry->value.as.obj->isMarked = true;
        }
    }
}

bool valuesEqual(Value a, Value b) {
    if (a.type != b.type) return false;
    switch (a.type) {
        case VAL_NIL: return true;
        case VAL_BOOL: return AS_BOOL(a) == AS_BOOL(b);
        case VAL_INT: return AS_INT(a) == AS_INT(b);
        case VAL_FLOAT: return AS_FLOAT(a) == AS_FLOAT(b);
        case VAL_STRING: return AS_STRING(a) == AS_STRING(b);
        case VAL_OBJECT:
        case VAL_ARRAY:
        case VAL_MAP:
        case VAL_FUNCTION:
        case VAL_NATIVE:
        case VAL_CLOSURE:
        case VAL_CLASS:
        case VAL_INSTANCE:
            return a.as.obj == b.as.obj;
        default: return false;
    }
}

void printValue(FILE* stream, Value value) {
    switch (value.type) {
        case VAL_NIL: fprintf(stream, "nil"); break;
        case VAL_BOOL: fprintf(stream, AS_BOOL(value) ? "true" : "false"); break;
        case VAL_INT: fprintf(stream, "%lld", (long long)AS_INT(value)); break;
        case VAL_FLOAT: fprintf(stream, "%g", AS_FLOAT(value)); break;
        case VAL_STRING: fprintf(stream, "\"%s\"", AS_CSTRING(value)); break;
        case VAL_ARRAY: {
            ObjArray* arr = AS_ARRAY(value);
            fprintf(stream, "[");
            for (uint32_t i = 0; i < arr->items.count; i++) {
                if (i > 0) fprintf(stream, ", ");
                printValue(stream, arr->items.values[i]);
            }
            fprintf(stream, "]");
            break;
        }
        case VAL_MAP: {
            ObjMap* map = AS_MAP(value);
            fprintf(stream, "{");
            bool first = true;
            for (uint32_t i = 0; i < map->capacity; i++) {
                if (!IS_NIL(map->entries[i].key)) {
                    if (!first) fprintf(stream, ", ");
                    first = false;
                    printValue(stream, map->entries[i].key);
                    fprintf(stream, ": ");
                    printValue(stream, map->entries[i].value);
                }
            }
            fprintf(stream, "}");
            break;
        }
        case VAL_FUNCTION:
            if (AS_FUNCTION(value)->name)
                fprintf(stream, "<fn %s>", AS_FUNCTION(value)->name->chars);
            else
                fprintf(stream, "<fn script>");
            break;
        case VAL_NATIVE:
            fprintf(stream, "<native %s>", AS_NATIVE(value)->name ? AS_NATIVE(value)->name->chars : "fn");
            break;
        case VAL_CLOSURE:
            if (AS_CLOSURE(value)->function->name)
                fprintf(stream, "<fn %s>", AS_CLOSURE(value)->function->name->chars);
            else
                fprintf(stream, "<fn script>");
            break;
        case VAL_CLASS:
            fprintf(stream, "<class %s>", AS_CLASS(value)->name->chars);
            break;
        case VAL_INSTANCE:
            fprintf(stream, "<instance of %s>", AS_INSTANCE(value)->klass->name->chars);
            break;
        case VAL_BOUND_METHOD:
            fprintf(stream, "<bound method>");
            break;
        case VAL_UPVALUE:
            fprintf(stream, "<upvalue>");
            break;
        case VAL_FOREIGN:
            fprintf(stream, "<foreign>");
            break;
        case VAL_MODULE:
            fprintf(stream, "<module %s>", AS_MODULE(value)->name->chars);
            break;
        default:
            fprintf(stream, "<unknown>");
            break;
    }
}
