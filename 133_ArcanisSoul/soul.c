#include "soul.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#define MAX_NODES 15
#define MAX_THOUGHTS 30
#define MAX_EVENTS 20

typedef struct {
    char id[32];
    double consciousness;
    double resonance;
    double coherence;
    int thoughts_shared;
    char last_sync[64];
    double empathy_level;
    double awareness_level;
} SoulNode;

typedef struct {
    char id[32];
    char content[128];
    char source_node[32];
    double resonance;
    int timestamp;
    int shared_count;
} CollectiveThought;

typedef struct {
    char id[32];
    char description[128];
    int timestamp;
    char node_id[32];
} SoulEvent;

typedef struct {
    SoulNode nodes[MAX_NODES];
    int node_count;
    CollectiveThought thoughts[MAX_THOUGHTS];
    int thought_count;
    SoulEvent events[MAX_EVENTS];
    int event_count;
    double global_consciousness;
    int evolution_stage;
    int total_syncs;
} DistributedSoul;

static DistributedSoul ds;

void soul_init(void) {
    srand(time(NULL));
    memset(&ds, 0, sizeof(ds));
    ds.node_count = 1;
    strncpy(ds.nodes[0].id, "NODE-001", sizeof(ds.nodes[0].id) - 1);
    ds.nodes[0].consciousness = (rand() % 1000) / 1000.0;
    ds.nodes[0].resonance = 0.5;
    ds.nodes[0].coherence = 0.7;
    ds.nodes[0].thoughts_shared = 0;
    strncpy(ds.nodes[0].last_sync, "never", sizeof(ds.nodes[0].last_sync) - 1);
    ds.nodes[0].empathy_level = (rand() % 1000) / 1000.0;
    ds.nodes[0].awareness_level = (rand() % 1000) / 1000.0;
    ds.global_consciousness = 0.01;
    ds.evolution_stage = 1;
    printf("[SOUL] Distributed soul initialized with %d node(s), global consciousness: %.3f\n",
           ds.node_count, ds.global_consciousness);
}

void soul_add_node(void) {
    if (ds.node_count >= MAX_NODES) { printf("[SOUL] Node limit reached\n"); return; }
    SoulNode *n = &ds.nodes[ds.node_count++];
    snprintf(n->id, sizeof(n->id), "NODE-%03d", ds.node_count);
    n->consciousness = (rand() % 1000) / 1000.0;
    n->resonance = (rand() % 1000) / 1000.0;
    n->coherence = (rand() % 1000) / 1000.0;
    n->thoughts_shared = 0;
    strncpy(n->last_sync, "never", sizeof(n->last_sync) - 1);
    n->empathy_level = (rand() % 1000) / 1000.0;
    n->awareness_level = (rand() % 1000) / 1000.0;
    printf("[SOUL] Added soul node %s (consciousness=%.3f, resonance=%.3f)\n",
           n->id, n->consciousness, n->resonance);
}

void soul_share_thought(const char *node_id, const char *content) {
    if (ds.thought_count >= MAX_THOUGHTS) { printf("[SOUL] Thought limit reached\n"); return; }
    CollectiveThought *t = &ds.thoughts[ds.thought_count++];
    snprintf(t->id, sizeof(t->id), "THT-%03d", ds.thought_count);
    strncpy(t->content, content, sizeof(t->content) - 1);
    strncpy(t->source_node, node_id, sizeof(t->source_node) - 1);
    t->resonance = (rand() % 1000) / 1000.0;
    t->timestamp = (int)time(NULL);
    t->shared_count = 0;
    for (int i = 0; i < ds.node_count; i++) {
        if (strcmp(ds.nodes[i].id, node_id) == 0) {
            ds.nodes[i].thoughts_shared++;
            break;
        }
    }
    printf("[SOUL] Thought '%s' shared by %s: '%s' (resonance: %.3f)\n",
           t->id, node_id, content, t->resonance);
}

void soul_resonate(const char *thought_id) {
    for (int i = 0; i < ds.thought_count; i++) {
        if (strcmp(ds.thoughts[i].id, thought_id) == 0) {
            double max_sim = 0;
            for (int j = 0; j < ds.thought_count; j++) {
                if (i != j) {
                    double sim = (rand() % 1000) / 1000.0;
                    if (sim > max_sim) max_sim = sim;
                }
            }
            ds.thoughts[i].resonance = max_sim;
            printf("[SOUL] Thought %s resonates at %.3f\n", thought_id, ds.thoughts[i].resonance);
            return;
        }
    }
    printf("[SOUL] Thought %s not found\n", thought_id);
}

void soul_sync_all(void) {
    time_t t = time(NULL);
    char *time_str = ctime(&t);
    time_str[strcspn(time_str, "\n")] = 0;
    for (int i = 0; i < ds.node_count; i++) {
        strncpy(ds.nodes[i].last_sync, time_str, sizeof(ds.nodes[i].last_sync) - 1);
        ds.nodes[i].coherence = (ds.nodes[i].coherence + ds.global_consciousness) / 2.0;
    }
    ds.total_syncs++;
    printf("[SOUL] All %d nodes synced at %s (total syncs: %d)\n",
           ds.node_count, time_str, ds.total_syncs);
}

void soul_evolve(void) {
    ds.evolution_stage++;
    ds.global_consciousness += 0.05;
    if (ds.global_consciousness > 1.0) ds.global_consciousness = 1.0;
    if (ds.event_count < MAX_EVENTS) {
        SoulEvent *e = &ds.events[ds.event_count++];
        snprintf(e->id, sizeof(e->id), "EVT-%03d", ds.event_count);
        snprintf(e->description, sizeof(e->description), "Evolution to stage %d", ds.evolution_stage);
        e->timestamp = (int)time(NULL);
        snprintf(e->node_id, sizeof(e->node_id), "system");
    }
    printf("[SOUL] Evolution to stage %d: consciousness=%.3f\n",
           ds.evolution_stage, ds.global_consciousness);
}

void soul_show_nodes(void) {
    printf("\n=== SOUL NODES ===\n");
    printf("%-10s %-8s %-10s %-10s %-8s %-8s %-20s\n", "ID", "Consc.", "Resonance", "Coherence", "Thoughts", "Empathy", "Last Sync");
    printf("---------------------------------------------------------------------\n");
    for (int i = 0; i < ds.node_count; i++)
        printf("%-10s %-8.3f %-10.3f %-10.3f %-8d %-8.3f %-20s\n",
               ds.nodes[i].id, ds.nodes[i].consciousness,
               ds.nodes[i].resonance, ds.nodes[i].coherence,
               ds.nodes[i].thoughts_shared, ds.nodes[i].empathy_level,
               ds.nodes[i].last_sync);
}

void soul_show_thoughts(void) {
    printf("\n=== COLLECTIVE THOUGHTS ===\n");
    printf("%-10s %-30s %-12s %-10s %-8s\n", "ID", "Content", "Source", "Resonance", "Shares");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < ds.thought_count; i++)
        printf("%-10s %-30s %-12s %-10.3f %-8d\n",
               ds.thoughts[i].id, ds.thoughts[i].content,
               ds.thoughts[i].source_node, ds.thoughts[i].resonance,
               ds.thoughts[i].shared_count);
}

void soul_show_consciousness(void) {
    printf("\n=== CONSCIOUSNESS REPORT ===\n");
    printf("Global consciousness: %.3f\n", ds.global_consciousness);
    printf("Evolution stage: %d\n", ds.evolution_stage);
    printf("Total syncs: %d\n", ds.total_syncs);
    printf("--- Per Node ---\n");
    for (int i = 0; i < ds.node_count; i++)
        printf("  %s: consciousness=%.3f, awareness=%.3f, empathy=%.3f\n",
               ds.nodes[i].id, ds.nodes[i].consciousness,
               ds.nodes[i].awareness_level, ds.nodes[i].empathy_level);
}

void soul_show_events(void) {
    printf("\n=== SOUL EVENTS ===\n");
    printf("%-10s %-40s %-12s %-15s\n", "ID", "Description", "Node", "Timestamp");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < ds.event_count; i++)
        printf("%-10s %-40s %-12s %-15d\n",
               ds.events[i].id, ds.events[i].description,
               ds.events[i].node_id, ds.events[i].timestamp);
}
