# ArcanisDrivers Makefile

CC = gcc
CFLAGS = -Wall -Wextra -pedantic -std=c11 -Iinclude
LDFLAGS =

BUILD_DIR = build
SRC_DIR = src
INC_DIR = include
TEST_DIR = tests
EXAMPLE_DIR = examples

SRCS = $(SRC_DIR)/core/driver.c \
       $(SRC_DIR)/core/driver_event.c \
       $(SRC_DIR)/utils/driver_memory.c \
       $(SRC_DIR)/utils/driver_ringbuffer.c \
       $(SRC_DIR)/hal/hal.c \
       $(SRC_DIR)/pnp/pnp.c \
       $(SRC_DIR)/drivers/keyboard.c \
       $(SRC_DIR)/drivers/mouse.c \
       $(SRC_DIR)/drivers/display.c \
       $(SRC_DIR)/drivers/storage.c \
       $(SRC_DIR)/drivers/network.c \
       $(SRC_DIR)/arcanis_drivers.c

OBJS = $(patsubst $(SRC_DIR)/%.c, $(BUILD_DIR)/%.o, $(SRCS))
LIB = $(BUILD_DIR)/libarcanis_drivers.a
TEST = $(BUILD_DIR)/arcanis_test
EXAMPLE = $(BUILD_DIR)/arcanis_example

.PHONY: all clean test example dirs

all: dirs $(LIB)

dirs:
	@mkdir -p $(BUILD_DIR)/core
	@mkdir -p $(BUILD_DIR)/hal
	@mkdir -p $(BUILD_DIR)/pnp
	@mkdir -p $(BUILD_DIR)/drivers
	@mkdir -p $(BUILD_DIR)/utils

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

$(LIB): $(OBJS)
	ar rcs $@ $^

test: dirs $(LIB) $(BUILD_DIR)/test_main.o
	$(CC) $(CFLAGS) $(BUILD_DIR)/test_main.o $(LIB) $(LDFLAGS) -o $(TEST)
	@echo "Tests built: $(TEST)"

$(BUILD_DIR)/test_main.o: $(TEST_DIR)/test_main.c
	$(CC) $(CFLAGS) -c $< -o $@

example: dirs $(LIB) $(BUILD_DIR)/main.o
	$(CC) $(CFLAGS) $(BUILD_DIR)/main.o $(LIB) $(LDFLAGS) -o $(EXAMPLE)
	@echo "Example built: $(EXAMPLE)"

$(BUILD_DIR)/main.o: $(EXAMPLE_DIR)/main.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -rf $(BUILD_DIR)

run-test: test
	./$(TEST)

run-example: example
	./$(EXAMPLE)
