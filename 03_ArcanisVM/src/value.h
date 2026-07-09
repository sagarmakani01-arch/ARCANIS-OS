#ifndef ARCANIS_VALUE_H
#define ARCANIS_VALUE_H

#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>

typedef enum {
    VAL_NIL,
    VAL_BOOL,
    VAL_INT,
    VAL_FLOAT,
    VAL_STRING,
    VAL_OBJECT,
    VAL_ARRAY,
    VAL_MAP,
    VAL_FUNCTION,
    VAL_NATIVE,
    VAL_CLOSURE,
    VAL_UPVALUE,
    VAL_BOUND_METHOD,
    VAL_CLASS,
    VAL_INSTANCE,
    VAL_MODULE,
    VAL_FOREIGN,
} ValueType;

typedef enum {
    OBJ_STRING,
    OBJ_ARRAY,
    OBJ_MAP,
    OBJ_FUNCTION,
    OBJ_NATIVE,
    OBJ_CLOSURE,
    OBJ_UPVALUE,
    OBJ_BOUND_METHOD,
    OBJ_CLASS,
    OBJ_INSTANCE,
    OBJ_MODULE,
    OBJ_FOREIGN,
} ObjType;

typedef struct Obj Obj;
typedef struct ObjString ObjString;
typedef struct ObjArray ObjArray;
typedef struct ObjMap ObjMap;
typedef struct ObjFunction ObjFunction;
typedef struct ObjNative ObjNative;
typedef struct ObjClosure ObjClosure;
typedef struct ObjUpvalue ObjUpvalue;
typedef struct ObjBoundMethod ObjBoundMethod;
typedef struct ObjClass ObjClass;
typedef struct ObjInstance ObjInstance;
typedef struct ObjModule ObjModule;
typedef struct ObjForeign ObjForeign;

typedef struct Value Value;
typedef struct ValueArray ValueArray;

typedef Value (*NativeFn)(int argCount, Value* args, void* context);

struct Obj {
    ObjType type;
    bool isMarked;
    Obj* next;
};

struct ObjString {
    Obj obj;
    uint32_t length;
    uint32_t hash;
    char chars[];
};

struct ObjArray {
    Obj obj;
    ValueArray items;
};

struct ObjMap {
    Obj obj;
    struct MapEntry* entries;
    uint32_t capacity;
    uint32_t count;
};

struct ObjFunction {
    Obj obj;
    uint32_t arity;
    uint32_t upvalueCount;
    ValueArray constants;
    uint32_t* bytecode;
    uint32_t bytecodeLen;
    uint32_t bytecodeCap;
    ObjString* name;
    uint32_t lineCount;
    uint32_t* lines;
};

struct ObjNative {
    Obj obj;
    NativeFn function;
    void* context;
    ObjString* name;
};

struct ObjUpvalue {
    Obj obj;
    Value* location;
    Value closed;
    struct ObjUpvalue* next;
};

struct ObjClosure {
    Obj obj;
    ObjFunction* function;
    ObjUpvalue** upvalues;
    uint32_t upvalueCount;
};

struct ObjBoundMethod {
    Obj obj;
    Value receiver;
    ObjClosure* method;
};

struct ObjClass {
    Obj obj;
    ObjString* name;
    struct Table* methods;
};

struct ObjInstance {
    Obj obj;
    ObjClass* klass;
    struct Table* fields;
};

struct ObjModule {
    Obj obj;
    ObjString* name;
    struct Table* globals;
};

struct ObjForeign {
    Obj obj;
    void* data;
    void (*destructor)(void*);
};

struct Value {
    ValueType type;
    union {
        bool boolean;
        int64_t integer;
        double floating;
        Obj* obj;
    } as;
};

#define IS_NIL(v)       ((v).type == VAL_NIL)
#define IS_BOOL(v)      ((v).type == VAL_BOOL)
#define IS_INT(v)       ((v).type == VAL_INT)
#define IS_FLOAT(v)     ((v).type == VAL_FLOAT)
#define IS_NUMBER(v)    ((v).type == VAL_INT || (v).type == VAL_FLOAT)
#define IS_STRING(v)    ((v).type == VAL_STRING)
#define IS_OBJECT(v)    ((v).type == VAL_OBJECT)
#define IS_ARRAY(v)     ((v).type == VAL_ARRAY)
#define IS_MAP(v)       ((v).type == VAL_MAP)
#define IS_FUNCTION(v)  ((v).type == VAL_FUNCTION)
#define IS_NATIVE(v)    ((v).type == VAL_NATIVE)
#define IS_CLOSURE(v)   ((v).type == VAL_CLOSURE)
#define IS_CLASS(v)     ((v).type == VAL_CLASS)
#define IS_INSTANCE(v)  ((v).type == VAL_INSTANCE)
#define IS_CALLABLE(v)  ((v).type == VAL_FUNCTION || (v).type == VAL_NATIVE || (v).type == VAL_CLOSURE || (v).type == VAL_BOUND_METHOD)
#define IS_FOREIGN(v)   ((v).type == VAL_FOREIGN)

#define AS_BOOL(v)      ((v).as.boolean)
#define AS_INT(v)       ((v).as.integer)
#define AS_FLOAT(v)     ((v).as.floating)
#define AS_NUMBER(v)    ((v).type == VAL_INT ? (double)(v).as.integer : (v).as.floating)
#define AS_STRING(v)    ((ObjString*)((v).as.obj))
#define AS_CSTRING(v)   (((ObjString*)((v).as.obj))->chars)
#define AS_ARRAY(v)     ((ObjArray*)((v).as.obj))
#define AS_MAP(v)       ((ObjMap*)((v).as.obj))
#define AS_FUNCTION(v)  ((ObjFunction*)((v).as.obj))
#define AS_NATIVE(v)    ((ObjNative*)((v).as.obj))
#define AS_CLOSURE(v)   ((ObjClosure*)((v).as.obj))
#define AS_CLASS(v)     ((ObjClass*)((v).as.obj))
#define AS_INSTANCE(v)  ((ObjInstance*)((v).as.obj))
#define AS_FOREIGN(v)   ((ObjForeign*)((v).as.obj))
#define AS_OBJ_TYPE(v)  (((Obj*)((v).as.obj))->type)

#define BOOL_VAL(v)     ((Value){VAL_BOOL, {.boolean = (v)}})
#define NIL_VAL         ((Value){VAL_NIL, {.integer = 0}})
#define INT_VAL(v)      ((Value){VAL_INT, {.integer = (v)}})
#define FLOAT_VAL(v)    ((Value){VAL_FLOAT, {.floating = (v)}})
#define OBJ_VAL(v)      ((Value){VAL_OBJECT, {.obj = (Obj*)(v)}})
#define STRING_VAL(v)   ((Value){VAL_STRING, {.obj = (Obj*)(v)}})
#define ARRAY_VAL(v)    ((Value){VAL_ARRAY, {.obj = (Obj*)(v)}})
#define MAP_VAL(v)      ((Value){VAL_MAP, {.obj = (Obj*)(v)}})
#define FUNCTION_VAL(v) ((Value){VAL_FUNCTION, {.obj = (Obj*)(v)}})
#define NATIVE_VAL(v)   ((Value){VAL_NATIVE, {.obj = (Obj*)(v)}})
#define CLOSURE_VAL(v)  ((Value){VAL_CLOSURE, {.obj = (Obj*)(v)}})
#define CLASS_VAL(v)    ((Value){VAL_CLASS, {.obj = (Obj*)(v)}})
#define INSTANCE_VAL(v) ((Value){VAL_INSTANCE, {.obj = (Obj*)(v)}})
#define FOREIGN_VAL(v)  ((Value){VAL_FOREIGN, {.obj = (Obj*)(v)}})

struct MapEntry {
    Value key;
    Value value;
    uint32_t hash;
};

struct Table {
    struct MapEntry* entries;
    uint32_t capacity;
    uint32_t count;
};

struct ValueArray {
    Value* values;
    uint32_t capacity;
    uint32_t count;
};

uint32_t hashString(const char* chars, uint32_t length);
void initValueArray(ValueArray* array);
void writeValueArray(ValueArray* array, Value value);
void freeValueArray(ValueArray* array);
void initTable(struct Table* table);
void freeTable(struct Table* table);
bool tableSet(struct Table* table, Value key, Value value);
bool tableGet(struct Table* table, Value key, Value* value);
bool tableDelete(struct Table* table, Value key);
void tableMarkAll(struct Table* table);

bool valuesEqual(Value a, Value b);
void printValue(FILE* stream, Value value);

#endif
