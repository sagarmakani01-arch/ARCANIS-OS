#ifndef ARCANIS_INIT_H
#define ARCANIS_INIT_H

#include <arcanis/types.h>

#define SERVICE_MAX     64
#define SERVICE_NAME_MAX 32
#define SERVICE_DESC_MAX 128
#define SERVICE_CMD_MAX  256

typedef enum {
    SVC_STOPPED = 0,
    SVC_STARTING,
    SVC_RUNNING,
    SVC_STOPPING,
    SVC_FAILED,
    SVC_DISABLED,
} service_state_t;

typedef enum {
    SVC_ON_BOOT = 0,
    SVC_ON_DEMAND,
    SVC_MANUAL,
} service_start_t;

typedef struct {
    char     name[SERVICE_NAME_MAX];
    char     description[SERVICE_DESC_MAX];
    char     exec[SERVICE_CMD_MAX];
    uint32_t pid;
    service_state_t  state;
    service_start_t  start_type;
    int      restart_count;
    int      max_restarts;
    uint32_t last_start;
    uint32_t last_stop;
    uint8_t  in_use;
} service_t;

typedef struct {
    service_t services[SERVICE_MAX];
    uint32_t  count;
    uint32_t  boot_time;
} init_system_t;

void         init_system_init(init_system_t* sys);
int          service_register(init_system_t* sys, const char* name, const char* desc,
                              const char* exec, service_start_t start);
int          service_start(init_system_t* sys, const char* name);
int          service_stop(init_system_t* sys, const char* name);
int          service_restart(init_system_t* sys, const char* name);
service_t*   service_find(init_system_t* sys, const char* name);
int          service_list(init_system_t* sys, service_t* out, uint32_t max);
int          service_set_state(init_system_t* sys, const char* name, service_state_t state);
void         init_boot(init_system_t* sys);
void         init_shutdown(init_system_t* sys);

#endif
