#ifndef ARCANIS_PROCESS_H
#define ARCANIS_PROCESS_H

#include <arcanis/types.h>
#include <arcanis/vmm.h>

enum process_state {
    PROCESS_RUNNING,
    PROCESS_READY,
    PROCESS_BLOCKED,
    PROCESS_ZOMBIE,
    PROCESS_TERMINATED,
};

typedef struct {
    uint32_t eax, ebx, ecx, edx;
    uint32_t esi, edi, ebp, esp;
    uint32_t eip, eflags;
    uint32_t cs, ss, ds, es, fs, gs;
    uint32_t cr3;
} process_context_t;

typedef struct process {
    pid_t              pid;
    enum process_state state;
    process_context_t  context;
    page_directory_t*  page_directory;
    uint32_t           kernel_stack;
    uint32_t           user_stack;
    uint32_t           priority;
    uint32_t           time_slice;
    char               name[64];
    struct process*    next;
    struct process*    prev;
    uid_t              uid;
    uint32_t           exit_code;
    uint32_t           sleep_until;
} process_t;

void process_initialize(void);
process_t* process_create(const char* name, void* entry_point, uint32_t priority);
void process_destroy(process_t* proc);
void process_switch(process_t* next);
process_t* process_get_current(void);
process_t* process_get_by_pid(pid_t pid);

#endif
