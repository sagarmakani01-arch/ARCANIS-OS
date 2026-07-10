/**
 * edge.h — Edge Computing
 *
 * Edge node management, workload offloading, and edge-cloud sync.
 */
#ifndef ARCANIS_EDGE_H
#define ARCANIS_EDGE_H

#include <arcanis/types.h>

#define EDGE_MAX_NODES      128
#define EDGE_MAX_WORKLOADS  256
#define EDGE_MAX_POLICIES   64
#define EDGE_MAX_NAME       64
#define EDGE_MAX_ADDR       256

typedef enum {
    EDGE_NODE_EDGE,
    EDGE_NODE_FOG,
    EDGE_NODE_CLOUD
} edge_node_type_t;

typedef enum {
    EDGE_STATE_ONLINE,
    EDGE_STATE_OFFLINE,
    EDGE_STATE_DEGRADED,
    EDGE_STATE_MAINTENANCE
} edge_node_state_t;

typedef enum {
    WORKLOAD_STATE_PENDING,
    WORKLOAD_STATE_RUNNING,
    WORKLOAD_STATE_COMPLETED,
    WORKLOAD_STATE_FAILED,
    WORKLOAD_STATE_MIGRATING
} workload_state_t;

typedef enum {
    POLICY_LATENCY,
    POLICY_BANDWIDTH,
    POLICY_COST,
    POLICY_ENERGY,
    POLICY_SECURITY
} policy_type_t;

typedef struct {
    uint32_t id;
    char name[EDGE_MAX_NAME];
    char address[EDGE_MAX_ADDR];
    uint16_t port;
    edge_node_type_t type;
    edge_node_state_t state;
    uint32_t cpu_cores;
    uint64_t memory_mb;
    uint64_t storage_gb;
    uint32_t bandwidth_mbps;
    float cpu_usage;
    float memory_usage;
    uint32_t latency_ms;
    uint32_t temperature;
    uint32_t power_watts;
    uint32_t num_workloads;
    uint64_t total_processed;
    uint32_t last_heartbeat;
} edge_node_t;

typedef struct {
    uint32_t id;
    char name[EDGE_MAX_NAME];
    workload_state_t state;
    uint32_t source_node;
    uint32_t target_node;
    uint32_t cpu_required;
    uint64_t memory_required;
    uint64_t data_size;
    uint32_t deadline_ms;
    uint32_t priority;
    uint64_t start_time;
    uint64_t end_time;
    int      migrated;
} edge_workload_t;

typedef struct {
    uint32_t id;
    char name[EDGE_MAX_NAME];
    policy_type_t type;
    uint32_t weight;
    int enabled;
    char conditions[256];
} edge_policy_t;

typedef struct {
    edge_node_t nodes[EDGE_MAX_NODES];
    uint32_t num_nodes;

    edge_workload_t workloads[EDGE_MAX_WORKLOADS];
    uint32_t num_workloads;

    edge_policy_t policies[EDGE_MAX_POLICIES];
    uint32_t num_policies;

    uint64_t total_workloads;
    uint64_t successful_workloads;
    uint64_t failed_workloads;
    uint32_t avg_latency_ms;
} edge_manager_t;

/* Initialize edge manager */
void edge_init(edge_manager_t* mgr);

/* Node management */
int   edge_add_node(edge_manager_t* mgr, const char* name, const char* address,
                   uint16_t port, edge_node_type_t type);
int   edge_remove_node(edge_manager_t* mgr, uint32_t node_id);
int   edge_update_node_status(edge_manager_t* mgr, uint32_t node_id,
                             float cpu, float memory, uint32_t latency);
int   edge_list_nodes(edge_manager_t* mgr, char* buf, uint32_t buf_len);
int   edge_get_node_info(edge_manager_t* mgr, uint32_t node_id, char* buf, uint32_t buf_len);
int   edge_find_best_node(edge_manager_t* mgr, uint32_t cpu_req, uint64_t mem_req,
                         uint32_t max_latency, uint32_t* node_id);

/* Workload management */
int   edge_submit_workload(edge_manager_t* mgr, const char* name,
                          uint32_t cpu_req, uint64_t mem_req,
                          uint64_t data_size, uint32_t deadline_ms,
                          uint32_t priority);
int   edge_cancel_workload(edge_manager_t* mgr, uint32_t workload_id);
int   edge_migrate_workload(edge_manager_t* mgr, uint32_t workload_id,
                           uint32_t target_node);
int   edge_list_workloads(edge_manager_t* mgr, char* buf, uint32_t buf_len);
int   edge_get_workload_info(edge_manager_t* mgr, uint32_t workload_id,
                            char* buf, uint32_t buf_len);

/* Policy management */
int   edge_add_policy(edge_manager_t* mgr, const char* name,
                     policy_type_t type, uint32_t weight,
                     const char* conditions);
int   edge_remove_policy(edge_manager_t* mgr, uint32_t policy_id);
int   edge_list_policies(edge_manager_t* mgr, char* buf, uint32_t buf_len);

/* Edge-Cloud sync */
int   edge_sync_data(edge_manager_t* mgr, uint32_t node_id,
                    const char* path, int to_cloud);
int   edge_offload(edge_manager_t* mgr, uint32_t workload_id);
int   edge_prefetch(edge_manager_t* mgr, uint32_t node_id,
                   const char* data_key);

/* Monitoring */
int   edge_get_stats(edge_manager_t* mgr, char* buf, uint32_t buf_len);
int   edge_get_cluster_health(edge_manager_t* mgr, char* buf, uint32_t buf_len);
int   edge_optimize_placement(edge_manager_t* mgr);

#endif
