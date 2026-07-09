# ArcanisKernel Build Guide

## Prerequisites

### Toolchain

ArcanisKernel requires an i686-elf cross-compiler toolchain:

1. **NASM** (Netwide Assembler) - For assembly files
2. **i686-elf-gcc** - Cross-compiler for kernel code
3. **GNU LD** (i686-elf-ld) - Linker
4. **QEMU** (optional) - For testing

### Installing on Ubuntu/Debian

```bash
sudo apt update
sudo apt install nasm qemu-system-x86 build-essential

# Build cross-compiler (or download pre-built)
export TARGET=i686-elf
export PREFIX="$HOME/opt/cross"
export PATH="$PREFIX/bin:$PATH"

mkdir -p $HOME/src
cd $HOME/src

# Download binutils
wget https://ftp.gnu.org/gnu/binutils/binutils-2.41.tar.xz
tar xf binutils-2.41.tar.xz
mkdir -p build-binutils
cd build-binutils
../binutils-2.41/configure --target=$TARGET --prefix=$PREFIX \
    --with-sysroot --disable-nls --disable-werror
make -j$(nproc)
make install

# Download GCC
cd $HOME/src
wget https://ftp.gnu.org/gnu/gcc/gcc-13.2.0/gcc-13.2.0.tar.xz
tar xf gcc-13.2.0.tar.xz
mkdir -p build-gcc
cd build-gcc
../gcc-13.2.0/configure --target=$TARGET --prefix=$PREFIX \
    --disable-nls --enable-languages=c --without-headers
make -j$(nproc) all-gcc all-target-libgcc
make install-gcc install-target-libgcc
```

### Installing on Windows

1. Install WSL2 or use a Linux VM
2. Follow Ubuntu instructions above
3. Or use pre-built toolchain from [OSDev Wiki](https://wiki.osdev.org/GCC_Cross-Compiler)

### Installing on macOS

```bash
brew install nasm qemu
# Build cross-compiler following Linux instructions
```

## Building

### Quick Build

```bash
make all
```

### Build Targets

```bash
make all      # Build kernel image
make run      # Run in QEMU (128MB RAM)
make debug    # Run with GDB stub (port 1234)
make test     # Run test suite
make clean    # Clean build artifacts
make iso      # Create bootable ISO
make size     # Show kernel size
make help     # Show all targets
```

### Manual Build

```bash
# Create build directory
mkdir -p build

# Assemble boot sector
nasm -f bin src/boot/boot.asm -o build/boot.bin

# Assemble kernel entry
nasm -f bin src/boot/entry.asm -o build/entry.bin

# Assemble ASM stubs
nasm -f elf32 src/interrupts/isr.asm -o build/isr.o
nasm -f elf32 src/interrupts/irq.asm -o build/irq.o
nasm -f elf32 src/interrupts/gdt_flush.asm -o build/gdt_flush.o
nasm -f elf32 src/syscall/syscall_entry.asm -o build/syscall_entry.o
nasm -f elf32 src/process/context_switch.asm -o build/context_switch.o

# Compile C sources
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/kernel/kernel.c -o build/kernel.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/kernel/string.c -o build/string.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/kernel/printf.c -o build/printf.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/drivers/vga.c -o build/vga.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/drivers/keyboard.c -o build/keyboard.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/drivers/timer.c -o build/timer.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/drivers/serial.c -o build/serial.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/memory/pmm.c -o build/pmm.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/memory/vmm.c -o build/vmm.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/memory/heap.c -o build/heap.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/process/process.c -o build/process.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/process/scheduler.c -o build/scheduler.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/interrupts/gdt.c -o build/gdt.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/interrupts/idt.c -o build/idt.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/interrupts/isr.c -o build/isr_handler.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/interrupts/irq.c -o build/irq_handler.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/syscall/syscall.c -o build/syscall.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/fs/vfs.c -o build/vfs.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/fs/initrd.c -o build/initrd.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/security/security.c -o build/security.o
i686-elf-gcc -m32 -ffreestanding -nostdlib -c src/net/net.c -o build/net.o

# Link
i686-elf-ld -m elf_i386 -T linker.ld --oformat binary \
    -o build/arcanis.bin build/*.o

# Create bootable image
cat build/boot.bin build/arcanis.bin > build/arcanis.img
```

## Testing

### Running in QEMU

```bash
make run
```

This launches QEMU with:
- 128MB RAM
- Serial output to terminal
- VGA display window

### GDB Debugging

```bash
# Terminal 1: Start QEMU with GDB stub
make debug

# Terminal 2: Connect GDB
i686-elf-gdb
(gdb) target remote localhost:1234
(gdb) break kernel_main
(gdb) continue
```

### In-Kernel Testing

Once the kernel boots, use the `test` command:

```
arcanis@kernel > test
```

This runs the built-in test suite covering:
- String operations
- Memory management
- Interrupt handling
- VGA display
- Timer functionality
