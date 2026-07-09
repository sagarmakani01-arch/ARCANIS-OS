# ArcanisKernel API Reference

## System Calls

All system calls are invoked via INT 0x80 with the syscall number in EAX.

### SYS_EXIT (0)
```c
int exit(int status);
```
Terminates the current process and frees its resources.

### SYS_FORK (1)
```c
int fork(void);
```
Creates a child process. Returns PID to parent, 0 to child.

### SYS_EXEC (2)
```c
int exec(const char* path, char* const argv[]);
```
Replaces current process image with a new program.

### SYS_READ (3)
```c
int read(int fd, void* buf, size_t count);
```
Reads data from a file descriptor.

### SYS_WRITE (4)
```c
int write(int fd, const void* buf, size_t count);
```
Writes data to a file descriptor.

### SYS_SLEEP (7)
```c
int sleep(unsigned int ms);
```
Sleeps for the specified number of milliseconds.

### SYS_GETPID (8)
```c
int getpid(void);
```
Returns the current process ID.

### SYS_PUTCHAR (9)
```c
int putchar(int c);
```
Prints a character to the VGA display.

### SYS_GETCHAR (10)
```c
int getchar(void);
```
Reads a character from the keyboard (blocking).

### SYS_CLS (11)
```c
int cls(void);
```
Clears the VGA display.

### SYS_INFO (12)
```c
int info(void);
```
Returns system information.

## Kernel Functions

### String Operations (string.h)
```c
size_t strlen(const char* str);
char* strcpy(char* dest, const char* src);
int strcmp(const char* s1, const char* s2);
void* memset(void* ptr, int value, size_t num);
void* memcpy(void* dest, const void* src, size_t num);
int memcmp(const void* ptr1, const void* ptr2, size_t num);
char* itoa(int value, char* str, int base);
int atoi(const char* str);
```

### VGA Functions (vga.h)
```c
void vga_initialize(void);
void vga_clear(void);
void vga_set_color(uint8_t fg, uint8_t bg);
void vga_put_char(char c);
void vga_puts(const char* str);
void vga_printf(const char* format, ...);
void vga_put_hex(uint32_t value);
void vga_put_dec(uint32_t value);
```

### Memory Functions
```c
// PMM (pmm.h)
void* pmm_alloc_block(void);
void  pmm_free_block(void* block);
void* pmm_alloc_blocks(size_t count);
uint32_t pmm_get_free_blocks(void);

// VMM (vmm.h)
void vmm_map_page(page_directory_t* dir, uint32_t virt, uint32_t phys, uint32_t flags);
void vmm_unmap_page(page_directory_t* dir, uint32_t virt);
void vmm_switch_directory(page_directory_t* dir);

// Heap (heap.h)
void* kmalloc(size_t size);
void  kfree(void* ptr);
size_t heap_get_used(void);
```

### Process Functions (process.h)
```c
process_t* process_create(const char* name, void* entry, uint32_t priority);
void process_destroy(process_t* proc);
void process_switch(process_t* next);
process_t* process_get_current(void);
```

### Scheduler Functions (scheduler.h)
```c
void scheduler_add_process(process_t* proc);
void scheduler_remove_process(process_t* proc);
void scheduler_yield(void);
void scheduler_tick(void);
```

### Timer Functions (timer.h)
```c
void timer_initialize(uint32_t freq);
uint32_t timer_get_ticks(void);
uint32_t timer_get_seconds(void);
void timer_sleep(uint32_t ms);
```

### Keyboard Functions (keyboard.h)
```c
void keyboard_initialize(void);
void keyboard_register_callback(keyboard_callback_t cb);
char scancode_to_ascii(uint8_t scancode);
uint8_t keyboard_get_scancode(void);
```

### Serial Functions (serial.h)
```c
void serial_initialize(uint16_t port);
void serial_putchar(char c);
void serial_puts(const char* str);
char serial_getchar(void);
```

## Color Constants (vga.h)
```c
enum vga_color {
    VGA_BLACK         = 0,
    VGA_BLUE          = 1,
    VGA_GREEN         = 2,
    VGA_CYAN          = 3,
    VGA_RED           = 4,
    VGA_MAGENTA       = 5,
    VGA_BROWN         = 6,
    VGA_LIGHT_GREY    = 7,
    VGA_DARK_GREY     = 8,
    VGA_LIGHT_BLUE    = 9,
    VGA_LIGHT_GREEN   = 10,
    VGA_LIGHT_CYAN    = 11,
    VGA_LIGHT_RED     = 12,
    VGA_LIGHT_MAGENTA = 13,
    VGA_YELLOW        = 14,
    VGA_WHITE         = 15,
};
```
