# ArcanisKernel Testing Guide

## Test Types

### 1. In-Kernel Tests

Built into the kernel shell, accessible via the `test` command.

**Test Categories:**
- String operations (strlen, strcpy, strcmp, memset, memcpy)
- Memory management (PMM, heap)
- Interrupt handling (IDT, timer, keyboard)
- VGA display

### 2. Unit Tests

Located in `tests/` directory. Run via the test framework.

### 3. Integration Tests

Test interaction between subsystems:
- Process creation and scheduling
- System call invocation
- Memory mapping across processes

### 4. Stress Tests

- Memory exhaustion
- Process creation limits
- Interrupt storm handling

## Running Tests

### Quick Test

```bash
make run
# In kernel shell:
test
```

### Test Output

```
========================================
    ArcanisKernel Test Suite
========================================
--- String Operations Tests ---
  [PASS] strlen basic
  [PASS] strlen empty
  [PASS] strcpy/strcmp
  [PASS] memset
  [PASS] memcpy/memcmp
  [PASS] itoa decimal
  [PASS] itoa hex
--- Memory Operations Tests ---
  [PASS] PMM alloc block
  [PASS] PMM alloc second block
  [PASS] PMM blocks differ
  [PASS] Heap alloc 32 bytes
  [PASS] Heap alloc 64 bytes
  [PASS] Heap allocs differ
========================================
    Results
========================================
  Total:   13
  Passed:  13
========================================
```

## Writing New Tests

### Test Structure

```c
#include <arcanis/test.h>

int my_test(void) {
    // Setup
    int result = 0;

    // Test logic
    test_assert(result == expected, "Test description");

    return TEST_PASS;
}
```

### Test Registration

Add test cases to `tests/test_suite.c`:

```c
static test_case_t tests[] = {
    { "String ops", test_string_ops },
    { "Memory ops", test_memory_ops },
    { "My test",    my_test },
};
```

## Debugging

### Serial Output

All kernel messages are printed to COM1 (serial port):

```bash
# In QEMU, serial output appears in terminal
make run
```

### GDB Debugging

```bash
# Start QEMU with GDB stub
make debug

# In another terminal
i686-elf-gdb
(gdb) target remote localhost:1234
(gdb) break isr_handler
(gdb) continue
```

### Common Issues

1. **Kernel doesn't boot**: Check bootloader assembly, ensure NASM output format is correct
2. **Triple fault**: IDT setup issue, check ISR/IRQ stubs
3. **Page fault on boot**: VMM initialization, check page directory setup
4. **No display**: VGA buffer address, check 0xB8000 mapping
