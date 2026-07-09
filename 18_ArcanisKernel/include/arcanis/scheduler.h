#ifndef ARCANIS_SCHEDULER_H
#define ARCANIS_SCHEDULER_H

#include <arcanis/types.h>
#include <arcanis/process.h>

#define SCHED_DEFAULT_QUANTUM 10
#define SCHED_PRIORITY_HIGH   10
#define SCHED_PRIORITY_NORMAL 5
#define SCHED_PRIORITY_LOW    1

void scheduler_initialize(void);
void scheduler_add_process(process_t* proc);
void scheduler_remove_process(process_t* proc);
void scheduler_yield(void);
void scheduler_tick(void);
process_t* scheduler_get_next(void);
void scheduler_schedule(void);

#endif
