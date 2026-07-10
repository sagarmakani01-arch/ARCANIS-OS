/**
 * edge.c — Edge Computing Implementation
 *
 * Edge node management, workload offloading, and edge-cloud sync.
 */
#include <arcanis/edge.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>
#include <stdlib.h>

/* ---- Initialization ---- */

void edge_init(edge_manager_t* mgr) {
    if (!mgr) return;
    memset(mgr, 0, sizeof(edge_manager_t));
}

/* ---- Node management ---- */

static edge_node_t* find_node(edge_manager_t* mgr, uint32_t id) {
    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        if (mgr->nodes[i].id == id)
            return &mgr->nodes[i];
    }
    return NULL;
}

int edge_add_node(edge_manager_t* mgr, const char* name, const char* address,
                 uint16_t port, edge_node_type_t type) {
    if (!mgr || !name || !address) return -1;
    if (mgr->num_nodes >= EDGE_MAX_NODES) return -1;

    edge_node_t* node = &mgr->nodes[mgr->num_nodes];
    memset(node, 0, sizeof(edge_node_t));

    node->id = mgr->num_nodes + 1;
    string_copy(node->name, name, EDGE_MAX_NAME);
    string_copy(node->address, address, EDGE_MAX_ADDR);
    node->port = port;
    node->type = type;
    node->state = EDGE_STATE_ONLINE;
    node->cpu_cores = 4;
    node->memory_mb = 8192;
    node->storage_gb = 256;
    node->bandwidth_mbps = 1000;
    node->latency_ms = 10;

    mgr->num_nodes++;
    printf("[EDGE] Node '%s' added (type=%d)\n", name, type);
    return (int)node->id;
}

int edge_remove_node(edge_manager_t* mgr, uint32_t node_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        if (mgr->nodes[i].id == node_id) {
            printf("[EDGE] Node '%s' removed\n", mgr->nodes[i].name);
            for (uint32_t j = i; j < mgr->num_nodes - 1; j++)
                mgr->nodes[j] = mgr->nodes[j + 1];
            mgr->num_nodes--;
            return 0;
        }
    }
    return -1;
}

int edge_update_node_status(edge_manager_t* mgr, uint32_t node_id,
                           float cpu, float memory, uint32_t latency) {
    if (!mgr) return -1;

    edge_node_t* node = find_node(mgr, node_id);
    if (!node) return -1;

    node->cpu_usage = cpu;
    node->memory_usage = memory;
    node->latency_ms = latency;
    node->last_heartbeat = 0;

    if (cpu > 90 || memory > 90)
        node->state = EDGE_STATE_DEGRADED;
    else
        node->state = EDGE_STATE_ONLINE;

    return 0;
}

int edge_list_nodes(edge_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    const char* type_names[] = {"edge", "fog", "cloud"};
    const char* state_names[] = {"online", "offline", "degraded", "maintenance"};
    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos, "EDGE NODES: %u\n", mgr->num_nodes);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID  NAME            TYPE      STATE      CPU     MEM     LATENCY\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_nodes && pos < buf_len - 150; i++) {
        edge_node_t* n = &mgr->nodes[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-15s %-9s %-10s %-6.0f%% %-6.0f%% %u ms\n",
            n->id, n->name, type_names[n->type],
            state_names[n->state], n->cpu_usage, n->memory_usage,
            n->latency_ms);
    }

    return (int)pos;
}

int edge_get_node_info(edge_manager_t* mgr, uint32_t node_id, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    edge_node_t* node = find_node(mgr, node_id);
    if (!node) return -1;

    const char* type_names[] = {"edge", "fog", "cloud"};
    const char* state_names[] = {"online", "offline", "degraded", "maintenance"};
    return snprintf(buf, buf_len,
        "Node: %s\n"
        "  Type: %s\n"
        "  Address: %s:%u\n"
        "  State: %s\n"
        "  CPU: %u cores (%.1f%% used)\n"
        "  Memory: %llu MB (%.1f%% used)\n"
        "  Storage: %llu GB\n"
        "  Bandwidth: %u Mbps\n"
        "  Latency: %u ms\n"
        "  Temperature: %u C\n"
        "  Power: %u W\n"
        "  Workloads: %u\n"
        "  Total Processed: %llu\n",
        node->name, type_names[node->type],
        node->address, node->port,
        state_names[node->state],
        node->cpu_cores, node->cpu_usage,
        (unsigned long long)node->memory_mb, node->memory_usage,
        (unsigned long long)node->storage_gb,
        node->bandwidth_mbps, node->latency_ms,
        node->temperature, node->power_watts,
        node->num_workloads, (unsigned long long)node->total_processed);
}

int edge_find_best_node(edge_manager_t* mgr, uint32_t cpu_req, uint64_t mem_req,
                       uint32_t max_latency, uint32_t* node_id) {
    if (!mgr || !node_id) return -1;

    edge_node_t* best = NULL;
    float best_score = -1;

    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        edge_node_t* n = &mgr->nodes[i];
        if (n->state != EDGE_STATE_ONLINE) continue;
        if (n->cpu_usage > 90) continue;
        if (n->latency_ms > max_latency) continue;

        float score = (100 - n->cpu_usage) * (100 - n->memory_usage) / (n->latency_ms + 1);
        if (score > best_score) {
            best_score = score;
            best = n;
        }
    }

    if (best) {
        *node_id = best->id;
        printf("[EDGE] Best node: '%s' (score=%.2f)\n", best->name, best_score);
        return 0;
    }

    return -1;
}

/* ---- Workload management ---- */

static edge_workload_t* find_workload(edge_manager_t* mgr, uint32_t id) {
    for (uint32_t i = 0; i < mgr->num_workloads; i++) {
        if (mgr->workloads[i].id == id)
            return &mgr->workloads[i];
    }
    return NULL;
}

int edge_submit_workload(edge_manager_t* mgr, const char* name,
                        uint32_t cpu_req, uint64_t mem_req,
                        uint64_t data_size, uint32_t deadline_ms,
                        uint32_t priority) {
    if (!mgr || !name) return -1;
    if (mgr->num_workloads >= EDGE_MAX_WORKLOADS) return -1;

    /* Find best node */
    uint32_t target_node = 0;
    if (edge_find_best_node(mgr, cpu_req, mem_req, deadline_ms, &target_node) != 0) {
        printf("[EDGE] No suitable node found\n");
        return -1;
    }

    edge_workload_t* wl = &mgr->workloads[mgr->num_workloads];
    memset(wl, 0, sizeof(edge_workload_t));

    wl->id = mgr->num_workloads + 1;
    string_copy(wl->name, name, EDGE_MAX_NAME);
    wl->state = WORKLOAD_STATE_RUNNING;
    wl->source_node = 0;
    wl->target_node = target_node;
    wl->cpu_required = cpu_req;
    wl->memory_required = mem_req;
    wl->data_size = data_size;
    wl->deadline_ms = deadline_ms;
    wl->priority = priority;
    wl->start_time = 0;

    /* Update node */
    edge_node_t* node = find_node(mgr, target_node);
    if (node) {
        node->num_workloads++;
        node->total_processed++;
    }

    mgr->num_workloads++;
    mgr->total_workloads++;
    mgr->successful_workloads++;

    printf("[EDGE] Workload '%s' submitted to node %u\n", name, target_node);
    return (int)wl->id;
}

int edge_cancel_workload(edge_manager_t* mgr, uint32_t workload_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_workloads; i++) {
        if (mgr->workloads[i].id == workload_id) {
            mgr->workloads[i].state = WORKLOAD_STATE_FAILED;
            printf("[EDGE] Workload '%s' cancelled\n", mgr->workloads[i].name);
            return 0;
        }
    }
    return -1;
}

int edge_migrate_workload(edge_manager_t* mgr, uint32_t workload_id,
                         uint32_t target_node) {
    if (!mgr) return -1;

    edge_workload_t* wl = find_workload(mgr, workload_id);
    if (!wl) return -1;

    wl->state = WORKLOAD_STATE_MIGRATING;
    wl->target_node = target_node;
    wl->migrated = 1;
    wl->state = WORKLOAD_STATE_RUNNING;

    printf("[EDGE] Workload '%s' migrated to node %u\n", wl->name, target_node);
    return 0;
}

int edge_list_workloads(edge_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    const char* state_names[] = {"pending", "running", "completed", "failed", "migrating"};
    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos, "WORKLOADS: %u\n", mgr->num_workloads);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID  NAME            STATE       NODE  CPU   MEM     SIZE    DEADLINE\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_workloads && pos < buf_len - 150; i++) {
        edge_workload_t* w = &mgr->workloads[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-15s %-11s %-5u %-5u %-7llu %-7llu %u ms\n",
            w->id, w->name, state_names[w->state],
            w->target_node, w->cpu_required,
            (unsigned long long)(w->memory_required / (1024 * 1024)),
            (unsigned long long)(w->data_size / (1024 * 1024)),
            w->deadline_ms);
    }

    return (int)pos;
}

int edge_get_workload_info(edge_manager_t* mgr, uint32_t workload_id,
                          char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    edge_workload_t* wl = find_workload(mgr, workload_id);
    if (!wl) return -1;

    const char* state_names[] = {"pending", "running", "completed", "failed", "migrating"};
    return snprintf(buf, buf_len,
        "Workload: %s\n"
        "  State: %s\n"
        "  Target Node: %u\n"
        "  CPU Required: %u cores\n"
        "  Memory Required: %llu MB\n"
        "  Data Size: %llu MB\n"
        "  Deadline: %u ms\n"
        "  Priority: %u\n"
        "  Migrated: %s\n",
        wl->name, state_names[wl->state],
        wl->target_node, wl->cpu_required,
        (unsigned long long)(wl->memory_required / (1024 * 1024)),
        (unsigned long long)(wl->data_size / (1024 * 1024)),
        wl->deadline_ms, wl->priority,
        wl->migrated ? "yes" : "no");
}

/* ---- Policy management ---- */

int edge_add_policy(edge_manager_t* mgr, const char* name,
                   policy_type_t type, uint32_t weight,
                   const char* conditions) {
    if (!mgr || !name) return -1;
    if (mgr->num_policies >= EDGE_MAX_POLICIES) return -1;

    edge_policy_t* policy = &mgr->policies[mgr->num_policies];
    memset(policy, 0, sizeof(edge_policy_t));

    policy->id = mgr->num_policies + 1;
    string_copy(policy->name, name, EDGE_MAX_NAME);
    policy->type = type;
    policy->weight = weight;
    policy->enabled = 1;
    if (conditions) string_copy(policy->conditions, conditions, 256);

    mgr->num_policies++;
    printf("[EDGE] Policy '%s' added (type=%d, weight=%u)\n", name, type, weight);
    return (int)policy->id;
}

int edge_remove_policy(edge_manager_t* mgr, uint32_t policy_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_policies; i++) {
        if (mgr->policies[i].id == policy_id) {
            printf("[EDGE] Policy '%s' removed\n", mgr->policies[i].name);
            for (uint32_t j = i; j < mgr->num_policies - 1; j++)
                mgr->policies[j] = mgr->policies[j + 1];
            mgr->num_policies--;
            return 0;
        }
    }
    return -1;
}

int edge_list_policies(edge_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    const char* type_names[] = {"latency", "bandwidth", "cost", "energy", "security"};
    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos, "POLICIES: %u\n", mgr->num_policies);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID  NAME            TYPE        WEIGHT  ENABLED\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_policies && pos < buf_len - 100; i++) {
        edge_policy_t* p = &mgr->policies[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-15s %-11s %-7u %s\n",
            p->id, p->name, type_names[p->type],
            p->weight, p->enabled ? "yes" : "no");
    }

    return (int)pos;
}

/* ---- Edge-Cloud sync ---- */

int edge_sync_data(edge_manager_t* mgr, uint32_t node_id,
                  const char* path, int to_cloud) {
    if (!mgr || !path) return -1;

    edge_node_t* node = find_node(mgr, node_id);
    if (!node) return -1;

    printf("[EDGE] Syncing '%s' %s %s\n", path,
           to_cloud ? "to cloud from" : "from cloud to",
           node->name);
    return 0;
}

int edge_offload(edge_manager_t* mgr, uint32_t workload_id) {
    if (!mgr) return -1;

    edge_workload_t* wl = find_workload(mgr, workload_id);
    if (!wl) return -1;

    printf("[EDGE] Offloading workload '%s' to cloud\n", wl->name);
    return 0;
}

int edge_prefetch(edge_manager_t* mgr, uint32_t node_id, const char* data_key) {
    if (!mgr || !data_key) return -1;

    edge_node_t* node = find_node(mgr, node_id);
    if (!node) return -1;

    printf("[EDGE] Prefetching '%s' to node '%s'\n", data_key, node->name);
    return 0;
}

/* ---- Monitoring ---- */

int edge_get_stats(edge_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    return snprintf(buf, buf_len,
        "Edge Computing Statistics:\n"
        "  Nodes: %u total\n"
        "  Workloads: %u total, %u successful, %u failed\n"
        "  Success Rate: %.2f%%\n"
        "  Avg Latency: %u ms\n",
        mgr->num_nodes,
        mgr->total_workloads, mgr->successful_workloads, mgr->failed_workloads,
        mgr->total_workloads > 0 ?
            (float)mgr->successful_workloads / mgr->total_workloads * 100 : 0,
        mgr->avg_latency_ms);
}

int edge_get_cluster_health(edge_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    uint32_t online = 0, offline = 0, degraded = 0;
    for (uint32_t i = 0; i < mgr->num_nodes; i++) {
        switch (mgr->nodes[i].state) {
            case EDGE_STATE_ONLINE: online++; break;
            case EDGE_STATE_OFFLINE: offline++; break;
            case EDGE_STATE_DEGRADED: degraded++; break;
            default: break;
        }
    }

    const char* health = "healthy";
    if (offline > 0) health = "critical";
    else if (degraded > 0) health = "degraded";

    return snprintf(buf, buf_len,
        "Cluster Health: %s\n"
        "  Online: %u\n"
        "  Degraded: %u\n"
        "  Offline: %u\n",
        health, online, degraded, offline);
}

int edge_optimize_placement(edge_manager_t* mgr) {
    if (!mgr) return -1;

    printf("[EDGE] Optimizing workload placement...\n");

    /* Simple optimization: migrate workloads from overloaded nodes */
    for (uint32_t i = 0; i < mgr->num_workloads; i++) {
        edge_workload_t* wl = &mgr->workloads[i];
        if (wl->state != WORKLOAD_STATE_RUNNING) continue;

        edge_node_t* node = find_node(mgr, wl->target_node);
        if (node && node->cpu_usage > 80) {
            uint32_t new_node;
            if (edge_find_best_node(mgr, wl->cpu_required, wl->memory_required,
                                   wl->deadline_ms, &new_node) == 0) {
                edge_migrate_workload(mgr, wl->id, new_node);
            }
        }
    }

    printf("[EDGE] Optimization complete\n");
    return 0;
}
