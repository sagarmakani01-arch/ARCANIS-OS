/**
 * signal.c — Basic Signal Handling
 *
 * POSIX-like signal delivery for Arcanis processes.
 * Supports handler registration, masking, pending signals.
 */
#include <arcanis/signal.h>
#include <arcanis/process.h>
#include <arcanis/string.h>

void signal_init(signal_state_t* state) {
    if (!state) return;
    for (int i = 0; i < SIG_MAX; i++)
        state->handlers[i] = NULL;
    state->blocked = 0;
    state->pending = 0;

    /* Default handlers */
    state->handlers[SIGINT] = (signal_handler_t)SIG_IGN;
    state->handlers[SIGTERM] = (signal_handler_t)SIG_IGN;
    state->handlers[SIGCHLD] = (signal_handler_t)SIG_IGN;
}

int signal_set_handler(signal_state_t* state, int signum, signal_handler_t handler) {
    if (!state || signum < 0 || signum >= SIG_MAX) return -1;
    if (signum == SIGKILL || signum == SIGSTOP) return -1; /* Cannot change these */
    state->handlers[signum] = handler;
    return 0;
}

int signal_send(pid_t pid, int signum) {
    if (signum < 0 || signum >= SIG_MAX) return -1;

    process_t* proc = process_get_by_pid(pid);
    if (!proc) return -1;

    /* Set pending bit */
    proc->signal_state.pending |= (1 << signum);

    /* If process is blocked, unblock it to deliver signal */
    if (proc->state == PROCESS_BLOCKED) {
        process_unblock(proc);
    }

    return 0;
}

int signal_mask(signal_state_t* state, int signum, int block) {
    if (!state || signum < 0 || signum >= SIG_MAX) return -1;
    if (block)
        state->blocked |= (1 << signum);
    else
        state->blocked &= ~(1 << signum);
    return 0;
}

void signal_deliver(signal_state_t* state) {
    if (!state) return;

    for (int i = 0; i < SIG_MAX; i++) {
        if (!(state->pending & (1 << i))) continue;
        if (state->blocked & (1 << i)) continue;

        state->pending &= ~(1 << i);

        signal_handler_t handler = state->handlers[i];
        if (handler == NULL || handler == (signal_handler_t)SIG_DFL) {
            /* Default: terminate for fatal signals */
            if (i == SIGINT || i == SIGTERM || i == SIGKILL ||
                i == SIGSEGV || i == SIGABRT || i == SIGFPE) {
                process_t* proc = process_get_current();
                if (proc) {
                    proc->exit_code = 128 + i;
                    process_destroy(proc);
                }
            }
        } else if (handler == (signal_handler_t)SIG_IGN) {
            /* Ignore */
        } else {
            /* Call user handler */
            handler(i);
        }
    }
}

int signal_pending(signal_state_t* state) {
    if (!state) return 0;
    return state->pending & ~state->blocked;
}
