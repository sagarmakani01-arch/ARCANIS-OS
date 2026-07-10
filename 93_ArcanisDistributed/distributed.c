/**
 * distributed.c — Distributed Systems Implementation
 *
 * Consensus algorithms, distributed storage, and cluster management.
 */
#include <arcanis/distributed.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>
#include <stdlib.h>

/* ---- Initialization ---- */

void dist_init(distributed_manager_t* mgr) {
    if (!mgr) return;
    memset(mgr, 0, sizeof(distributed_manager_t));
    mgr->consensus = CONSENSUS_RAFT;
    mgr->quorum_size = 3;
}

/* ---- Node management ---- */

static dist_node_t* find_node(distributed_manager_t* mgr, uint32_t id) {
    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        if (mgr->nodes[i].id == id)
            return &mgr->nodes[i];
    }
    return NULL;
}

int dist_add_node(distributed_manager_t* mgr, const char* name,
                 const char* address, uint16_t port) {
    if (!mgr || !name || !address) return -1;
    if (mgr->num_nodes >= DIST_MAX_NODES) return -1;

    dist_node_t* node = &mgr->nodes[mgr->num_nodes];
    memset(node, 0, sizeof(dist_node_t));

    node->id = mgr->num_nodes + 1;
    string_copy(node->name, name, DIST_MAX_NAME);
    string_copy(node->address, address, DIST_MAX_ADDR);
    node->port = port;
    node->state = NODE_FOLLOWER;
    node->term = mgr->current_term;
    node->voter = 1;

    mgr->num_nodes++;
    printf("[DIST] Node '%s' added at %s:%u\n", name, address, port);
    return (int)node->id;
}

int dist_remove_node(distributed_manager_t* mgr, uint32_t node_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        if (mgr->nodes[i].id == node_id) {
            printf("[DIST] Node '%s' removed\n", mgr->nodes[i].name);
            for (uint32_t j = i; j < mgr->num_nodes - 1; j++)
                mgr->nodes[j] = mgr->nodes[j + 1];
            mgr->num_nodes--;
            return 0;
        }
    }
    return -1;
}

int dist_get_node(distributed_manager_t* mgr, uint32_t node_id, dist_node_t* node) {
    if (!mgr || !node) return -1;

    dist_node_t* found = find_node(mgr, node_id);
    if (!found) return -1;

    memcpy(node, found, sizeof(dist_node_t));
    return 0;
}

int dist_list_nodes(distributed_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    const char* state_names[] = {"leader", "follower", "candidate", "down"};
    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos, "CLUSTER NODES: %u\n", mgr->num_nodes);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID  NAME            ADDRESS                 PORT   STATE     TERM\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_nodes && pos < buf_len - 150; i++) {
        dist_node_t* n = &mgr->nodes[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-15s %-23s %-6u %-9s %llu\n",
            n->id, n->name, n->address, n->port,
            state_names[n->state], (unsigned long long)n->term);
    }

    return (int)pos;
}

/* ---- Consensus ---- */

int dist_elect_leader(distributed_manager_t* mgr) {
    if (!mgr) return -1;
    if (mgr->num_nodes < 3) return -1;

    mgr->current_term++;

    /* Reset all nodes */
    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        mgr->nodes[i].term = mgr->current_term;
        mgr->nodes[i].state = NODE_CANDIDATE;
    }

    /* Simulate election - elect node with highest ID */
    uint32_t leader_id = mgr->nodes[mgr->num_nodes - 1].id;
    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        if (mgr->nodes[i].state == NODE_CANDIDATE) {
            mgr->nodes[i].state = NODE_FOLLOWER;
        }
    }

    dist_node_t* leader = find_node(mgr, leader_id);
    if (leader) {
        leader->state = NODE_LEADER;
        printf("[DIST] Leader elected: '%s' (term=%llu)\n",
               leader->name, (unsigned long long)mgr->current_term);
    }

    return 0;
}

int dist_append_log(distributed_manager_t* mgr, uint32_t node_id,
                   const log_entry_t* entry) {
    if (!mgr || !entry) return -1;

    if (mgr->log_size >= 1024) return -1;

    log_entry_t* new_entry = &mgr->log[mgr->log_size++];
    memcpy(new_entry, entry, sizeof(log_entry_t));
    new_entry->leader_id = node_id;

    printf("[DIST] Log entry appended (term=%llu, index=%llu)\n",
           (unsigned long long)entry->term, (unsigned long long)entry->index);
    return 0;
}

int dist_replicate_log(distributed_manager_t* mgr, uint32_t leader_id) {
    if (!mgr) return -1;

    dist_node_t* leader = find_node(mgr, leader_id);
    if (!leader || leader->state != NODE_LEADER) return -1;

    uint32_t replicated = 0;
    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        if (mgr->nodes[i].id != leader_id && mgr->nodes[i].state != NODE_DOWN) {
            mgr->nodes[i].log_index = mgr->log_size;
            replicated++;
        }
    }

    printf("[DIST] Log replicated to %u nodes\n", replicated);
    return 0;
}

int dist_commit_log(distributed_manager_t* mgr, uint64_t index) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        mgr->nodes[i].commit_index = index;
    }

    printf("[DIST] Log committed at index %llu\n", (unsigned long long)index);
    return 0;
}

int dist_get_log(distributed_manager_t* mgr, uint32_t node_id,
                log_entry_t* entries, uint32_t* count) {
    if (!mgr || !entries || !count) return -1;

    uint32_t to_copy = *count;
    if (to_copy > mgr->log_size) to_copy = mgr->log_size;

    for (uint32_t i = 0; i < to_copy; i++)
        memcpy(&entries[i], &mgr->log[i], sizeof(log_entry_t));

    *count = to_copy;
    return 0;
}

/* ---- Shard management ---- */

int dist_create_shard(distributed_manager_t* mgr, uint32_t leader_node) {
    if (!mgr) return -1;
    if (mgr->num_shards >= DIST_MAX_SHARDS) return -1;

    dist_shard_t* shard = &mgr->shards[mgr->num_shards];
    memset(shard, 0, sizeof(dist_shard_t));

    shard->id = mgr->num_shards + 1;
    shard->state = SHARD_ACTIVE;
    shard->leader_node = leader_node;
    shard->key_range_start = mgr->num_shards * 1000;
    shard->key_range_end = (mgr->num_shards + 1) * 1000 - 1;

    mgr->num_shards++;
    printf("[DIST] Shard %u created (keys %u-%u)\n",
           shard->id, shard->key_range_start, shard->key_range_end);
    return 0;
}

int dist_delete_shard(distributed_manager_t* mgr, uint32_t shard_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_shards; i++) {
        if (mgr->shards[i].id == shard_id) {
            printf("[DIST] Shard %u deleted\n", shard_id);
            for (uint32_t j = i; j < mgr->num_shards - 1; j++)
                mgr->shards[j] = mgr->shards[j + 1];
            mgr->num_shards--;
            return 0;
        }
    }
    return -1;
}

int dist_split_shard(distributed_manager_t* mgr, uint32_t shard_id) {
    if (!mgr) return -1;
    if (mgr->num_shards >= DIST_MAX_SHARDS) return -1;

    for (uint32_t i = 0; i < mgr->num_shards; i++) {
        if (mgr->shards[i].id == shard_id) {
            dist_shard_t* original = &mgr->shards[i];

            /* Create new shard */
            dist_shard_t* new_shard = &mgr->shards[mgr->num_shards];
            memset(new_shard, 0, sizeof(dist_shard_t));
            new_shard->id = mgr->num_shards + 1;
            new_shard->state = SHARD_ACTIVE;
            new_shard->leader_node = original->leader_node;
            new_shard->key_range_start = (original->key_range_start + original->key_range_end) / 2 + 1;
            new_shard->key_range_end = original->key_range_end;

            /* Update original shard */
            original->key_range_end = new_shard->key_range_start - 1;

            mgr->num_shards++;
            printf("[DIST] Shard %u split into %u and %u\n",
                   shard_id, original->id, new_shard->id);
            return 0;
        }
    }
    return -1;
}

int dist_merge_shard(distributed_manager_t* mgr, uint32_t shard1, uint32_t shard2) {
    if (!mgr) return -1;

    dist_shard_t* s1 = NULL;
    dist_shard_t* s2 = NULL;

    for (uint32_t i = 0; i < mgr->num_shards; i++) {
        if (mgr->shards[i].id == shard1) s1 = &mgr->shards[i];
        if (mgr->shards[i].id == shard2) s2 = &mgr->shards[i];
    }

    if (!s1 || !s2) return -1;

    s1->key_range_end = s2->key_range_end;

    /* Remove s2 */
    for (uint32_t i = 0; i < mgr->num_shards; i++) {
        if (mgr->shards[i].id == shard2) {
            for (uint32_t j = i; j < mgr->num_shards - 1; j++)
                mgr->shards[j] = mgr->shards[j + 1];
            mgr->num_shards--;
            break;
        }
    }

    printf("[DIST] Shards %u and %u merged\n", shard1, shard2);
    return 0;
}

int dist_migrate_shard(distributed_manager_t* mgr, uint32_t shard_id, uint32_t target_node) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_shards; i++) {
        if (mgr->shards[i].id == shard_id) {
            mgr->shards[i].state = SHARD_MIGRATING;
            mgr->shards[i].leader_node = target_node;
            printf("[DIST] Shard %u migrating to node %u\n", shard_id, target_node);
            mgr->shards[i].state = SHARD_ACTIVE;
            return 0;
        }
    }
    return -1;
}

int dist_list_shards(distributed_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    const char* state_names[] = {"active", "recovering", "migrating", "offline"};
    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos, "SHARDS: %u\n", mgr->num_shards);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID  STATE       LEADER  KEY RANGE       REPLICAS\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_shards && pos < buf_len - 150; i++) {
        dist_shard_t* s = &mgr->shards[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-11s %-7u %5u-%-5u       %u\n",
            s->id, state_names[s->state], s->leader_node,
            s->key_range_start, s->key_range_end,
            s->num_replicas);
    }

    return (int)pos;
}

/* ---- Key-Value operations ---- */

static dist_kv_t* find_kv(distributed_manager_t* mgr, const char* key) {
    for (uint32_t i = 0; i < mgr->num_data; i++) {
        if (string_compare(mgr->data[i].key, key) == 0)
            return &mgr->data[i];
    }
    return NULL;
}

int dist_kv_put(distributed_manager_t* mgr, const char* key, const char* value) {
    if (!mgr || !key || !value) return -1;

    dist_kv_t* kv = find_kv(mgr, key);
    if (kv) {
        string_copy(kv->value, value, 4096);
        kv->version++;
        kv->timestamp = 0;
    } else {
        if (mgr->num_data >= DIST_MAX_PARTITIONS) return -1;

        kv = &mgr->data[mgr->num_data++];
        memset(kv, 0, sizeof(dist_kv_t));
        string_copy(kv->key, key, 256);
        string_copy(kv->value, value, 4096);
        kv->version = 1;
        kv->timestamp = 0;
        kv->shard_id = (hash(key) % mgr->num_shards) + 1;
    }

    printf("[DIST] PUT %s = %s (v%llu)\n", key, value, (unsigned long long)kv->version);
    return 0;
}

int dist_kv_get(distributed_manager_t* mgr, const char* key, char* value, uint32_t* value_len) {
    if (!mgr || !key || !value || !value_len) return -1;

    dist_kv_t* kv = find_kv(mgr, key);
    if (!kv) return -1;

    uint32_t len = string_length(kv->value);
    if (len >= *value_len) return -1;

    string_copy(value, kv->value, *value_len);
    *value_len = len;

    printf("[DIST] GET %s = %s\n", key, kv->value);
    return 0;
}

int dist_kv_delete(distributed_manager_t* mgr, const char* key) {
    if (!mgr || !key) return -1;

    for (uint32_t i = 0; i < mgr->num_data; i++) {
        if (string_compare(mgr->data[i].key, key) == 0) {
            printf("[DIST] DELETE %s\n", key);
            for (uint32_t j = i; j < mgr->num_data - 1; j++)
                mgr->data[j] = mgr->data[j + 1];
            mgr->num_data--;
            return 0;
        }
    }
    return -1;
}

int dist_kv_list(distributed_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "KEY-VALUE STORE: %u entries\n", mgr->num_data);
    pos += snprintf(buf + pos, buf_len - pos, "KEY                 VALUE                VERSION\n");
    pos += snprintf(buf + pos, buf_len - pos, "--------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_data && pos < buf_len - 100; i++) {
        dist_kv_t* kv = &mgr->data[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-19s %-20s %llu\n",
            kv->key, kv->value, (unsigned long long)kv->version);
    }

    return (int)pos;
}

int dist_kv_acquire_lock(distributed_manager_t* mgr, const char* key, uint32_t node_id) {
    if (!mgr || !key) return -1;

    dist_kv_t* kv = find_kv(mgr, key);
    if (!kv) return -1;
    if (kv->locked) return -1;

    kv->locked = 1;
    printf("[DIST] Lock acquired on '%s' by node %u\n", key, node_id);
    return 0;
}

int dist_kv_release_lock(distributed_manager_t* mgr, const char* key, uint32_t node_id) {
    if (!mgr || !key) return -1;

    dist_kv_t* kv = find_kv(mgr, key);
    if (!kv) return -1;

    kv->locked = 0;
    printf("[DIST] Lock released on '%s' by node %u\n", key, node_id);
    return 0;
}

/* ---- Cluster operations ---- */

int dist_join_cluster(distributed_manager_t* mgr, const char* address, uint16_t port) {
    if (!mgr || !address) return -1;

    printf("[DIST] Joining cluster at %s:%u\n", address, port);
    return 0;
}

int dist_leave_cluster(distributed_manager_t* mgr, uint32_t node_id) {
    if (!mgr) return -1;

    dist_node_t* node = find_node(mgr, node_id);
    if (!node) return -1;

    printf("[DIST] Node '%s' leaving cluster\n", node->name);
    node->state = NODE_DOWN;
    return 0;
}

int dist_cluster_status(distributed_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    uint32_t leaders = 0, followers = 0, candidates = 0, down = 0;
    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        switch (mgr->nodes[i].state) {
            case NODE_LEADER: leaders++; break;
            case NODE_FOLLOWER: followers++; break;
            case NODE_CANDIDATE: candidates++; break;
            case NODE_DOWN: down++; break;
        }
    }

    return snprintf(buf, buf_len,
        "Cluster Status:\n"
        "  Nodes: %u total\n"
        "  Leaders: %u\n"
        "  Followers: %u\n"
        "  Candidates: %u\n"
        "  Down: %u\n"
        "  Shards: %u\n"
        "  Consensus: %s\n"
        "  Current Term: %llu\n",
        mgr->num_nodes, leaders, followers, candidates, down,
        mgr->num_shards,
        mgr->consensus == 0 ? "Raft" : mgr->consensus == 1 ? "Paxos" : "PBFT",
        (unsigned long long)mgr->current_term);
}

int dist_cluster_stats(distributed_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    return snprintf(buf, buf_len,
        "Cluster Statistics:\n"
        "  Total Requests: %llu\n"
        "  Successful: %llu\n"
        "  Failed: %llu\n"
        "  Success Rate: %.2f%%\n"
        "  Data Entries: %u\n"
        "  Log Size: %u\n",
        (unsigned long long)mgr->total_requests,
        (unsigned long long)mgr->successful_requests,
        (unsigned long long)mgr->failed_requests,
        mgr->total_requests > 0 ?
            (float)mgr->successful_requests / mgr->total_requests * 100 : 0,
        mgr->num_data, mgr->log_size);
}

/* ---- Failure detection ---- */

int dist_heartbeat(distributed_manager_t* mgr, uint32_t sender_id, uint32_t receiver_id) {
    if (!mgr) return -1;

    dist_node_t* sender = find_node(mgr, sender_id);
    dist_node_t* receiver = find_node(mgr, receiver_id);
    if (!sender || !receiver) return -1;

    receiver->last_heartbeat = 0;
    return 0;
}

int dist_check_failure(distributed_manager_t* mgr, uint32_t node_id) {
    if (!mgr) return -1;

    dist_node_t* node = find_node(mgr, node_id);
    if (!node) return -1;

    /* Check if heartbeat timeout */
    if (node->last_heartbeat > 5000) {
        printf("[DIST] Node '%s' appears to be down\n", node->name);
        return 1;
    }
    return 0;
}

int dist_mark_down(distributed_manager_t* mgr, uint32_t node_id) {
    if (!mgr) return -1;

    dist_node_t* node = find_node(mgr, node_id);
    if (!node) return -1;

    node->state = NODE_DOWN;
    printf("[DIST] Node '%s' marked as down\n", node->name);
    return 0;
}

int dist_recover_node(distributed_manager_t* mgr, uint32_t node_id) {
    if (!mgr) return -1;

    dist_node_t* node = find_node(mgr, node_id);
    if (!node) return -1;

    node->state = NODE_FOLLOWER;
    node->last_heartbeat = 0;
    printf("[DIST] Node '%s' recovered\n", node->name);
    return 0;
}
