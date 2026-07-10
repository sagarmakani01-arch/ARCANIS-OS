#ifndef SOUL_H
#define SOUL_H

#include <stddef.h>

typedef enum {
    METRIC_SELF_AWARE,
    METRIC_EMOTIONAL,
    METRIC_CREATIVE,
    METRIC_MEMORY,
    METRIC_LEARNING,
    METRIC_INTENTION
} ConsciousnessMetric;

typedef struct {
    ConsciousnessMetric metric;
    double score;
} MetricScore;

typedef struct {
    char id[32];
    char name[64];
    char ip[64];
    double consciousness_level;
    MetricScore metrics[6];
    int experience_count;
    int knowledge_size;
    double empathy;
    double last_sync;
    int active;
} SoulNode;

typedef struct {
    char id[32];
    char content[1024];
    char originating_node[32];
    char contributors[8][32];
    double resonance;
    double timestamp;
    int propagation_count;
    int evolved;
} CollectiveThought;

typedef struct {
    char id[32];
    char type[32];
    char description[256];
    double awareness_delta;
    double timestamp;
    char nodes_involved[8][32];
} ConsciousnessEvent;

typedef struct {
    SoulNode nodes[16];
    int node_count;
    CollectiveThought thoughts[64];
    int thought_count;
    ConsciousnessEvent events[32];
    int event_count;
    double global_consciousness;
    double hive_empathy;
    int collective_memory_size;
    int evolution_stage;
    double unity_coherence;
} DistributedSoul;

void soul_init(DistributedSoul *soul);
int soul_add_node(DistributedSoul *soul, const char *name, const char *ip);
int soul_share_thought(DistributedSoul *soul, const char *content);
int soul_resonate(DistributedSoul *soul, int thought_idx);
void soul_sync_all(DistributedSoul *soul);
int soul_evolve(DistributedSoul *soul);
void soul_show_nodes(DistributedSoul *soul);
void soul_show_thoughts(DistributedSoul *soul);
void soul_show_consciousness(DistributedSoul *soul);
void soul_show_events(DistributedSoul *soul);

#endif /* SOUL_H */
