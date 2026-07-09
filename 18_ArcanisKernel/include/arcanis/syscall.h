#ifndef ARCANIS_SYSCALL_H
#define ARCANIS_SYSCALL_H

#include <arcanis/types.h>

#define SYSCALL_COUNT 38

enum syscall_num {
    SYS_EXIT     = 0,
    SYS_FORK     = 1,
    SYS_EXEC     = 2,
    SYS_READ     = 3,
    SYS_WRITE    = 4,
    SYS_OPEN     = 5,
    SYS_CLOSE    = 6,
    SYS_SLEEP    = 7,
    SYS_GETPID   = 8,
    SYS_PUTCHAR  = 9,
    SYS_GETCHAR  = 10,
    SYS_CLS      = 11,
    SYS_INFO     = 12,
    SYS_EXEC_CMD = 13,
    SYS_CHDIR    = 14,
    SYS_GETCWD   = 15,
    SYS_STAT     = 16,
    SYS_MKDIR    = 17,
    SYS_RMDIR    = 18,
    SYS_UNLINK   = 19,
    SYS_PIPE     = 20,
    SYS_DUP      = 21,
    SYS_TIME     = 22,
    SYS_UNAME    = 23,
    SYS_IOCTL    = 24,
    SYS_MMAP     = 25,
    SYS_MUNMAP   = 26,
    SYS_WAIT     = 27,
    SYS_KILL     = 28,
    SYS_GETUID   = 29,
    SYS_SETUID   = 30,
    SYS_YIELD    = 31,
    SYS_MSYNC    = 32,
    SYS_MPROTECT = 33,
    SYS_LOGIN    = 34,
    SYS_SVC      = 35,
    SYS_PKG      = 36,
    SYS_NET      = 37,
};

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

typedef int32_t (*syscall_handler_t)(registers_t*);

void syscall_initialize(void);
void syscall_handler(registers_t* regs);

#endif
