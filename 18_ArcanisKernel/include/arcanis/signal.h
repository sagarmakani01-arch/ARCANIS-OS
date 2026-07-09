#ifndef ARCANIS_SIGNAL_H
#define ARCANIS_SIGNAL_H

#include <arcanis/types.h>

#define SIG_DFL  ((void*)0)
#define SIG_IGN  ((void*)1)

/* Standard signals */
#define SIGNULL    0
#define SIGHUP     1
#define SIGINT     2
#define SIGQUIT    3
#define SIGILL     4
#define SIGTRAP    5
#define SIGABRT    6
#define SIGBUS     7
#define SIGFPE     8
#define SIGKILL    9
#define SIGUSR1    10
#define SIGSEGV    11
#define SIGUSR2    12
#define SIGPIPE    13
#define SIGALRM    14
#define SIGTERM    15
#define SIGSTKFLT  16
#define SIGCHLD    17
#define SIGCONT    18
#define SIGSTOP    19
#define SIGTSTP    20
#define SIGTTIN    21
#define SIGTTOU    22
#define SIGURG     23
#define SIGXCPU    24
#define SIGXFSZ    25
#define SIGVTALRM  26
#define SIGPROF    27
#define SIGWINCH   28
#define SIGIO      29
#define SIGPWR     30
#define SIGSYS     31

#define SIG_MAX    32

typedef void (*signal_handler_t)(int signum);

typedef struct {
    signal_handler_t handlers[SIG_MAX];
    uint32_t         blocked;
    uint32_t         pending;
} signal_state_t;

void signal_init(signal_state_t* state);
int  signal_set_handler(signal_state_t* state, int signum, signal_handler_t handler);
int  signal_send(pid_t pid, int signum);
int  signal_mask(signal_state_t* state, int signum, int block);
void signal_deliver(signal_state_t* state);
int  signal_pending(signal_state_t* state);

#endif
