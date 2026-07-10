/**
 * container.h — Container Runtime
 *
 * Lightweight container runtime with namespaces, cgroups, and image support.
 * Similar to Docker but built into Arcanis OS.
 */
#ifndef ARCANIS_CONTAINER_H
#define ARCANIS_CONTAINER_H

#include <arcanis/types.h>

#define CONT_MAX_CONTAINERS  32
#define CONT_MAX_IMAGES      64
#define CONT_MAX_LAYERS      8
#define CONT_MAX_NAME        64
#define CONT_MAX_PATH        256
#define CONT_MAX_ENV         32
#define CONT_MAX_CMD         128

typedef enum {
    CONT_STATE_CREATED,
    CONT_STATE_RUNNING,
    CONT_STATE_PAUSED,
    CONT_STATE_STOPPED,
    CONT_STATE_DEAD
} container_state_t;

typedef enum {
    NS_PID,
    NS_MOUNT,
    NS_NET,
    NS_UTS,
    NS_IPC,
    NS_USER
} namespace_type_t;

typedef struct {
    namespace_type_t type;
    int enabled;
    uint32_t ns_id;
} container_namespace_t;

typedef struct {
    uint64_t cpu_quota;    /* CPU quota in microseconds */
    uint64_t cpu_period;   /* CPU period in microseconds */
    uint64_t memory_limit; /* Memory limit in bytes */
    uint64_t memory_usage; /* Current memory usage */
    uint32_t pids_limit;   /* Max PIDs */
    uint32_t pids_current; /* Current PIDs */
    uint64_t blkio_read;   /* Block I/O read bytes */
    uint64_t blkio_write;  /* Block I/O write bytes */
} container_cgroup_t;

typedef struct {
    char name[CONT_MAX_NAME];
    char version[32];
    char digest[64];
    uint32_t size;
    int present;
} container_layer_t;

typedef struct {
    char name[CONT_MAX_NAME];
    char tag[32];
    char digest[64];
    container_layer_t layers[CONT_MAX_LAYERS];
    uint32_t num_layers;
    uint64_t total_size;
    int present;
} container_image_t;

typedef struct {
    uint32_t id;
    char name[CONT_MAX_NAME];
    container_state_t state;
    container_namespace_t namespaces[6];
    container_cgroup_t cgroup;
    char rootfs[CONT_MAX_PATH];
    char workdir[CONT_MAX_PATH];
    char entrypoint[CONT_MAX_CMD];
    char command[CONT_MAX_CMD];
    char env[CONT_MAX_ENV][256];
    uint32_t num_env;
    uint32_t pid;
    uint32_t ppid;
    uint64_t created_time;
    uint64_t started_time;
    uint64_t memory_used;
    uint32_t cpu_percent;
    char image[CONT_MAX_NAME];
    char ip_address[16];
    uint16_t ports[32];
    uint32_t num_ports;
} container_t;

typedef struct {
    container_t containers[CONT_MAX_CONTAINERS];
    container_image_t images[CONT_MAX_IMAGES];
    uint32_t num_containers;
    uint32_t num_images;
    uint32_t next_id;
} container_runtime_t;

/* Initialize container runtime */
void container_init(container_runtime_t* runtime);

/* Container management */
int   container_create(container_runtime_t* runtime, const char* name,
                       const char* image, const char* command);
int   container_start(container_runtime_t* runtime, uint32_t id);
int   container_stop(container_runtime_t* runtime, uint32_t id);
int   container_pause(container_runtime_t* runtime, uint32_t id);
int   container_resume(container_runtime_t* runtime, uint32_t id);
int   container_destroy(container_runtime_t* runtime, uint32_t id);
int   container_exec(container_runtime_t* runtime, uint32_t id, const char* command);
int   container_list(container_runtime_t* runtime, char* buf, uint32_t buf_len);
int   container_inspect(container_runtime_t* runtime, uint32_t id, char* buf, uint32_t buf_len);

/* Container operations */
int   container_logs(container_runtime_t* runtime, uint32_t id, uint32_t lines);
int   container_cp(container_runtime_t* runtime, uint32_t id, const char* src, const char* dst);
int   container_stats(container_runtime_t* runtime, uint32_t id, char* buf, uint32_t buf_len);

/* Image management */
int   container_pull_image(container_runtime_t* runtime, const char* name, const char* tag);
int   container_list_images(container_runtime_t* runtime, char* buf, uint32_t buf_len);
int   container_remove_image(container_runtime_t* runtime, const char* name);
int   container_image_info(container_runtime_t* runtime, const char* name, char* buf, uint32_t buf_len);

/* Namespace management */
int   container_enable_namespace(container_runtime_t* runtime, uint32_t id, namespace_type_t ns);
int   container_disable_namespace(container_runtime_t* runtime, uint32_t id, namespace_type_t ns);

/* Cgroup management */
int   container_set_cpu_limit(container_runtime_t* runtime, uint32_t id, uint64_t quota, uint64_t period);
int   container_set_memory_limit(container_runtime_t* runtime, uint32_t id, uint64_t limit);
int   container_set_pids_limit(container_runtime_t* runtime, uint32_t id, uint32_t limit);
int   container_get_stats(container_runtime_t* runtime, uint32_t id, container_cgroup_t* stats);

/* Network */
int   container_set_ip(container_runtime_t* runtime, uint32_t id, const char* ip);
int   container_add_port(container_runtime_t* runtime, uint32_t id, uint16_t port);

#endif
