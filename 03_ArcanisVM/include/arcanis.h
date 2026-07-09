#ifndef ARCANIS_H
#define ARCANIS_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* VM instance opaque handle */
typedef struct ArcanisVM ArcanisVM;
typedef struct ArcanisValue ArcanisValue;

/* Result codes */
typedef enum {
    ARCANIS_OK = 0,
    ARCANIS_ERR_COMPILE,
    ARCANIS_ERR_RUNTIME,
    ARCANIS_ERR_MEMORY,
    ARCANIS_ERR_STACK_OVERFLOW,
    ARCANIS_ERR_SANDBOX,
    ARCANIS_ERR_MODULE_NOT_FOUND,
    ARCANIS_ERR_INVALID_ARG,
} ArcanisResult;

/* Value types */
typedef enum {
    ARCANIS_NIL,
    ARCANIS_BOOL,
    ARCANIS_INT,
    ARCANIS_FLOAT,
    ARCANIS_STRING,
    ARCANIS_ARRAY,
    ARCANIS_MAP,
    ARCANIS_FUNCTION,
    ARCANIS_OBJECT,
} ArcanisValueType;

/* Create a new VM instance */
ArcanisVM* arcanis_create(void);

/* Destroy a VM instance */
void arcanis_destroy(ArcanisVM* vm);

/* Execute Arcanis source code */
ArcanisResult arcanis_execute(ArcanisVM* vm, const char* source, size_t length);

/* Execute Arcanis source from file */
ArcanisResult arcanis_execute_file(ArcanisVM* vm, const char* path);

/* Register a native function */
typedef ArcanisValue (*ArcanisNativeFn)(int argc, ArcanisValue* argv, void* userdata);
ArcanisResult arcanis_register_function(ArcanisVM* vm, const char* name, ArcanisNativeFn fn, void* userdata);

/* Get a global variable */
ArcanisValue arcanis_get_global(ArcanisVM* vm, const char* name);

/* Set a global variable */
ArcanisResult arcanis_set_global(ArcanisVM* vm, const char* name, ArcanisValue value);

/* Value constructors */
ArcanisValue arcanis_nil(void);
ArcanisValue arcanis_bool(bool val);
ArcanisValue arcanis_int(int64_t val);
ArcanisValue arcanis_float(double val);
ArcanisValue arcanis_string(ArcanisVM* vm, const char* str);
ArcanisValue arcanis_array(ArcanisVM* vm, ArcanisValue* items, size_t count);

/* Value inspectors */
ArcanisValueType arcanis_type(ArcanisValue val);
bool arcanis_is_nil(ArcanisValue val);
bool arcanis_is_bool(ArcanisValue val);
bool arcanis_is_int(ArcanisValue val);
bool arcanis_is_float(ArcanisValue val);
bool arcanis_is_string(ArcanisValue val);
bool arcanis_is_array(ArcanisValue val);
bool arcanis_is_map(ArcanisValue val);

/* Value accessors */
bool arcanis_as_bool(ArcanisValue val);
int64_t arcanis_as_int(ArcanisValue val);
double arcanis_as_float(ArcanisValue val);
const char* arcanis_as_string(ArcanisValue val);
size_t arcanis_array_length(ArcanisValue val);
ArcanisValue arcanis_array_get(ArcanisValue val, size_t index);

/* Garbage collection */
void arcanis_gc_collect(ArcanisVM* vm);
void arcanis_gc_enable(ArcanisVM* vm);
void arcanis_gc_disable(ArcanisVM* vm);

/* Debugger */
void arcanis_debugger_enable(ArcanisVM* vm);
void arcanis_debugger_disable(ArcanisVM* vm);
void arcanis_debugger_set_breakpoint(ArcanisVM* vm, const char* file, unsigned int line);

/* Sandbox */
void arcanis_sandbox_enable(ArcanisVM* vm);
void arcanis_sandbox_disable(ArcanisVM* vm);
void arcanis_sandbox_set_memory_limit(ArcanisVM* vm, uint64_t max_bytes);
void arcanis_sandbox_set_instruction_limit(ArcanisVM* vm, uint64_t max_instructions);

/* Error handling */
const char* arcanis_last_error(ArcanisVM* vm);

/* Version */
const char* arcanis_version(void);

#ifdef __cplusplus
}
#endif

#endif
