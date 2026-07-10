/**
 * distributed.h — Distributed Systems
 *
 * Consensus algorithms, distributed storage, and cluster management.
 */
#ifndef ARCANIS_DISTRIBUTED_H
#define ARCANIS_DISTRIBUTED_H

#include <arcanis/types.h>

#define DIST_MAX_NODES     64
#define DIST_MAX_SHARDS    32
#define DIST_MAX_REPLICAS  8
#define DIST_MAX_PARTITIONS 128
#define DIST_MAX_NAME      64
#define DIST_MAX_ADDR      256

typedef enum {
    NODE_LEADER,
    NODE_FOLLOWER,
    NODE_CANDIDATE,
    NODE_DOWN
} node_state_t;

typedef enum {
    CONSENSUS_RAFT,
    CONSENSUS_PAXOS,
    CONSENSUS_PBFT,
    CONSENSUS_GOSSIP
} consensus_type_t;

typedef enum {
    SHARD_ACTIVE,
    SHARD_RECOVERING,
    SHARD_MIGRATING,
    SHARD_OFFLINE
} shard_state_t;

typedef struct {
    uint32_t id;
    char name[DIST_MAX_NAME];
    char address[DIST_MAX_ADDR];
    uint16_t port;
    node_state_t state;
    uint64_t term;
    uint64_t log_index;
    uint64_t commit_index;
    uint32_t last_heartbeat;
    uint32_t config_version;
    int      voter;
} dist_node_t;

typedef struct {
    uint32_t term;
    uint64_t index;
    uint32_t type;      /* 0=command, 1=config, 2=heartbeat */
    char data[1024];
    uint32_t leader_id;
} log_entry_t;

typedef struct {
    uint32_t id;
    shard_state_t state;
    uint32_t leader_node;
    uint32_t replicas[DIST_MAX_REPLICAS];
    uint32_t num_replicas;
    uint64_t data_size;
    uint32_t key_range_start;
    uint32_t key_range_end;
} dist_shard_t;

typedef struct {
    uint32_t id;
    char key[256];
    char value[4096];
    uint64_t version;
    uint64_t timestamp;
    uint32_t shard_id;
    int locked;
} dist_kv_t;

typedef struct {
    dist_node_t nodes[DIST_MAX_NODES];
    uint32_t num_nodes;

    dist_shard_t shards[DIST_MAX_SHARDS];
    uint32_t num_shards;

    dist_kv_t data[DIST_MAX_PARTITIONS];
    uint32_t num_data;

    log_entry_t log[1024];
    uint32_t log_size;
    uint64_t current_term;

    consensus_type_t consensus;
    uint32_t quorum_size;

    uint64_t total_requests;
    uint64_t successful_requests;
    uint64_t failed_requests;
} distributed_manager_t;

/* Initialize distributed manager */
void dist_init(distributed_manager_t* mgr);

/* Node management */
int   dist_add_node(distributed_manager_t* mgr, const char* name,
                   const char* address, uint16_t port);
int   dist_remove_node(distributed_manager_t* mgr, uint32_t node_id);
int   dist_get_node(distributed_manager_t* mgr, uint32_t node_id, dist_node_t* node);
int   dist_list_nodes(distributed_manager_t* mgr, char* buf, uint32_t buf_len);

/* Consensus */
int   dist_elect_leader(distributed_manager_t* mgr);
int   dist_append_log(distributed_manager_t* mgr, uint32_t node_id,
                     const log_entry_t* entry);
int   dist_replicate_log(distributed_manager_t* mgr, uint32_t leader_id);
int   dist_commit_log(distributed_manager_t* mgr, uint64_t index);
int   dist_get_log(distributed_manager_t* mgr, uint32_t node_id,
                  log_entry_t* entries, uint32_t* count);

/* Shard management */
int   dist_create_shard(distributed_manager_t* mgr, uint32_t leader_node);
int   dist_delete_shard(distributed_manager_t* mgr, uint32_t shard_id);
int   dist_split_shard(distributed_manager_t* mgr, uint32_t shard_id);
int   dist_merge_shard(distributed_manager_t* mgr, uint32_t shard1, uint32_t shard2);
int   dist_migrate_shard(distributed_manager_t* mgr, uint32_t shard_id, uint32_t target_node);
int   dist_list_shards(distributed_manager_t* mgr, char* buf, uint32_t buf_len);

/* Key-Value operations */
int   dist_kv_put(distributed_manager_t* mgr, const char* key, const char* value);
int   dist_kv_get(distributed_manager_t* mgr, const char* key, char* value, uint32_t* value_len);
int   dist_kv_delete(distributed_manager_t* mgr, const char* key);
int   dist_kv_list(distributed_manager_t* mgr, char* buf, uint32_t buf_len);
int   dist_kv_acquire_lock(distributed_manager_t* mgr, const char* key, uint32_t node_id);
int   dist_kv_release_lock(distributed_manager_t* mgr, const char* key, uint32_t node_id);

/* Cluster operations */
int   dist_join_cluster(distributed_manager_t* mgr, const char* address, uint16_t port);
int   dist_leave_cluster(distributed_manager_t* mgr, uint32_t node_id);
int   dist_cluster_status(distributed_manager_t* mgr, char* buf, uint32_t buf_len);
int   dist_cluster_stats(distributed_manager_t* mgr, char* buf, uint32_t buf_len);

/* Failure detection */
int   dist_heartbeat(distributed_manager_t* mgr, uint32_t sender_id, uint32_t receiver_id);
int   dist_check_failure(distributed_manager_t* mgr, uint32_t node_id);
int   dist_mark_down(distributed_manager_t* mgr, uint32_t node_id);
int   dist_recover_node(distributed_manager_t* mgr, uint32_t node_id);

#endif
