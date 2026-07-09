#include <arcanis/process.h>
#include <arcanis/heap.h>
#include <arcanis/vmm.h>
#include <arcanis/string.h>
#include <arcanis/defs.h>
#include <arcanis/scheduler.h>
#include <arcanis/io.h>

static process_t* process_list = NULL;
static process_t* current_process = NULL;
static pid_t next_pid = 1;

extern void context_switch(process_context_t* prev, process_context_t* next);
extern void context_switch_first(process_context_t* next);

void process_initialize(void) {
    process_list = NULL;
    current_process = NULL;
    next_pid = 1;
}

process_t* process_create(const char* name, void* entry_point, uint32_t priority) {
    process_t* proc = (process_t*)kmalloc(sizeof(process_t));
    if (!proc) return NULL;

    memset(proc, 0, sizeof(process_t));

    proc->pid = next_pid++;
    proc->state = PROCESS_READY;
    proc->priority = priority;
    proc->time_slice = SCHED_DEFAULT_QUANTUM;
    proc->page_directory = vmm_create_address_space();
    strncpy(proc->name, name, 63);
    proc->name[63] = '\0';

    proc->kernel_stack = (uint32_t)kmalloc(STACK_SIZE) + STACK_SIZE;
    proc->user_stack = 0x7FF00000;

    vmm_map_page(proc->page_directory, proc->user_stack - PAGE_SIZE,
        (uint32_t)pmm_alloc_block(), VMM_USER | VMM_WRITE | VMM_PRESENT);

    memset(&proc->context, 0, sizeof(process_context_t));
    proc->context.eip = (uint32_t)entry_point;
    proc->context.esp = proc->user_stack;
    proc->context.ebp = proc->user_stack;
    proc->context.eflags = 0x202;
    proc->context.cs = (GDT_USER_CODE * 8) | 3;
    proc->context.ss = (GDT_USER_DATA * 8) | 3;
    proc->context.ds = (GDT_USER_DATA * 8) | 3;
    proc->context.es = (GDT_USER_DATA * 8) | 3;
    proc->context.fs = (GDT_USER_DATA * 8) | 3;
    proc->context.gs = (GDT_USER_DATA * 8) | 3;

    proc->next = process_list;
    proc->prev = NULL;
    if (process_list) process_list->prev = proc;
    process_list = proc;

    scheduler_add_process(proc);
    return proc;
}

void process_destroy(process_t* proc) {
    if (!proc) return;

    proc->state = PROCESS_TERMINATED;

    if (proc->prev) proc->prev->next = proc->next;
    else process_list = proc->next;
    if (proc->next) proc->next->prev = proc->prev;

    scheduler_remove_process(proc);
    kfree(proc);
}

void process_switch(process_t* next) {
    process_t* prev = current_process;

    if (prev == next) return;

    current_process = next;
    next->state = PROCESS_RUNNING;

    if (prev) {
        prev->state = PROCESS_READY;
        context_switch(&prev->context, &next->context);
    } else {
        context_switch_first(&next->context);
    }
}

process_t* process_get_current(void) {
    return current_process;
}

process_t* process_get_by_pid(pid_t pid) {
    process_t* proc = process_list;
    while (proc) {
        if (proc->pid == pid) return proc;
        proc = proc->next;
    }
    return NULL;
}
