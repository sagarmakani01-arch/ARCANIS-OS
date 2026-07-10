/**
 * hypervisor.h — Virtual Machine Manager
 *
 * Type-2 hypervisor for Arcanis OS.
 * Supports VM creation, memory mapping, CPU scheduling, and I/O virtualization.
 */
#ifndef ARCANIS_HYPERVISOR_H
#define ARCANIS_HYPERVISOR_H

#include <arcanis/types.h>

#define HYPER_MAX_VMS       16
#define HYPER_MAX_VCPU      4
#define HYPER_MAX_MEMORY    (512 * 1024 * 1024)  /* 512MB */
#define HYPER_PAGE_SIZE     4096
#define HYPER_MAX_REGIONS   32
#define HYPER_MAX_IO        256
#define HYPER_MAX_NAME      64

typedef enum {
    VM_STATE_CREATED,
    VM_STATE_RUNNING,
    VM_STATE_PAUSED,
    VM_STATE_STOPPED,
    VM_STATE_CRASHED
} vm_state_t;

typedef enum {
    VCPU_STATE_RUNNING,
    VCPU_STATE_HALTED,
    VCPU_STATE_WAITING
} vcpu_state_t;

typedef struct {
    uint32_t eax, ebx, ecx, edx;
    uint32_t esi, edi, ebp, esp;
    uint32_t eip, eflags;
    uint16_t cs, ds, es, fs, gs, ss;
    uint32_t cr0, cr3, cr4;
    vcpu_state_t state;
} vcpu_t;

typedef struct {
    uint64_t gpa;       /* Guest physical address */
    uint64_t hpa;       /* Host physical address */
    uint64_t size;
    int      readable;
    int      writable;
    int      executable;
    int      present;
} vm_memory_region_t;

typedef struct {
    uint16_t port;
    uint16_t size;
    int      (*read)(uint16_t port, uint8_t* data, uint16_t size);
    int      (*write)(uint16_t port, const uint8_t* data, uint16_t size);
} vm_io_handler_t;

typedef struct {
    uint32_t id;
    char     name[HYPER_MAX_NAME];
    vm_state_t state;
    vcpu_t  vcpus[HYPER_MAX_VCPU];
    uint32_t num_vcpus;
    uint8_t* memory;
    uint64_t memory_size;
    vm_memory_region_t regions[HYPER_MAX_REGIONS];
    uint32_t num_regions;
    vm_io_handler_t io_handlers[HYPER_MAX_IO];
    uint32_t num_io;
    uint32_t exit_code;
    uint64_t entry_point;
    uint64_t cmdline_addr;
} vm_t;

typedef struct {
    vm_t vms[HYPER_MAX_VMS];
    uint32_t num_vms;
    uint32_t next_id;
    uint64_t total_memory;
    uint64_t used_memory;
} hypervisor_t;

/* Initialize hypervisor */
void hyper_init(hypervisor_t* hyper);

/* VM management */
int   hyper_create_vm(hypervisor_t* hyper, const char* name, uint64_t memory_size);
int   hyper_destroy_vm(hypervisor_t* hyper, uint32_t vm_id);
vm_t* hyper_get_vm(hypervisor_t* hyper, uint32_t vm_id);
int   hyper_list_vms(hypervisor_t* hyper, char* buf, uint32_t buf_len);

/* VM lifecycle */
int   hyper_start_vm(hypervisor_t* hyper, uint32_t vm_id);
int   hyper_stop_vm(hypervisor_t* hyper, uint32_t vm_id);
int   hyper_pause_vm(hypervisor_t* hyper, uint32_t vm_id);
int   hyper_resume_vm(hypervisor_t* hyper, uint32_t vm_id);

/* Memory management */
int   hyper_map_memory(hypervisor_t* hyper, uint32_t vm_id,
                       uint64_t gpa, uint64_t size, int rw);
int   hyper_unmap_memory(hypervisor_t* hyper, uint32_t vm_id, uint64_t gpa);
int   hyper_read_vm_memory(hypervisor_t* hyper, uint32_t vm_id,
                           uint64_t gpa, uint8_t* data, uint64_t size);
int   hyper_write_vm_memory(hypervisor_t* hyper, uint32_t vm_id,
                            uint64_t gpa, const uint8_t* data, uint64_t size);

/* VCPU management */
int   hyper_create_vcpu(hypervisor_t* hyper, uint32_t vm_id);
int   hyper_run_vcpu(hypervisor_t* hyper, uint32_t vm_id, uint32_t vcpu_id);
int   hyper_inject_irq(hypervisor_t* hyper, uint32_t vm_id, uint32_t vcpu_id, uint32_t vector);

/* I/O virtualization */
int   hyper_register_io(hypervisor_t* hyper, uint32_t vm_id,
                        uint16_t port, uint16_t size,
                        int (*read)(uint16_t, uint8_t*, uint16_t),
                        int (*write)(uint16_t, const uint8_t*, uint16_t));

/* Console */
int   hyper_vm_console_write(hypervisor_t* hyper, uint32_t vm_id,
                             const char* str, uint32_t len);

#endif
