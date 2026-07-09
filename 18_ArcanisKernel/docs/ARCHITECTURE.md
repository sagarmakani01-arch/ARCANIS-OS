# ArcanisKernel Architecture

## System Overview

ArcanisKernel is a monolithic kernel designed for x86 (i686) processors. It runs in protected mode with 32-bit addressing and implements a complete kernel subsystem stack from bootloader to shell.

## Boot Architecture

### Stage 1: Real Mode (16-bit)

The BIOS loads the boot sector (512 bytes) to address 0x7C00. The bootloader:

1. Initializes segment registers and stack
2. Enables the A20 gate for >1MB addressing
3. Loads kernel sectors from disk via INT 13h extensions
4. Loads the Global Descriptor Table (GDT)
5. Enables protected mode by setting CR0.PE
6. Performs a far jump to flush the pipeline

### Stage 2: Protected Mode (32-bit)

The kernel entry point clears the BSS section and calls `kernel_main()`, which initializes all subsystems in dependency order.

## Interrupt Architecture

### PIC (Programmable Interrupt Controller)

The 8259 PIC is remapped to avoid conflicts with CPU exceptions:
- Master PIC: IRQ 0-7 → INT 32-39
- Slave PIC: IRQ 8-15 → INT 40-47

### Exception Handling

CPU exceptions (INT 0-31) are handled by ISR stubs that:
1. Push a dummy error code (if CPU doesn't)
2. Push the interrupt number
3. Save all registers to a stack frame
4. Call the C exception handler

### Hardware Interrupts

IRQ 0-15 are handled similarly but with automatic PIC acknowledgment (EOI).

### System Calls

INT 0x80 provides the system call interface from ring 3 to ring 0.

## Memory Architecture

### Physical Memory Manager (PMM)

- Bitmap-based allocation
- 4KB block granularity
- Tracks kernel regions to avoid corruption

### Virtual Memory Manager (VMM)

- Two-level page tables (Page Directory + Page Tables)
- Identity maps the first 4MB for initial boot
- Kernel mapped to higher half (0xC0000000+)
- User processes get separate address spaces

### Kernel Heap

- First-fit allocation strategy
- Coalescing of free blocks
- Used for dynamic kernel allocations

## Process Architecture

### Process Structure

Each process contains:
- Process ID (PID)
- Execution state
- Saved CPU context (registers, EIP, ESP, EFLAGS)
- Page directory pointer
- Kernel/user stack pointers
- Priority and time slice

### Context Switching

Assembly-level context switch saves/restores:
- General purpose registers (EAX, EBX, ECX, EDX, ESI, EDI, EBP)
- Instruction pointer (EIP) and stack pointer (ESP)
- Flags register (EFLAGS)
- Segment registers (CS, SS, DS, ES, FS, GS)
- Page directory (CR3)

### Scheduler

Priority-based preemptive scheduler:
- Higher priority processes get CPU first
- Time slices prevent starvation
- Timer interrupt triggers rescheduling

## Driver Architecture

### VGA Text Mode

- Direct memory-mapped I/O at 0xB8000
- 80x25 character display
- Hardware cursor control via CRT controller

### Keyboard (PS/2)

- IRQ 1 handler
- Scancode set 1 translation
- Shift/Ctrl modifier tracking

### Timer (PIT 8253)

- IRQ 0 handler
- Configurable frequency (default 100Hz)
- Used for preemptive scheduling

### Serial (COM1)

- 115200 baud, 8N1
- Debug output channel
- Can be redirected to host terminal

## Security Model

### Ring Separation

- Ring 0: Kernel code, full hardware access
- Ring 3: User code, restricted instructions
- TSS manages stack switching on ring transitions

### Memory Protection

- Page-level permissions (present, read/write, user/supervisor)
- Process isolation via separate page directories
- Kernel pages marked supervisor-only

### ASLR

- Entropy source: TSC (Time Stamp Counter)
- Randomized placement of user stacks and heaps
- Configurable entropy bits

## Networking Foundation

### Layer Model

- Layer 2: Ethernet frame parsing
- Layer 2.5: ARP protocol structure
- Layer 3: IP header processing
- Layer 4: UDP header support

### Interface Abstraction

- Named network interfaces
- MAC/IP address storage
- Send/receive callback registration
