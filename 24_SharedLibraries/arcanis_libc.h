/**
 * arcanis_libc.h — Userspace C library for Arcanis OS
 *
 * Provides POSIX-like wrappers around Arcanis syscalls.
 * Programs link against this to interact with the kernel.
 */
#ifndef ARCANIS_LIBC_H
#define ARCANIS_LIBC_H

#include <stdint.h>

/* ---- Types ---- */
typedef int pid_t;
typedef int uid_t;
typedef int ssize_t;

typedef struct {
    uint32_t dev;
    uint32_t ino;
    uint32_t mode;
    uint32_t nlink;
    uint32_t uid;
    uint32_t gid;
    uint32_t rdev;
    uint32_t size;
    uint32_t atime;
    uint32_t mtime;
    uint32_t ctime;
} stat_t;

typedef struct {
    char sysname[64];
    char nodename[64];
    char release[64];
    char version[64];
    char machine[64];
} utsname_t;

/* ---- Syscall numbers ---- */
#define SYS_EXIT     0
#define SYS_FORK     1
#define SYS_EXEC     2
#define SYS_READ     3
#define SYS_WRITE    4
#define SYS_OPEN     5
#define SYS_CLOSE    6
#define SYS_SLEEP    7
#define SYS_GETPID   8
#define SYS_PUTCHAR  9
#define SYS_GETCHAR  10
#define SYS_CLS      11
#define SYS_INFO     12
#define SYS_CHDIR    14
#define SYS_GETCWD   15
#define SYS_STAT     16
#define SYS_MKDIR    17
#define SYS_RMDIR    18
#define SYS_UNLINK   19
#define SYS_TIME     22
#define SYS_UNAME    23
#define SYS_KILL     28
#define SYS_GETUID   29
#define SYS_SETUID   30
#define SYS_YIELD    31

/* File flags */
#define O_RDONLY  0x00
#define O_WRONLY  0x01
#define O_RDWR    0x02
#define O_CREAT   0x04
#define O_TRUNC   0x08
#define O_APPEND  0x10

/* File types */
#define S_IFDIR   0040000
#define S_IFREG   0100000

/* ---- Inline syscall helpers ---- */
static inline int32_t _syscall0(int num) {
    int32_t ret;
    asm volatile("int $0x80" : "=a"(ret) : "a"(num));
    return ret;
}
static inline int32_t _syscall1(int num, int32_t a1) {
    int32_t ret;
    asm volatile("int $0x80" : "=a"(ret) : "a"(num), "b"(a1));
    return ret;
}
static inline int32_t _syscall2(int num, int32_t a1, int32_t a2) {
    int32_t ret;
    asm volatile("int $0x80" : "=a"(ret) : "a"(num), "b"(a1), "c"(a2));
    return ret;
}
static inline int32_t _syscall3(int num, int32_t a1, int32_t a2, int32_t a3) {
    int32_t ret;
    asm volatile("int $0x80" : "=a"(ret) : "a"(num), "b"(a1), "c"(a2), "d"(a3));
    return ret;
}
static inline int32_t _syscall4(int num, int32_t a1, int32_t a2, int32_t a3, int32_t a4) {
    int32_t ret;
    asm volatile("int $0x80" : "=a"(ret) : "a"(num), "b"(a1), "c"(a2), "d"(a3), "S"(a4));
    return ret;
}

/* ---- Process ---- */
static inline void exit(int code) { _syscall1(SYS_EXIT, code); }
static inline pid_t getpid(void) { return _syscall0(SYS_GETPID); }
static inline void sleep_ms(uint32_t ms) { _syscall1(SYS_SLEEP, ms); }
static inline void yield(void) { _syscall0(SYS_YIELD); }
static inline pid_t fork(void) { return _syscall0(SYS_FORK); }
static inline int kill(pid_t pid) { return _syscall1(SYS_KILL, pid); }
static inline pid_t wait(int* status) { return _syscall2(SYS_WAIT, -1, (int32_t)status); }
static inline pid_t waitpid(pid_t pid, int* status) { return _syscall2(SYS_WAIT, pid, (int32_t)status); }
static inline int exec(const char* path) { return _syscall1(SYS_EXEC, (int32_t)path); }

/* ---- I/O ---- */
static inline void putchar(char c) { _syscall1(SYS_PUTCHAR, c); }
static inline int getchar(void) { return _syscall0(SYS_GETCHAR); }
static inline void cls(void) { _syscall0(SYS_CLS); }

/* ---- Filesystem ---- */
static inline int open(const char* path, int flags) {
    return _syscall2(SYS_OPEN, (int32_t)path, flags);
}
static inline int close(int fd) { return _syscall1(SYS_CLOSE, fd); }
static inline ssize_t read(int fd, void* buf, uint32_t size) {
    return _syscall3(SYS_READ, fd, 0, size);
    /* note: offset=0 for simplicity; real impl needs fd table */
}
static inline ssize_t write(int fd, const void* buf, uint32_t size) {
    return _syscall3(SYS_WRITE, fd, 0, size);
}
static inline int mkdir_p(const char* path) { return _syscall1(SYS_MKDIR, (int32_t)path); }
static inline int rmdir_p(const char* path) { return _syscall1(SYS_RMDIR, (int32_t)path); }
static inline int unlink(const char* path) { return _syscall1(SYS_UNLINK, (int32_t)path); }
static inline int chdir(const char* path) { return _syscall1(SYS_CHDIR, (int32_t)path); }
static inline int getcwd(char* buf, uint32_t size) {
    return _syscall2(SYS_GETCWD, (int32_t)buf, size);
}
static inline int stat(const char* path, stat_t* st) {
    return _syscall2(SYS_STAT, (int32_t)path, (int32_t)st);
}

/* ---- Time ---- */
static inline uint32_t time(void) { return _syscall0(SYS_TIME); }

/* ---- System ---- */
static inline int uname(utsname_t* buf) { return _syscall1(SYS_UNAME, (int32_t)buf); }
static inline uid_t getuid(void) { return _syscall0(SYS_GETUID); }
static inline int setuid(uid_t uid) { return _syscall1(SYS_SETUID, uid); }

/* ---- String (kernel-provided, usable in userspace) ---- */
uint32_t string_length(const char* str);
void string_copy(char* dst, const char* src);
int string_compare(const char* a, const char* b);

/* ---- printf / scanf (userspace) ---- */
int printf(const char* fmt, ...);
int sprintf(char* buf, const char* fmt, ...);
int scanf(const char* fmt, ...);
int puts(const char* s);
char* gets(char* buf);

/* ---- malloc / free (userspace heap) ---- */
void* malloc(uint32_t size);
void  free(void* ptr);
void* realloc(void* ptr, uint32_t new_size);

#endif
