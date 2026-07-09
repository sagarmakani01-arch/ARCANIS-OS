# ArcanisVM Public API Reference

## Integration with ArcanisOS

The public API is defined in `include/arcanis.h` and provides a stable C interface for embedding ArcanisVM into host applications.

## Core Functions

### VM Lifecycle

```c
ArcanisVM* arcanis_create(void);
```
Creates a new VM instance with initialized memory manager, GC, and runtime.

```c
void arcanis_destroy(ArcanisVM* vm);
```
Destroys the VM and frees all allocated memory.

### Execution

```c
ArcanisResult arcanis_execute(ArcanisVM* vm, const char* source, size_t length);
```
Compiles and executes Arcanis source code.

```c
ArcanisResult arcanis_execute_file(ArcanisVM* vm, const char* path);
```
Reads, compiles, and executes a file.

### Native Function Registration

```c
typedef ArcanisValue (*ArcanisNativeFn)(int argc, ArcanisValue* argv, void* userdata);

ArcanisResult arcanis_register_function(
    ArcanisVM* vm,
    const char* name,
    ArcanisNativeFn fn,
    void* userdata
);
```
Registers a C function as a callable Arcanis function.

### Global Variables

```c
ArcanisValue arcanis_get_global(ArcanisVM* vm, const char* name);
ArcanisResult arcanis_set_global(ArcanisVM* vm, const char* name, ArcanisValue value);
```

## Value API

### Constructors

```c
ArcanisValue arcanis_nil(void);
ArcanisValue arcanis_bool(bool val);
ArcanisValue arcanis_int(int64_t val);
ArcanisValue arcanis_float(double val);
ArcanisValue arcanis_string(ArcanisVM* vm, const char* str);
ArcanisValue arcanis_array(ArcanisVM* vm, ArcanisValue* items, size_t count);
```

### Type Inspection

```c
ArcanisValueType arcanis_type(ArcanisValue val);
bool arcanis_is_nil(ArcanisValue val);
bool arcanis_is_bool(ArcanisValue val);
// ... etc
```

### Value Accessors

```c
bool arcanis_as_bool(ArcanisValue val);
int64_t arcanis_as_int(ArcanisValue val);
double arcanis_as_float(ArcanisValue val);
const char* arcanis_as_string(ArcanisValue val);
```

## Advanced Features

### Garbage Collection

```c
void arcanis_gc_collect(ArcanisVM* vm);
void arcanis_gc_enable(ArcanisVM* vm);
void arcanis_gc_disable(ArcanisVM* vm);
```

### Debugger

```c
void arcanis_debugger_enable(ArcanisVM* vm);
void arcanis_debugger_disable(ArcanisVM* vm);
void arcanis_debugger_set_breakpoint(ArcanisVM* vm, const char* file, unsigned int line);
```

### Sandbox

```c
void arcanis_sandbox_enable(ArcanisVM* vm);
void arcanis_sandbox_disable(ArcanisVM* vm);
void arcanis_sandbox_set_memory_limit(ArcanisVM* vm, uint64_t max_bytes);
void arcanis_sandbox_set_instruction_limit(ArcanisVM* vm, uint64_t max_instructions);
```

### Error Handling

```c
const char* arcanis_last_error(ArcanisVM* vm);
```

## Integration Example

```c
#include "arcanis.h"
#include <stdio.h>

int main() {
    ArcanisVM* vm = arcanis_create();

    // Register a custom native function
    arcanis_register_function(vm, "hello",
        (ArcanisNativeFn)[](int argc, ArcanisValue* argv, void* ud) {
            printf("Hello from C!\n");
            return arcanis_nil();
        }, NULL);

    // Execute Arcanis code
    const char* code = "print('Hello from Arcanis!'); hello();";
    ArcanisResult r = arcanis_execute(vm, code, strlen(code));

    if (r != ARCANIS_OK) {
        fprintf(stderr, "Error: %s\n", arcanis_last_error(vm));
    }

    arcanis_destroy(vm);
    return 0;
}
```
