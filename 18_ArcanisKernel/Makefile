# =============================================================================
# ArcanisKernel Build System
# =============================================================================
# Requirements: NASM, i686-elf-gcc cross compiler, GNU ld
# =============================================================================

# Toolchain
CC       = i686-elf-gcc
LD       = i686-elf-ld
NASM     = nasm
QEMU     = qemu-system-i386

# Flags
CFLAGS   = -m32 -ffreestanding -nostdlib -nostdinc -fno-builtin -fno-stack-protector \
           -nostartfiles -nodefaultlibs -Wall -Wextra -c -Iinclude
LDFLAGS  = -m elf_i386 -T linker.ld --oformat binary
NASMFLAGS = -f bin

# Directories
SRC_DIR  = src
BUILD_DIR = build
OBJ_DIR  = $(BUILD_DIR)/obj

# Source files
BOOT_SRC   = $(SRC_DIR)/boot/boot.asm
ENTRY_SRC  = $(SRC_DIR)/boot/entry.asm
ISR_SRC    = $(SRC_DIR)/interrupts/isr.asm
IRQ_SRC    = $(SRC_DIR)/interrupts/irq.asm
GDT_ASM    = $(SRC_DIR)/interrupts/gdt_flush.asm
SYSCALL_ASM = $(SRC_DIR)/syscall/syscall_entry.asm
CTX_ASM    = $(SRC_DIR)/process/context_switch.asm

C_SOURCES = $(wildcard $(SRC_DIR)/kernel/*.c) \
            $(wildcard $(SRC_DIR)/drivers/*.c) \
            $(wildcard $(SRC_DIR)/memory/*.c) \
            $(wildcard $(SRC_DIR)/process/*.c) \
            $(wildcard $(SRC_DIR)/interrupts/*.c) \
            $(wildcard $(SRC_DIR)/syscall/*.c) \
            $(wildcard $(SRC_DIR)/fs/*.c) \
            $(wildcard $(SRC_DIR)/security/*.c) \
            $(wildcard $(SRC_DIR)/net/*.c)

ASM_SOURCES = $(ENTRY_SRC) $(ISR_SRC) $(IRQ_SRC) $(GDT_ASM) $(SYSCALL_ASM) $(CTX_ASM)

# Object files
C_OBJECTS   = $(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(C_SOURCES))
ASM_OBJECTS = $(patsubst $(SRC_DIR)/%.asm, $(OBJ_DIR)/%.o, $(ASM_SOURCES))
ALL_OBJECTS = $(ASM_OBJECTS) $(C_OBJECTS)

# Output
KERNEL_BIN  = $(BUILD_DIR)/arcanis.bin
KERNEL_ISO  = $(BUILD_DIR)/arcanis.iso
BOOT_BIN    = $(BUILD_DIR)/boot.bin

# Targets
.PHONY: all clean run debug test iso help

all: $(KERNEL_ISO)

help:
	@echo "ArcanisKernel Build System"
	@echo "========================="
	@echo "  make all    - Build kernel ISO"
	@echo "  make run    - Run in QEMU"
	@echo "  make debug  - Run with GDB stub"
	@echo "  make test   - Run test suite"
	@echo "  make clean  - Clean build artifacts"
	@echo "  make iso    - Create bootable ISO"
	@echo "  make size   - Show kernel size"

$(KERNEL_ISO): $(BOOT_BIN) $(KERNEL_BIN)
	@mkdir -p $(BUILD_DIR)/iso/boot
	@cp $(BOOT_BIN) $(BUILD_DIR)/iso/boot/boot.bin
	@cp $(KERNEL_BIN) $(BUILD_DIR)/iso/boot/kernel.bin
	@# Create a simple bootable image
	@cat $(BOOT_BIN) $(KERNEL_BIN) > $(BUILD_DIR)/arcanis.img
	@echo "Build complete: $(BUILD_DIR)/arcanis.img"

$(BOOT_BIN): $(SRC_DIR)/boot/boot.asm
	@mkdir -p $(BUILD_DIR)
	$(NASM) -f bin $< -o $@

$(KERNEL_BIN): $(ENTRY_BIN) $(ALL_OBJECTS)
	@mkdir -p $(BUILD_DIR)
	$(LD) $(LDFLAGS) -o $@ $(ENTRY_BIN) $(ALL_OBJECTS)
	@echo "Kernel built: $@"

$(ENTRY_BIN): $(ENTRY_SRC)
	@mkdir -p $(BUILD_DIR)
	$(NASM) -f bin $< -o $@

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.asm
	@mkdir -p $(dir $@)
	$(NASM) -f elf32 $< -o $@

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $< -o $@

run: $(KERNEL_ISO)
	$(QEMU) -kernel $(KERNEL_BIN) -m 128M -serial stdio

debug: $(KERNEL_ISO)
	$(QEMU) -kernel $(KERNEL_BIN) -m 128M -serial stdio -s -S &

test:
	@echo "Running ArcanisKernel test suite..."
	@echo "Tests can be run inside the kernel shell with 'test' command"
	@echo "Or use the test framework in tests/"

iso: $(KERNEL_ISO)

size: $(KERNEL_BIN)
	@echo "Kernel size: $$(wc -c < $(KERNEL_BIN)) bytes"

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(ALL_OBJECTS)
	@echo "Clean complete"
