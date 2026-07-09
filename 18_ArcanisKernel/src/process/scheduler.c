#include <arcanis/scheduler.h>
#include <arcanis/process.h>
#include <arcanis/types.h>
#include <arcanis/string.h>
#include <arcanis/timer.h>

static process_t* scheduler_queue = NULL;
static process_t* scheduler_current = NULL;

void scheduler_initialize(void) {
    scheduler_queue = NULL;
    scheduler_current = NULL;
}

void scheduler_add_process(process_t* proc) {
    if (!proc) return;

    proc->next = scheduler_queue;
    proc->prev = NULL;
    if (scheduler_queue) scheduler_queue->prev = proc;
    scheduler_queue = proc;
}

void scheduler_remove_process(process_t* proc) {
    if (!proc) return;

    if (proc->prev) proc->prev->next = proc->next;
    else scheduler_queue = proc->next;
    if (proc->next) proc->next->prev = proc->prev;

    if (scheduler_current == proc) {
        scheduler_current = proc->next ? proc->next : scheduler_queue;
    }
}

void scheduler_yield(void) {
    process_t* current = process_get_current();
    if (current && current->state == PROCESS_RUNNING) {
        current->state = PROCESS_READY;
        current->time_slice = SCHED_DEFAULT_QUANTUM;
    }
    scheduler_schedule();
}

void scheduler_tick(void) {
    process_t* proc = scheduler_queue;
    uint32_t now = timer_get_ticks();

    while (proc) {
        if (proc->state == PROCESS_BLOCKED && proc->sleep_until > 0 && now >= proc->sleep_until) {
            proc->sleep_until = 0;
            proc->state = PROCESS_READY;
        }
        proc = proc->next;
    }

    process_t* current = process_get_current();
    if (!current) return;

    if (current->time_slice > 0) {
        current->time_slice--;
    }

    if (current->time_slice == 0) {
        scheduler_yield();
    }
}

process_t* scheduler_get_next(void) {
    process_t* proc = scheduler_queue;
    process_t* highest = NULL;
    uint32_t highest_priority = 0;

    while (proc) {
        if (proc->state == PROCESS_READY) {
            if (!highest || proc->priority > highest_priority) {
                highest = proc;
                highest_priority = proc->priority;
            }
        }
        proc = proc->next;
    }

    return highest;
}

void scheduler_schedule(void) {
    process_t* next = scheduler_get_next();
    if (next) {
        next->time_slice = SCHED_DEFAULT_QUANTUM;
        process_switch(next);
    }
}
