# ArcanisOS Integration Guide

## Embedding ArcanisVM

ArcanisVM is designed from the ground up for tight integration with ArcanisOS. The architecture supports three integration modes:

### 1. Embedded Library (Recommended)

Link `libarcanis.a` or `arcanis.dll` into your application.

**CMake integration:**
```cmake
find_library(ARCANIS_LIB arcanis)
find_path(ARCANIS_INCLUDE arcanis.h)
target_link_libraries(myapp ${ARCANIS_LIB})
target_include_directories(myapp PRIVATE ${ARCANIS_INCLUDE})
```

**Initialization:**
```c
#include <arcanis.h>

void init_system() {
    ArcanisVM* vm = arcanis_create();

    // Register ArcanisOS system calls
    arcanis_register_function(vm, "os_open",  sys_open,  NULL);
    arcanis_register_function(vm, "os_read",  sys_read,  NULL);
    arcanis_register_function(vm, "os_write", sys_write, NULL);
    arcanis_register_function(vm, "os_close", sys_close, NULL);

    // Set up IPC
    arcanis_register_function(vm, "ipc_send", ipc_send,  NULL);
    arcanis_register_function(vm, "ipc_recv", ipc_recv,  NULL);

    // Enable sandbox for untrusted code
    arcanis_sandbox_enable(vm);

    // Execute system scripts
    arcanis_execute_file(vm, "/system/init.arc");
}
```

### 2. Standalone Process

Run `arcanisvm` as a subprocess with stdin/stdout communication.

**Protocol:**
```
-> {"cmd": "exec", "source": "print(1+2)"}
<- {"result": "3"}
```

### 3. Plugin Architecture

ArcanisVM can load native plugins that extend its capabilities.

**Plugin example:**
```c
#include <arcanis/plugin.h>

Plugin* createPlugin() {
    Plugin* p = calloc(1, sizeof(Plugin));
    p->name = "my_plugin";
    p->version = "1.0.0";
    p->onLoad = my_on_load;
    p->onImport = my_on_import;
    return p;
}
```

## Security Architecture

### Sandbox Layers

1. **Opcode filtering** - Block dangerous operations at the VM level
2. **Resource limits** - Memory, instructions, call depth
3. **Native function whitelist** - Only approved syscalls available
4. **Plugin verification** - Signed plugin loading

### Recommended Sandbox Configuration

```c
void configure_sandbox(ArcanisVM* vm) {
    // Restrict resources
    arcanis_sandbox_set_memory_limit(vm, 64 * 1024 * 1024);       // 64MB
    arcanis_sandbox_set_instruction_limit(vm, 10 * 1000 * 1000);   // 10M instr

    // Load whitelist of approved functions
    const char* whitelist[] = {
        "print", "len", "type", "toString",
        "arrayPush", "arrayPop", "arraySlice",
        "mapKeys", "mapValues", "mapHas",
        "clock", "assert"
    };
}
```

## Performance Tuning

### GC Tuning

```c
// Adjust GC threshold (default: 1MB)
// Lower = more frequent, shorter pauses
// Higher = less frequent, longer pauses
arcanis_gc_collect(vm);  // Force immediate collection
```

### Profiling for Optimization

```bash
arcanisvm --profile --eval "your_code"
```

This produces an opcode frequency report showing hot spots.

## Error Handling

VM execution errors are propagated through:
1. Return codes from `arcanis_execute()`
2. Error message via `arcanis_last_error()`
3. Stderr output with source line numbers

## Building for ArcanisOS

```bash
# Cross-compile for ArcanisOS
make CC=arcanis-unknown-arcanis-gcc
```
