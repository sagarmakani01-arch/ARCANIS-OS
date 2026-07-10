#include "hive.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static HiveMind hive;

void hive_init(void) {
    memset(&hive, 0, sizeof(hive));
    hive.collective_intelligence = 1.0;
    hive.self_organizing = 1;
    srand((unsigned)time(NULL));

    hive_join("master-node", "192.168.1.1", 9000);
    hive_join("worker-1", "192.168.1.2", 9001);
    hive_join("worker-2", "192.168.1.3", 9002);
    printf("[HIVE] Hive initialized with %d nodes\n", hive.node_count);
}

HiveNode* hive_join(const char* hostname, const char* ip, int port) {
    if (hive.node_count >= 32) return NULL;
    HiveNode* n = &hive.nodes[hive.node_count++];
    snprintf(n->id, sizeof(n->id), "NODE-%d", hive.node_count);
    snprintf(n->hostname, sizeof(n->hostname), "%s", hostname);
    snprintf(n->ip_address, sizeof(n->ip_address), "%s", ip);
    n->port = port;
    n->connected = 1;
    n->load_share = 0.0;
    n->capabilities = rand() % 256;
    n->trust_score = 100;
    printf("[HIVE] Node '%s' joined (id=%s)\n", hostname, n->id);
    return n;
}

void hive_leave(const char* node_id) {
    for (int i = 0; i < hive.node_count; i++) {
        if (strcmp(hive.nodes[i].id, node_id) == 0) {
            hive.nodes[i].connected = 0;
            printf("[HIVE] Node '%s' left the hive\n", node_id);
            return;
        }
    }
}

KnowledgeFragment* hive_share_knowledge(const char* type, const char* data, int urgency) {
    if (hive.knowledge_count >= 256) return NULL;
    KnowledgeFragment* kf = &hive.knowledge_base[hive.knowledge_count++];
    snprintf(kf->id, sizeof(kf->id), "KF-%d", hive.knowledge_count);
    snprintf(kf->type, sizeof(kf->type), "%s", type);
    snprintf(kf->data, sizeof(kf->data), "%s", data);
    kf->urgency = urgency;
    kf->ttl = rand() % 100 + 50;
    kf->value = (rand() % 1000) / 10.0;
    hive.total_ops++;
    printf("[HIVE] Knowledge shared: [%s] %s (urgency=%d)\n", type, data, urgency);
    return kf;
}

void hive_broadcast_threat(const char* type, const char* data, int severity) {
    if (hive.threat_count >= 64) return;
    CollectiveThreat* t = &hive.threats[hive.threat_count++];
    snprintf(t->id, sizeof(t->id), "THREAT-%d", hive.threat_count);
    snprintf(t->type, sizeof(t->type), "%s", type);
    snprintf(t->source_node, sizeof(t->source_node), "NODE-%d", rand() % hive.node_count + 1);
    snprintf(t->threat_data, sizeof(t->threat_data), "%s", data);
    t->severity = severity;
    t->mitigated = 0;
    t->broadcast = 1;
    printf("[HIVE] Threat broadcast: [%s] severity=%d\n", type, severity);
}

WorkloadUnit* hive_assign_workload(WorkloadUnit* w) {
    if (!w) return NULL;
    w->cpu_load = (rand() % 100) / 100.0;
    w->mem_load = (rand() % 100) / 100.0;
    w->network_load = (rand() % 100) / 100.0;
    w->thermal_load = (rand() % 100) / 100.0;
    w->active_tasks = rand() % 10 + 1;
    hive.total_ops++;
    printf("[HIVE] Workload assigned to '%s': cpu=%.2f mem=%.2f net=%.2f\n",
           w->name, w->cpu_load, w->mem_load, w->network_load);
    return w;
}

int hive_reach_consensus(const char* topic, int vote_count) {
    hive.consensus_rounds++;
    int result = (vote_count > 2) ? 1 : 0;
    printf("[HIVE] Consensus round %d on '%s': votes=%d -> %s\n",
           hive.consensus_rounds, topic, vote_count, result ? "REACHED" : "FAILED");
    return result;
}

void hive_sync_all(void) {
    int connected = 0;
    for (int i = 0; i < hive.node_count; i++) {
        if (hive.nodes[i].connected) connected++;
    }
    printf("[HIVE] Syncing %d/%d nodes | knowledge=%d threats=%d ops=%d\n",
           connected, hive.node_count, hive.knowledge_count, hive.threat_count, hive.total_ops);
}

void hive_show_nodes(void) {
    printf("=== Hive Nodes ===\n");
    printf("%-8s %-16s %-16s %-6s %-8s %s\n", "ID", "Hostname", "IP", "Port", "Trust", "Status");
    for (int i = 0; i < hive.node_count; i++) {
        HiveNode* n = &hive.nodes[i];
        printf("%-8s %-16s %-16s %-6d %-8d %s\n", n->id, n->hostname, n->ip_address,
               n->port, n->trust_score, n->connected ? "ONLINE" : "OFFLINE");
    }
}

void hive_show_knowledge(void) {
    printf("=== Knowledge Base ===\n");
    printf("%-8s %-16s %-8s %-8s %s\n", "ID", "Type", "Urgency", "Value", "Data");
    for (int i = 0; i < hive.knowledge_count; i++) {
        KnowledgeFragment* k = &hive.knowledge_base[i];
        printf("%-8s %-16s %-8d %-8.1f %s\n", k->id, k->type, k->urgency, k->value, k->data);
    }
}

void hive_show_threats(void) {
    printf("=== Collective Threats ===\n");
    printf("%-10s %-16s %-8s %-10s %s\n", "ID", "Type", "Severity", "Broadcast", "Status");
    for (int i = 0; i < hive.threat_count; i++) {
        CollectiveThreat* t = &hive.threats[i];
        printf("%-10s %-16s %-8d %-10s %s\n", t->id, t->type, t->severity,
               t->broadcast ? "YES" : "NO", t->mitigated ? "MITIGATED" : "ACTIVE");
    }
}

void hive_show_collective_stats(void) {
    printf("=== Collective Stats ===\n");
    printf("  Nodes: %d\n", hive.node_count);
    printf("  Knowledge Fragments: %d\n", hive.knowledge_count);
    printf("  Threats: %d\n", hive.threat_count);
    printf("  Total Ops: %d\n", hive.total_ops);
    printf("  Consensus Rounds: %d\n", hive.consensus_rounds);
    printf("  Collective Intelligence: %.2f\n", hive.collective_intelligence);
    printf("  Self-Organizing: %s\n", hive.self_organizing ? "YES" : "NO");
}

double hive_calculate_intelligence(void) {
    hive.collective_intelligence = hive.node_count * (hive.knowledge_count + 1) * 0.5;
    printf("[HIVE] Collective intelligence calculated: %.2f\n", hive.collective_intelligence);
    return hive.collective_intelligence;
}
