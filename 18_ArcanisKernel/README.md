# ArcanisKernel

## Overview

ArcanisKernel is an independent operating system kernel built from first principles for the x86 architecture. It implements core OS concepts including protected mode bootloading, memory management, process scheduling, interrupt handling, and a driver framework.

## Architecture

### Boot Process

1. **BIOS loads bootloader** at 0x7C00
2. **Bootloader** sets up segments, enables A20 line
3. **Loads kernel** from disk using INT 13h extensions
4. **Enables Protected Mode** by setting CR0 bit 0
5. **Jumps to kernel entry** at 0x10000

### Memory Layout

```
0x00000000 - 0x000FFFFF  BIOS/IVT/Real Mode (1MB)
0x00100000 - 0x00FFFFFF  Kernel Space (1MB - 16MB)
0x00100000 - 0x0010FFFF  Boot Sector
0x00110000 - 0x0011FFFF  Kernel Code/Data
0x00200000 - 0x00FFFFFF  PMM Bitmap + Available
0x07FF0000 - 0x07FFFFFF  User Stack
0x08000000 - 0x0BFFFFFF  Kernel Heap
0x0C000000 - 0x0FFFFFFF  Kernel Mapped Memory
0xB8000000 - 0xB8FFFFFF  VGA Text Buffer
0xFFC00000 - 0xFFFFFFFF  Page Directory (Recursive)
```

### Kernel Components

#### 1. Global Descriptor Table (GDT)
- Ring 0 code/data segments
- Ring 3 user code/data segments
- Task State Segment (TSS)

#### 2. Interrupt Descriptor Table (IDT)
- 32 CPU exception handlers (ISR 0-31)
- 16 hardware IRQ handlers (IRQ 0-15)
- System call interface (INT 0x80)

#### 3. Memory Management
- **PMM**: Bitmap-based physical memory manager
- **VMM**: Two-level page table virtual memory
- **Heap**: First-fit kernel heap allocator

#### 4. Process Management
- Process creation/destruction
- Context switching via assembly
- Priority-based preemptive scheduling

#### 5. Drivers
- **VGA**: 80x25 text mode with cursor control
- **Keyboard**: PS/2 keyboard with scancode translation
- **Timer**: PIT 8253 at configurable frequency
- **Serial**: COM1 for debugging output

#### 6. Security
- Ring 0/3 separation
- ASLR (Address Space Layout Randomization)
- Protected memory ranges

#### 7. Networking Foundation
- Ethernet frame handling
- ARP packet structure
- IP header processing
- Network interface abstraction

### System Calls

| Syscall | Number | Description |
|---------|--------|-------------|
| EXIT    | 0      | Terminate process |
| FORK    | 1      | Create child process |
| EXEC    | 2      | Execute program |
| READ    | 3      | Read from file |
| WRITE   | 4      | Write to file |
| OPEN    | 5      | Open file |
| CLOSE   | 6      | Close file |
| SLEEP   | 7      | Sleep for milliseconds |
| GETPID  | 8      | Get process ID |
| PUTCHAR | 9      | Print character |
| GETCHAR | 10     | Read character |
| CLS     | 11     | Clear screen |
| INFO    | 12     | System info |
| EXEC_CMD| 13     | Execute command |

## Building

### Prerequisites

- **NASM**: Netwide Assembler
- **GCC Cross Compiler**: i686-elf-gcc
- **GNU LD**: i686-elf-ld
- **QEMU**: For testing (optional)

### Build Commands

```bash
make all      # Build kernel image
make run      # Run in QEMU
make debug    # Run with GDB stub
make test     # Run test suite
make clean    # Clean build artifacts
make size     # Show kernel size
```

### Manual Build

```bash
# Assemble boot sector
nasm -f bin src/boot/boot.asm -o build/boot.bin

# Assemble kernel entry
nasm -f bin src/boot/entry.asm -o build/entry.bin

# Assemble ISR/IRQ stubs
nasm -f elf32 src/interrupts/isr.asm -o build/isr.o
nasm -f elf32 src/interrupts/irq.asm -o build/irq.o
nasm -f elf32 src/interrupts/gdt_flush.asm -o build/gdt_flush.o
nasm -f elf32 src/syscall/syscall_entry.asm -o build/syscall_entry.o
nasm -f elf32 src/process/context_switch.asm -o build/context_switch.o

# Compile C sources
for f in src/kernel/*.c src/drivers/*.c src/memory/*.c src/process/*.c \
         src/interrupts/*.c src/syscall/*.c src/fs/*.c src/security/*.c \
         src/net/*.c; do
    i686-elf-gcc -m32 -ffreestanding -nostdlib -c $f -o build/$(basename $f .c).o
done

# Link
i686-elf-ld -m elf_i386 -T linker.ld --oformat binary -o build/arcanis.bin build/*.o
```

## Testing

### In-Kernel Tests

The kernel includes a built-in test framework accessible via the `test` command in the shell. Tests cover:

- String operations (strlen, strcpy, strcmp, memset, memcpy)
- Memory management (PMM allocation, heap allocation)
- Interrupt handling (IDT setup, timer, keyboard)
- VGA display functionality

### Running Tests

```bash
make run
# Inside kernel shell:
test
```

## Documentation

- `docs/ARCHITECTURE.md` - Detailed architecture document
- `docs/API.md` - System call and function reference
- `docs/BUILDING.md` - Build instructions and toolchain setup
- `docs/TESTING.md` - Testing procedures

## Project Structure

```
ArcanisKernel/
├── src/
│   ├── boot/           # Bootloader and entry point
│   │   ├── boot.asm    # Stage 1 bootloader
│   │   └── entry.asm   # Kernel entry point
│   ├── kernel/         # Core kernel
│   │   ├── kernel.c    # Main kernel + shell
│   │   ├── string.c    # String functions
│   │   └── printf.c    # Kernel printf
│   ├── drivers/        # Device drivers
│   │   ├── vga.c       # VGA text mode
│   │   ├── keyboard.c  # PS/2 keyboard
│   │   ├── timer.c     # PIT timer
│   │   └── serial.c    # Serial port
│   ├── memory/         # Memory management
│   │   ├── pmm.c       # Physical memory manager
│   │   ├── vmm.c       # Virtual memory manager
│   │   └── heap.c      # Kernel heap
│   ├── process/        # Process management
│   │   ├── process.c   # Process lifecycle
│   │   ├── scheduler.c # Priority scheduler
│   │   └── context_switch.asm  # Context switch
│   ├── interrupts/     # Interrupt handling
│   │   ├── gdt.c       # GDT setup
│   │   ├── idt.c       # IDT setup
│   │   ├── isr.c       # Exception handlers
│   │   ├── irq.c       # Hardware interrupt handlers
│   │   ├── isr.asm     # ISR stubs
│   │   ├── irq.asm     # IRQ stubs
│   │   └── gdt_flush.asm  # GDT flush
│   ├── syscall/        # System calls
│   │   ├── syscall.c   # Syscall handler
│   │   └── syscall_entry.asm  # INT 0x80 stub
│   ├── fs/             # File system
│   │   ├── vfs.c       # Virtual file system
│   │   └── initrd.c    # Initial ramdisk
│   ├── security/       # Security model
│   │   └── security.c  # ASLR, access control
│   └── net/            # Networking
│       └── net.c       # Network stack foundation
├── include/
│   └── arcanis/        # Kernel headers
├── tests/              # Test framework
├── docs/               # Documentation
├── tools/              # Build tools
├── Makefile            # Build system
└── linker.ld           # Linker script
```

## Security Model

### Protection Rings

- **Ring 0 (Kernel)**: Full hardware access, privileged instructions
- **Ring 3 (User)**: Limited access, memory protection

### Memory Protection

- Page-level access control
- User/supervisor page flags
- Write protection

### ASLR

- Randomized stack/heap placement
- Entropy-based offset generation

## License

ArcanisKernel is developed as an independent research OS kernel.
