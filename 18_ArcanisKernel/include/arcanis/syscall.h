#ifndef ARCANIS_SYSCALL_H
#define ARCANIS_SYSCALL_H

#include <arcanis/types.h>

#define SYSCALL_COUNT 32

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
};

typedef int32_t (*syscall_handler_t)(registers_t*);

void syscall_initialize(void);
void syscall_handler(registers_t* regs);

#endif
