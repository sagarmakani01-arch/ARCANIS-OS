/**
 * scheduler.h — Priority Scheduler
 *
 * Multi-level feedback queue scheduler with priority aging.
 * Supports real-time, normal, and idle priority classes.
 */
#ifndef ARCANIS_SCHEDULER_H
#define ARCANIS_SCHEDULER_H

#include <arcanis/types.h>
#include <arcanis/process.h>

#define SCHED_MAX_PROCS    256
#define SCHED_NUM_QUEUES   8
#define SCHED_QUANTUM_BASE 10  /* Base time quantum in ticks */
#define SCHED_AGING_RATE   1   /* Priority boost per tick waited */

typedef enum {
    PROC_CLASS_REALTIME,   /* Priority 0-3: highest */
    PROC_CLASS_NORMAL,     /* Priority 4-6: normal */
    PROC_CLASS_IDLE        /* Priority 7: lowest */
} proc_class_t;

typedef enum {
    PROC_STATE_READY,
    PROC_STATE_RUNNING,
    PROC_STATE_BLOCKED,
    PROC_STATE_SLEEPING,
    PROC_STATE_ZOMBIE
} proc_state_t;

typedef struct {
    uint32_t    pid;
    uint32_t    priority;     /* 0=highest, 7=lowest */
    uint32_t    base_priority;
    uint32_t    quantum;      /* Time quantum remaining */
    uint32_t    time_used;    /* CPU time used */
    uint32_t    wait_time;    /* Time waiting in queue */
    proc_state_t state;
    proc_class_t class;
    uint32_t    arrival_time;
    uint32_t    io_wait;      /* Waiting for I/O */
    uint32_t    sleep_until;  /* Wake up at tick */
    char        name[32];
} sched_proc_t;

typedef struct {
    sched_proc_t* procs[SCHED_MAX_PROCS];
    uint32_t      count;
    uint32_t      head;
    uint32_t      tail;
} sched_queue_t;

typedef struct {
    sched_queue_t queues[SCHED_NUM_QUEUES];
    uint32_t      num_procs;
    uint32_t      current_tick;
    uint32_t      context_switches;
    uint32_t      total_time;
    sched_proc_t  current_proc;
    int           preempt_enabled;
    uint32_t      quantum_length;
    uint32_t      aging_enabled;
} scheduler_state_t;

/* Initialize scheduler */
void sched_init(scheduler_state_t* sched);

/* Process management */
int      sched_add_proc(scheduler_state_t* sched, uint32_t pid, const char* name,
                        uint32_t priority, proc_class_t class);
int      sched_remove_proc(scheduler_state_t* sched, uint32_t pid);

/* Priority management */
void     sched_set_priority(scheduler_state_t* sched, uint32_t pid, uint32_t priority);
uint32_t sched_get_priority(scheduler_state_t* sched, uint32_t pid);
void     sched_boost_priority(scheduler_state_t* sched, uint32_t pid);
void     sched_demote_priority(scheduler_state_t* sched, uint32_t pid);

/* Scheduling decisions */
uint32_t sched_next_proc(scheduler_state_t* sched);
uint32_t sched_pick_highest(scheduler_state_t* sched);
int      sched_should_preempt(scheduler_state_t* sched);

/* State transitions */
void     sched_block(scheduler_state_t* sched, uint32_t pid);
void     sched_unblock(scheduler_state_t* sched, uint32_t pid);
void     sched_sleep(scheduler_state_t* sched, uint32_t pid, uint32_t ticks);
void     sched_wake(scheduler_state_t* sched, uint32_t pid);
void     sched_yield(scheduler_state_t* sched);

/* Timer tick */
void     sched_tick(scheduler_state_t* sched);

/* Aging */
void     sched_age(scheduler_state_t* sched);

/* Statistics */
uint32_t sched_get_cpu_usage(scheduler_state_t* sched, uint32_t pid);
uint32_t sched_get_wait_time(scheduler_state_t* sched, uint32_t pid);
void     sched_print_stats(scheduler_state_t* sched);

/* Queue operations */
int      sched_enqueue(scheduler_state_t* sched, sched_proc_t* proc);
sched_proc_t* sched_dequeue(scheduler_state_t* sched, uint32_t priority);

#endif
