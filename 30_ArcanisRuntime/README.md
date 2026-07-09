# ArcanisRuntime

**Project ID:** 30-ArcanisRuntime
**Phase:** 1 — Research & Prototyping (Q2 2027)
**Status:** Implemented
**Language:** C (bare-metal, freestanding)

## Overview

ArcanisRuntime is the foundational runtime library for the Arcanis ecosystem. It provides the memory management primitives that the kernel, shell, and all user-space programs depend on. This is the **critical path** dependency — nothing else can progress without it.

## Components

| Module | File | Description |
|--------|------|-------------|
| **PMM** | `pmm.c` | Bitmap-based physical memory manager. Allocates/frees 4KB blocks. |
| **VMM** | `vmm.c` | Two-level page table virtual memory manager. Maps virtual→physical addresses. |
| **Heap** | `heap.c` | First-fit kernel heap allocator with block splitting, coalescing, and alignment. |
| **String** | `string.c` | Freestanding string/memory utilities (no libc dependency). |
| **Runtime** | `runtime.c` | Top-level initialization that wires PMM → VMM → Heap together. |

## API

```c
#include <arcanis/runtime.h>

// Initialize the runtime (call once at boot)
arc_status_t arc_runtime_init(uint32_t mem_map_base, uint32_t mem_map_size);

// Allocate memory
void* arc_aligned_alloc(size_t size, size_t alignment);
void* arc_calloc(size_t count, size_t size);
void* arc_realloc(void* ptr, size_t new_size);
void  arc_free(void* ptr);

// Query memory state
size_t arc_get_used_memory(void);
size_t arc_get_free_memory(void);
```

## Low-Level API

```c
#include <arcanis/pmm.h>    // Physical memory
#include <arcanis/vmm.h>    // Virtual memory
#include <arcanis/heap.h>   // Kernel heap
#include <arcanis/string.h> // String utilities
```

## Building

```bash
make          # Build libarcanis_runtime.a
make clean    # Remove build artifacts
make test     # Run test suite
```

**Prerequisites:** `i686-elf-gcc` cross compiler, `i686-elf-ar`, `nasm`

## Memory Layout

```
0x00000000 - 0x000FFFFF  BIOS/IVT/Real Mode (1MB)
0x00100000 - 0x00FFFFFF  Kernel Space (1MB - 16MB)
0x08000000 - 0x0BFFFFFF  Kernel Heap (64MB default)
0xC0000000 - 0xFFFFFFFF  Kernel Virtual Mapping
```

## Integration

This library is designed to be linked into:
- **18_ArcanisKernel** — provides the memory subsystem
- **31_ArcanisContainer** — container memory isolation
- Any bare-metal C project in the ecosystem

## License

All rights reserved. ArcanisLabs — Sagar Makani.
