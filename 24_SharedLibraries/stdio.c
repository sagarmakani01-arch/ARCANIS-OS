/**
 * stdio.c — Userspace printf/scanf/puts/gets
 *
 * Minimal formatted I/O for Arcanis userspace programs.
 * Uses sys_write/sys_read for console I/O.
 */
#include "arcanis_libc.h"

/* Forward declarations for inline syscalls */
static inline ssize_t sys_write_stdout(const void* buf, uint32_t size) {
    /* Write to stdout (fd 1) — simplified: directly call putchar for each char */
    const char* s = (const char*)buf;
    for (uint32_t i = 0; i < size; i++) {
        putchar(s[i]);
    }
    return (ssize_t)size;
}

static inline ssize_t sys_read_stdin(void* buf, uint32_t size) {
    char* s = (char*)buf;
    for (uint32_t i = 0; i < size; i++) {
        s[i] = (char)getchar();
        if (s[i] == '\n' || s[i] == '\r') {
            s[i] = '\n';
            return (ssize_t)(i + 1);
        }
    }
    return (ssize_t)size;
}

/* ---- Helper: write int ---- */
static void write_int(char* buf, int* pos, int value) {
    char tmp[12];
    int i = 0;
    int neg = 0;
    unsigned int val;

    if (value < 0) { neg = 1; val = (unsigned int)(-value); }
    else { val = (unsigned int)value; }

    if (val == 0) { tmp[i++] = '0'; }
    else {
        while (val > 0) { tmp[i++] = '0' + (val % 10); val /= 10; }
    }

    if (neg) buf[(*pos)++] = '-';
    while (i > 0) buf[(*pos)++] = tmp[--i];
}

static void write_uint(char* buf, int* pos, unsigned int value) {
    char tmp[12];
    int i = 0;

    if (value == 0) { tmp[i++] = '0'; }
    else {
        while (value > 0) { tmp[i++] = '0' + (value % 10); value /= 10; }
    }
    while (i > 0) buf[(*pos)++] = tmp[--i];
}

static void write_hex(char* buf, int* pos, unsigned int value) {
    char tmp[12];
    int i = 0;
    const char* hex = "0123456789abcdef";

    if (value == 0) { tmp[i++] = '0'; }
    else {
        while (value > 0) { tmp[i++] = hex[value % 16]; value /= 16; }
    }
    while (i > 0) buf[(*pos)++] = tmp[--i];
}

/* ---- printf ---- */
int printf(const char* fmt, ...) {
    char buf[4096];
    int pos = 0;
    __builtin_va_list args;
    __builtin_va_start(args, fmt);

    while (*fmt && pos < 4095) {
        if (*fmt == '%') {
            fmt++;
            int pad_zero = 0;
            int width = 0;

            /* Parse width */
            while (*fmt >= '0' && *fmt <= '9') {
                width = width * 10 + (*fmt - '0');
                fmt++;
            }

            if (*fmt == '0') { pad_zero = 1; fmt++; }

            while (*fmt >= '0' && *fmt <= '9') {
                width = width * 10 + (*fmt - '0');
                fmt++;
            }

            switch (*fmt) {
                case 'd': case 'i': {
                    int val = __builtin_va_arg(args, int);
                    int start = pos;
                    write_int(buf, &pos, val);
                    /* Pad with spaces */
                    while (pos - start < width) {
                        /* Shift right and insert space */
                        for (int j = pos; j > start; j--) buf[j] = buf[j-1];
                        buf[start] = pad_zero ? '0' : ' ';
                        pos++;
                    }
                    break;
                }
                case 'u': {
                    unsigned int val = __builtin_va_arg(args, unsigned int);
                    write_uint(buf, &pos, val);
                    break;
                }
                case 'x': case 'X': {
                    unsigned int val = __builtin_va_arg(args, unsigned int);
                    write_hex(buf, &pos, val);
                    break;
                }
                case 's': {
                    const char* s = __builtin_va_arg(args, const char*);
                    if (!s) s = "(null)";
                    while (*s && pos < 4095) buf[pos++] = *s++;
                    break;
                }
                case 'c': {
                    char c = (char)__builtin_va_arg(args, int);
                    buf[pos++] = c;
                    break;
                }
                case 'p': {
                    unsigned long val = (unsigned long)__builtin_va_arg(args, void*);
                    buf[pos++] = '0';
                    buf[pos++] = 'x';
                    write_hex(buf, &pos, (unsigned int)val);
                    break;
                }
                case '%': {
                    buf[pos++] = '%';
                    break;
                }
                default: {
                    buf[pos++] = '%';
                    buf[pos++] = *fmt;
                    break;
                }
            }
        } else {
            buf[pos++] = *fmt;
        }
        fmt++;
    }

    __builtin_va_end(args);
    buf[pos] = '\0';
    sys_write_stdout(buf, pos);
    return pos;
}

/* ---- sprintf ---- */
int sprintf(char* buf, const char* fmt, ...) {
    int pos = 0;
    __builtin_va_list args;
    __builtin_va_start(args, fmt);

    while (*fmt) {
        if (*fmt == '%') {
            fmt++;
            switch (*fmt) {
                case 'd': case 'i': {
                    int val = __builtin_va_arg(args, int);
                    write_int(buf, &pos, val);
                    break;
                }
                case 'u': {
                    unsigned int val = __builtin_va_arg(args, unsigned int);
                    write_uint(buf, &pos, val);
                    break;
                }
                case 'x': {
                    unsigned int val = __builtin_va_arg(args, unsigned int);
                    write_hex(buf, &pos, val);
                    break;
                }
                case 's': {
                    const char* s = __builtin_va_arg(args, const char*);
                    if (!s) s = "(null)";
                    while (*s) buf[pos++] = *s++;
                    break;
                }
                case 'c': {
                    buf[pos++] = (char)__builtin_va_arg(args, int);
                    break;
                }
                case '%': {
                    buf[pos++] = '%';
                    break;
                }
                default: {
                    buf[pos++] = '%';
                    buf[pos++] = *fmt;
                    break;
                }
            }
        } else {
            buf[pos++] = *fmt;
        }
        fmt++;
    }

    __builtin_va_end(args);
    buf[pos] = '\0';
    return pos;
}

/* ---- puts ---- */
int puts(const char* s) {
    while (*s) putchar(*s++);
    putchar('\n');
    return 0;
}

/* ---- gets ---- */
char* gets(char* buf) {
    int i = 0;
    char c;
    while (1) {
        c = (char)getchar();
        if (c == '\n' || c == '\r') {
            buf[i] = '\0';
            putchar('\n');
            return buf;
        }
        if (c == 8 && i > 0) { /* backspace */
            i--;
            putchar(8);
            putchar(' ');
            putchar(8);
        } else {
            buf[i++] = c;
            putchar(c);
        }
    }
}

/* ---- Simple malloc (bump allocator for userspace) ---- */
static uint32_t heap_start = 0x80000000;
static uint32_t heap_ptr = 0x80000000;
static uint32_t heap_end = 0x80100000;

void* malloc(uint32_t size) {
    if (heap_ptr == 0) heap_ptr = heap_start;
    /* Align to 8 bytes */
    uint32_t aligned = (size + 7) & ~7;
    if (heap_ptr + aligned > heap_end) return (void*)0;
    void* ptr = (void*)heap_ptr;
    heap_ptr += aligned;
    return ptr;
}

void free(void* ptr) {
    /* Bump allocator — no-op */
    (void)ptr;
}

void* realloc(void* ptr, uint32_t new_size) {
    if (!ptr) return malloc(new_size);
    /* Can't shrink in bump allocator */
    return ptr;
}
