# ArcanisRuntime - Phase 1 Critical Path
# Runtime library for the Arcanis ecosystem

CC = i686-elf-gcc
AR = i686-elf-ar
NASM = nasm

CFLAGS = -m32 -ffreestanding -nostdlib -nostartfiles -nodefaultlibs \
         -Wall -Wextra -Werror -Iinclude -fno-builtin -fno-stack-protector \
         -nostdinc -fno-exceptions -nostdinc++

NASMFLAGS = -f elf32

SRC_DIR = src
BUILD_DIR = build
INCLUDE_DIR = include

SRCS = $(wildcard $(SRC_DIR)/*.c)
OBJS = $(patsubst $(SRC_DIR)/%.c, $(BUILD_DIR)/%.o, $(SRCS))
ASM_OBJS = $(wildcard $(BUILD_DIR)/*.asm.o)

LIB = $(BUILD_DIR)/libarcanis_runtime.a

.PHONY: all clean test info

all: $(LIB)

$(LIB): $(OBJS)
	$(AR) rcs $@ $^
	@echo "Built: $@"

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR)

test:
	@echo "Run tests with: cd tests && make test"

info:
	@echo "ArcanisRuntime v0.1.0"
	@echo "Sources: $(SRCS)"
	@echo "Objects: $(OBJS)"
