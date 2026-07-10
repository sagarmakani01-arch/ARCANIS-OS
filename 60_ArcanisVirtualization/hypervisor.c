/**
 * hypervisor.c — Virtual Machine Manager Implementation
 *
 * Type-2 hypervisor for Arcanis OS.
 */
#include <arcanis/hypervisor.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>

/* ---- Initialization ---- */

void hyper_init(hypervisor_t* hyper) {
    if (!hyper) return;
    memset(hyper, 0, sizeof(hypervisor_t));
    hyper->next_id = 1;
    hyper->total_memory = HYPER_MAX_MEMORY;
}

/* ---- VM management ---- */

static vm_t* find_vm(hypervisor_t* hyper, uint32_t vm_id) {
    for (uint32_t i = 0; i < hyper->num_vms; i++) {
        if (hyper->vms[i].id == vm_id)
            return &hyper->vms[i];
    }
    return NULL;
}

int hyper_create_vm(hypervisor_t* hyper, const char* name, uint64_t memory_size) {
    if (!hyper || !name) return -1;
    if (hyper->num_vms >= HYPER_MAX_VMS) return -1;
    if (hyper->used_memory + memory_size > hyper->total_memory) return -1;

    vm_t* vm = &hyper->vms[hyper->num_vms];
    memset(vm, 0, sizeof(vm_t));

    vm->id = hyper->next_id++;
    string_copy(vm->name, name, HYPER_MAX_NAME);
    vm->state = VM_STATE_CREATED;
    vm->memory_size = memory_size;
    vm->memory = malloc(memory_size);

    if (!vm->memory) return -1;
    memset(vm->memory, 0, memory_size);

    hyper->num_vms++;
    hyper->used_memory += memory_size;

    return (int)vm->id;
}

int hyper_destroy_vm(hypervisor_t* hyper, uint32_t vm_id) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;

    if (vm->state == VM_STATE_RUNNING)
        hyper_stop_vm(hyper, vm_id);

    if (vm->memory) {
        free(vm->memory);
        hyper->used_memory -= vm->memory_size;
    }

    /* Remove from array */
    for (uint32_t i = 0; i < hyper->num_vms; i++) {
        if (hyper->vms[i].id == vm_id) {
            for (uint32_t j = i; j < hyper->num_vms - 1; j++)
                hyper->vms[j] = hyper->vms[j + 1];
            hyper->num_vms--;
            break;
        }
    }

    return 0;
}

vm_t* hyper_get_vm(hypervisor_t* hyper, uint32_t vm_id) {
    if (!hyper) return NULL;
    return find_vm(hyper, vm_id);
}

int hyper_list_vms(hypervisor_t* hyper, char* buf, uint32_t buf_len) {
    if (!hyper || !buf) return 0;

    uint32_t pos = 0;
    const char* state_names[] = {"CREATED", "RUNNING", "PAUSED", "STOPPED", "CRASHED"};

    for (uint32_t i = 0; i < hyper->num_vms && pos < buf_len - 100; i++) {
        vm_t* vm = &hyper->vms[i];
        int written = snprintf(buf + pos, buf_len - pos,
            "VM %u: %s | State: %s | Memory: %lluMB | VCPUs: %u\n",
            vm->id, vm->name, state_names[vm->state],
            (unsigned long long)(vm->memory_size / (1024 * 1024)),
            vm->num_vcpus);
        pos += written;
    }
    return (int)pos;
}

/* ---- VM lifecycle ---- */

int hyper_start_vm(hypervisor_t* hyper, uint32_t vm_id) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;
    if (vm->state != VM_STATE_CREATED && vm->state != VM_STATE_STOPPED)
        return -1;

    vm->state = VM_STATE_RUNNING;
    return 0;
}

int hyper_stop_vm(hypervisor_t* hyper, uint32_t vm_id) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;

    vm->state = VM_STATE_STOPPED;
    for (uint32_t i = 0; i < vm->num_vcpus; i++)
        vm->vcpus[i].state = VCPU_STATE_HALTED;

    return 0;
}

int hyper_pause_vm(hypervisor_t* hyper, uint32_t vm_id) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;
    if (vm->state != VM_STATE_RUNNING) return -1;

    vm->state = VM_STATE_PAUSED;
    return 0;
}

int hyper_resume_vm(hypervisor_t* hyper, uint32_t vm_id) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;
    if (vm->state != VM_STATE_PAUSED) return -1;

    vm->state = VM_STATE_RUNNING;
    return 0;
}

/* ---- Memory management ---- */

static vm_memory_region_t* find_region(vm_t* vm, uint64_t gpa) {
    for (uint32_t i = 0; i < vm->num_regions; i++) {
        if (vm->regions[i].present &&
            gpa >= vm->regions[i].gpa &&
            gpa < vm->regions[i].gpa + vm->regions[i].size)
            return &vm->regions[i];
    }
    return NULL;
}

int hyper_map_memory(hypervisor_t* hyper, uint32_t vm_id,
                     uint64_t gpa, uint64_t size, int rw) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;
    if (vm->num_regions >= HYPER_MAX_REGIONS) return -1;

    /* Check for overlap */
    for (uint32_t i = 0; i < vm->num_regions; i++) {
        if (vm->regions[i].present) {
            uint64_t other_end = vm->regions[i].gpa + vm->regions[i].size;
            if (gpa < other_end && gpa + size > vm->regions[i].gpa)
                return -1; /* Overlap */
        }
    }

    vm_memory_region_t* region = &vm->regions[vm->num_regions++];
    region->gpa = gpa;
    region->hpa = gpa; /* Identity mapping for simplicity */
    region->size = size;
    region->readable = rw;
    region->writable = rw;
    region->executable = 1;
    region->present = 1;

    return 0;
}

int hyper_unmap_memory(hypervisor_t* hyper, uint32_t vm_id, uint64_t gpa) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;

    for (uint32_t i = 0; i < vm->num_regions; i++) {
        if (vm->regions[i].present && vm->regions[i].gpa == gpa) {
            vm->regions[i].present = 0;
            return 0;
        }
    }
    return -1;
}

int hyper_read_vm_memory(hypervisor_t* hyper, uint32_t vm_id,
                         uint64_t gpa, uint8_t* data, uint64_t size) {
    if (!hyper || !data) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;

    vm_memory_region_t* region = find_region(vm, gpa);
    if (!region) return -1;
    if (!region->readable) return -1;

    uint64_t offset = gpa - region->gpa;
    uint64_t hpa = region->hpa + offset;

    if (hpa + size > vm->memory_size) return -1;
    memcpy(data, vm->memory + hpa, size);

    return 0;
}

int hyper_write_vm_memory(hypervisor_t* hyper, uint32_t vm_id,
                          uint64_t gpa, const uint8_t* data, uint64_t size) {
    if (!hyper || !data) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;

    vm_memory_region_t* region = find_region(vm, gpa);
    if (!region) return -1;
    if (!region->writable) return -1;

    uint64_t offset = gpa - region->gpa;
    uint64_t hpa = region->hpa + offset;

    if (hpa + size > vm->memory_size) return -1;
    memcpy(vm->memory + hpa, data, size);

    return 0;
}

/* ---- VCPU management ---- */

int hyper_create_vcpu(hypervisor_t* hyper, uint32_t vm_id) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;
    if (vm->num_vcpus >= HYPER_MAX_VCPU) return -1;

    vcpu_t* vcpu = &vm->vcpus[vm->num_vcpus++];
    memset(vcpu, 0, sizeof(vcpu_t));
    vcpu->state = VCPU_STATE_HALTED;

    return (int)(vm->num_vcpus - 1);
}

int hyper_run_vcpu(hypervisor_t* hyper, uint32_t vm_id, uint32_t vcpu_id) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;
    if (vcpu_id >= vm->num_vcpus) return -1;

    vcpu_t* vcpu = &vm->vcpus[vcpu_id];
    vcpu->state = VCPU_STATE_RUNNING;

    /* Simulate instruction execution */
    for (int i = 0; i < 100; i++) {
        vcpu->eip += 4;
        if (vcpu->eip >= vm->memory_size) break;
    }

    vcpu->state = VCPU_STATE_HALTED;
    return 0;
}

int hyper_inject_irq(hypervisor_t* hyper, uint32_t vm_id, uint32_t vcpu_id, uint32_t vector) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;
    if (vcpu_id >= vm->num_vcpus) return -1;

    vcpu_t* vcpu = &vm->vcpus[vcpu_id];

    /* Push to stack */
    vcpu->esp -= 4;
    *(uint32_t*)(vm->memory + vcpu->esp) = vcpu->eflags;
    vcpu->esp -= 4;
    *(uint32_t*)(vm->memory + vcpu->esp) = vcpu->cs;
    vcpu->esp -= 4;
    *(uint32_t*)(vm->memory + vcpu->esp) = vcpu->eip;

    /* Jump to handler */
    vcpu->eip = vector * 4; /* IVT */
    vcpu->eflags &= ~0x200; /* Clear IF */

    return 0;
}

/* ---- I/O virtualization ---- */

int hyper_register_io(hypervisor_t* hyper, uint32_t vm_id,
                      uint16_t port, uint16_t size,
                      int (*read)(uint16_t, uint8_t*, uint16_t),
                      int (*write)(uint16_t, const uint8_t*, uint16_t)) {
    if (!hyper) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;
    if (vm->num_io >= HYPER_MAX_IO) return -1;

    vm_io_handler_t* handler = &vm->io_handlers[vm->num_io++];
    handler->port = port;
    handler->size = size;
    handler->read = read;
    handler->write = write;

    return 0;
}

/* ---- Console ---- */

int hyper_vm_console_write(hypervisor_t* hyper, uint32_t vm_id,
                           const char* str, uint32_t len) {
    if (!hyper || !str) return -1;

    vm_t* vm = find_vm(hyper, vm_id);
    if (!vm) return -1;

    printf("\033[1;36m[VM:%s]\033[0m ", vm->name);
    for (uint32_t i = 0; i < len; i++)
        putchar(str[i]);

    return (int)len;
}
