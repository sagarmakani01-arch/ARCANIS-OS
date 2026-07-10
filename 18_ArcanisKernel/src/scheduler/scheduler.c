/**
 * scheduler.c — Priority Scheduler Implementation
 *
 * Multi-level feedback queue with priority aging and preemption.
 */
#include <arcanis/scheduler.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

void sched_init(scheduler_state_t* sched) {
    if (!sched) return;
    memset(sched, 0, sizeof(scheduler_state_t));
    sched->quantum_length = SCHED_QUANTUM_BASE;
    sched->preempt_enabled = 1;
    sched->aging_enabled = 1;

    for (int i = 0; i < SCHED_NUM_QUEUES; i++) {
        sched->queues[i].count = 0;
        sched->queues[i].head = 0;
        sched->queues[i].tail = 0;
    }
}

/* ---- Queue operations ---- */

int sched_enqueue(scheduler_state_t* sched, sched_proc_t* proc) {
    if (!sched || !proc || proc->priority >= SCHED_NUM_QUEUES) return -1;

    sched_queue_t* q = &sched->queues[proc->priority];
    if (q->count >= SCHED_MAX_PROCS) return -1;

    q->procs[q->tail] = proc;
    q->tail = (q->tail + 1) % SCHED_MAX_PROCS;
    q->count++;
    return 0;
}

sched_proc_t* sched_dequeue(scheduler_state_t* sched, uint32_t priority) {
    if (!sched || priority >= SCHED_NUM_QUEUES) return NULL;

    sched_queue_t* q = &sched->queues[priority];
    if (q->count == 0) return NULL;

    sched_proc_t* proc = q->procs[q->head];
    q->head = (q->head + 1) % SCHED_MAX_PROCS;
    q->count--;
    return proc;
}

/* ---- Process management ---- */

int sched_add_proc(scheduler_state_t* sched, uint32_t pid, const char* name,
                    uint32_t priority, proc_class_t class) {
    if (!sched || sched->num_procs >= SCHED_MAX_PROCS) return -1;
    if (priority >= SCHED_NUM_QUEUES) return -1;

    sched_proc_t* proc = (sched_proc_t*)kmalloc(sizeof(sched_proc_t));
    if (!proc) return -1;

    memset(proc, 0, sizeof(sched_proc_t));
    proc->pid = pid;
    proc->priority = priority;
    proc->base_priority = priority;
    proc->quantum = SCHED_QUANTUM_BASE;
    proc->time_used = 0;
    proc->wait_time = 0;
    proc->state = PROC_STATE_READY;
    proc->class = class;
    proc->arrival_time = sched->current_tick;
    string_copy(proc->name, name, 32);

    if (sched_enqueue(sched, proc) != 0) {
        kfree(proc);
        return -1;
    }

    sched->num_procs++;
    return 0;
}

int sched_remove_proc(scheduler_state_t* sched, uint32_t pid) {
    if (!sched) return -1;

    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            uint32_t idx = (q->head + i) % SCHED_MAX_PROCS;
            if (q->procs[idx] && q->procs[idx]->pid == pid) {
                sched_proc_t* proc = q->procs[idx];
                /* Shift remaining */
                for (uint32_t j = i; j < q->count - 1; j++) {
                    uint32_t next = (q->head + j + 1) % SCHED_MAX_PROCS;
                    q->procs[(q->head + j) % SCHED_MAX_PROCS] = q->procs[next];
                }
                q->count--;
                kfree(proc);
                sched->num_procs--;
                return 0;
            }
        }
    }
    return -1;
}

/* ---- Priority management ---- */

void sched_set_priority(scheduler_state_t* sched, uint32_t pid, uint32_t priority) {
    if (!sched || priority >= SCHED_NUM_QUEUES) return;

    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid) {
                /* Remove from current queue */
                uint32_t old_priority = proc->priority;
                sched_queue_t* old_q = &sched->queues[old_priority];
                for (uint32_t j = i; j < old_q->count - 1; j++) {
                    uint32_t idx = (old_q->head + j) % SCHED_MAX_PROCS;
                    uint32_t next = (old_q->head + j + 1) % SCHED_MAX_PROCS;
                    old_q->procs[idx] = old_q->procs[next];
                }
                old_q->count--;

                /* Add to new queue */
                proc->priority = priority;
                sched_enqueue(sched, proc);
                return;
            }
        }
    }
}

uint32_t sched_get_priority(scheduler_state_t* sched, uint32_t pid) {
    if (!sched) return 0;

    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid)
                return proc->priority;
        }
    }
    return 0;
}

void sched_boost_priority(scheduler_state_t* sched, uint32_t pid) {
    if (!sched) return;
    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid) {
                if (proc->priority > 0) {
                    proc->priority--;
                    /* Re-enqueue at higher priority */
                    sched_set_priority(sched, pid, proc->priority);
                }
                return;
            }
        }
    }
}

void sched_demote_priority(scheduler_state_t* sched, uint32_t pid) {
    if (!sched) return;
    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid) {
                if (proc->priority < SCHED_NUM_QUEUES - 1) {
                    proc->priority++;
                    sched_set_priority(sched, pid, proc->priority);
                }
                return;
            }
        }
    }
}

/* ---- Scheduling ---- */

uint32_t sched_pick_highest(scheduler_state_t* sched) {
    if (!sched) return 0;

    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        if (q->count > 0) {
            sched_proc_t* proc = q->procs[q->head];
            return proc ? proc->pid : 0;
        }
    }
    return 0;
}

uint32_t sched_next_proc(scheduler_state_t* sched) {
    if (!sched) return 0;

    /* Pick highest priority ready process */
    uint32_t pid = sched_pick_highest(sched);
    if (pid == 0) return 0;

    /* Find and prepare it */
    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid) {
                proc->state = PROC_STATE_RUNNING;
                proc->quantum = SCHED_QUANTUM_BASE + (SCHED_NUM_QUEUES - proc->priority) * 2;
                proc->time_used = 0;
                sched->current_proc = *proc;
                sched->context_switches++;
                return pid;
            }
        }
    }
    return 0;
}

int sched_should_preempt(scheduler_state_t* sched) {
    if (!sched || !sched->preempt_enabled) return 0;

    /* Check if higher priority process is waiting */
    sched_proc_t* current = &sched->current_proc;
    if (current->priority > 0) {
        sched_queue_t* higher = &sched->queues[current->priority - 1];
        if (higher->count > 0) return 1;
    }

    /* Check if quantum expired */
    if (current->quantum <= 0) return 1;

    return 0;
}

/* ---- State transitions ---- */

void sched_block(scheduler_state_t* sched, uint32_t pid) {
    if (!sched) return;
    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid) {
                proc->state = PROC_STATE_BLOCKED;
                /* Remove from ready queue */
                for (uint32_t j = i; j < q->count - 1; j++) {
                    uint32_t idx = (q->head + j) % SCHED_MAX_PROCS;
                    uint32_t next = (q->head + j + 1) % SCHED_MAX_PROCS;
                    q->procs[idx] = q->procs[next];
                }
                q->count--;
                return;
            }
        }
    }
}

void sched_unblock(scheduler_state_t* sched, uint32_t pid) {
    if (!sched) return;
    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid) {
                proc->state = PROC_STATE_READY;
                sched_enqueue(sched, proc);
                return;
            }
        }
    }
}

void sched_sleep(scheduler_state_t* sched, uint32_t pid, uint32_t ticks) {
    if (!sched) return;
    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid) {
                proc->state = PROC_STATE_SLEEPING;
                proc->sleep_until = sched->current_tick + ticks;
                return;
            }
        }
    }
}

void sched_wake(scheduler_state_t* sched, uint32_t pid) {
    if (!sched) return;
    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid && proc->state == PROC_STATE_SLEEPING) {
                proc->state = PROC_STATE_READY;
                sched_enqueue(sched, proc);
                return;
            }
        }
    }
}

void sched_yield(scheduler_state_t* sched) {
    if (!sched) return;
    if (sched->current_proc.pid != 0) {
        sched_proc_t* current = &sched->current_proc;
        current->state = PROC_STATE_READY;
        current->priority = (current->priority < SCHED_NUM_QUEUES - 1) ?
                            current->priority + 1 : current->priority;
        sched_enqueue(sched, current);
    }
}

/* ---- Timer tick ---- */

void sched_tick(scheduler_state_t* sched) {
    if (!sched) return;
    sched->current_tick++;
    sched->total_time++;

    /* Decrement quantum */
    if (sched->current_proc.pid != 0) {
        sched->current_proc.quantum--;
        sched->current_proc.time_used++;
    }

    /* Age waiting processes */
    if (sched->aging_enabled)
        sched_age(sched);

    /* Wake sleeping processes */
    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->state == PROC_STATE_SLEEPING &&
                sched->current_tick >= proc->sleep_until) {
                proc->state = PROC_STATE_READY;
            }
        }
    }
}

/* ---- Aging ---- */

void sched_age(scheduler_state_t* sched) {
    if (!sched) return;

    for (uint32_t p = 1; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->state == PROC_STATE_READY) {
                proc->wait_time++;
                /* Boost priority after waiting too long */
                if (proc->wait_time >= 50 && proc->priority > 0) {
                    proc->priority--;
                    proc->wait_time = 0;
                    /* Re-enqueue at new priority */
                    sched_set_priority(sched, proc->pid, proc->priority);
                }
            }
        }
    }
}

/* ---- Statistics ---- */

uint32_t sched_get_cpu_usage(scheduler_state_t* sched, uint32_t pid) {
    if (!sched || sched->total_time == 0) return 0;

    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid)
                return (proc->time_used * 100) / sched->total_time;
        }
    }
    return 0;
}

uint32_t sched_get_wait_time(scheduler_state_t* sched, uint32_t pid) {
    if (!sched) return 0;

    for (uint32_t p = 0; p < SCHED_NUM_QUEUES; p++) {
        sched_queue_t* q = &sched->queues[p];
        for (uint32_t i = 0; i < q->count; i++) {
            sched_proc_t* proc = q->procs[(q->head + i) % SCHED_MAX_PROCS];
            if (proc && proc->pid == pid)
                return proc->wait_time;
        }
    }
    return 0;
}

void sched_print_stats(scheduler_state_t* sched) {
    if (!sched) return;
    /* In real implementation: print scheduler statistics */
    /* printf("Scheduler: %u procs, %u switches, tick=%u\n",
              sched->num_procs, sched->context_switches, sched->current_tick); */
}
