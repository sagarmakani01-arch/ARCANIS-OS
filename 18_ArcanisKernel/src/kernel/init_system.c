/**
 * init.c — Init System / Service Manager
 *
 * Manages system services: start, stop, restart, boot ordering.
 * Like systemd but simpler.
 */
#include <arcanis/init.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

void init_system_init(init_system_t* sys) {
    memset(sys, 0, sizeof(init_system_t));
    sys->boot_time = 0;
}

int service_register(init_system_t* sys, const char* name, const char* desc,
                     const char* exec, service_start_t start) {
    if (!sys || !name) return -1;
    if (sys->count >= SERVICE_MAX) return -1;
    if (service_find(sys, name)) return -1;

    service_t* svc = &sys->services[sys->count];
    string_copy(svc->name, name);
    string_copy(svc->description, desc ? desc : "");
    string_copy(svc->exec, exec ? exec : "");
    svc->pid = 0;
    svc->state = SVC_STOPPED;
    svc->start_type = start;
    svc->restart_count = 0;
    svc->max_restarts = 3;
    svc->last_start = 0;
    svc->last_stop = 0;
    svc->in_use = 1;
    sys->count++;
    return 0;
}

service_t* service_find(init_system_t* sys, const char* name) {
    if (!sys || !name) return NULL;
    for (uint32_t i = 0; i < sys->count; i++) {
        if (sys->services[i].in_use && string_compare(sys->services[i].name, name) == 0)
            return &sys->services[i];
    }
    return NULL;
}

int service_start(init_system_t* sys, const char* name) {
    service_t* svc = service_find(sys, name);
    if (!svc) return -1;
    if (svc->state == SVC_RUNNING) return 0;
    if (svc->state == SVC_DISABLED) return -2;

    svc->state = SVC_STARTING;
    /* In real OS: fork() and exec() the service */
    svc->pid = 100 + (svc - sys->services); /* Simulated PID */
    svc->state = SVC_RUNNING;
    svc->last_start = sys->boot_time;
    svc->restart_count = 0;
    return 0;
}

int service_stop(init_system_t* sys, const char* name) {
    service_t* svc = service_find(sys, name);
    if (!svc) return -1;
    if (svc->state == SVC_STOPPED) return 0;

    svc->state = SVC_STOPPING;
    /* In real OS: send SIGTERM, wait, SIGKILL */
    svc->pid = 0;
    svc->state = SVC_STOPPED;
    svc->last_stop = sys->boot_time;
    return 0;
}

int service_restart(init_system_t* sys, const char* name) {
    service_t* svc = service_find(sys, name);
    if (!svc) return -1;
    if (svc->restart_count >= svc->max_restarts) return -2;

    service_stop(sys, name);
    svc->restart_count++;
    return service_start(sys, name);
}

int service_list(init_system_t* sys, service_t* out, uint32_t max) {
    if (!sys) return 0;
    uint32_t count = 0;
    for (uint32_t i = 0; i < sys->count && count < max; i++) {
        if (sys->services[i].in_use)
            out[count++] = sys->services[i];
    }
    return (int)count;
}

int service_set_state(init_system_t* sys, const char* name, service_state_t state) {
    service_t* svc = service_find(sys, name);
    if (!svc) return -1;
    svc->state = state;
    return 0;
}

void init_boot(init_system_t* sys) {
    sys->boot_time = 1;

    /* Start boot services in order */
    for (uint32_t i = 0; i < sys->count; i++) {
        if (sys->services[i].in_use && sys->services[i].start_type == SVC_ON_BOOT) {
            service_start(sys, sys->services[i].name);
        }
    }
}

void init_shutdown(init_system_t* sys) {
    /* Stop all services in reverse order */
    for (int i = sys->count - 1; i >= 0; i--) {
        if (sys->services[i].in_use && sys->services[i].state == SVC_RUNNING) {
            service_stop(sys, sys->services[i].name);
        }
    }
}
