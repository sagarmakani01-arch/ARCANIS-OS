CC = gcc
CFLAGS = -Wall -Wextra -Wpedantic -std=c11 -O2 -g -I src -I include
LDFLAGS = -lm

SRC = src/main.c src/vm.c src/bytecode.c src/value.c src/stack.c src/memory.c \
      src/gc.c src/runtime.c src/compiler.c src/debugger.c src/profiler.c \
      src/sandbox.c src/plugin.c

OBJ = $(SRC:.c=.o)
TARGET = arcanisvm

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

test: $(TARGET)
	@echo "Running tests..."
	$(TARGET) --eval "print(1 + 2 * 3); assert(len('hello') == 5); print('Basic tests passed')"
	$(TARGET) --eval "var x = 10; var y = 20; print(x + y); assert(x + y == 30)"
	$(TARGET) --eval "fun fib(n) { if (n < 2) return n; return fib(n-1) + fib(n-2); } print(fib(10)); assert(fib(10) == 55)"
	$(TARGET) --eval "var arr = [1, 2, 3]; arrayPush(arr, 4); assert(len(arr) == 4); assert(arr[3] == 4)"
	$(TARGET) --eval "var m = {'a': 1, 'b': 2}; assert(m['a'] == 1)"
	@echo "All tests passed!"

test-fib:
	$(TARGET) --profile --eval "fun fib(n) { if (n < 2) return n; return fib(n-1) + fib(n-2); } print(fib(20))"

test-class:
	$(TARGET) --eval "class Animal { speak() { print('Animal speaks'); } } class Dog < Animal { speak() { print('Woof!'); } } var d = Dog(); d.speak();"

dist: all
	mkdir -p dist/ArcanisVM/bin dist/ArcanisVM/lib dist/ArcanisVM/include
	cp $(TARGET) dist/ArcanisVM/bin/
	cp src/*.h dist/ArcanisVM/include/
	cp include/arcanis.h dist/ArcanisVM/include/

clean:
	rm -f $(OBJ) $(TARGET)
	rm -rf dist

install: all
	cp $(TARGET) /usr/local/bin/
	mkdir -p /usr/local/include/arcanis
	cp include/arcanis.h /usr/local/include/arcanis/
	cp src/*.h /usr/local/include/arcanis/
