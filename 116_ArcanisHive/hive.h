#ifndef ARCANIS_HIVE_H
#define ARCANIS_HIVE_H

typedef struct {
    char id[32];
    char hostname[64];
    char ip_address[64];
    int port;
    int connected;
    double load_share;
    int capabilities;
    int trust_score;
} HiveNode;

typedef struct {
    char id[32];
    char type[64];
    char data[1024];
    int urgency;
    int ttl;
    double value;
} KnowledgeFragment;

typedef struct {
    char id[32];
    char name[64];
    double cpu_load;
    double mem_load;
    double network_load;
    double thermal_load;
    int active_tasks;
} WorkloadUnit;

typedef struct {
    char id[32];
    char type[64];
    char source_node[32];
    char threat_data[1024];
    int severity;
    int mitigated;
    int broadcast;
} CollectiveThreat;

typedef struct {
    HiveNode nodes[32];
    int node_count;
    KnowledgeFragment knowledge_base[256];
    int knowledge_count;
    CollectiveThreat threats[64];
    int threat_count;
    int total_ops;
    double collective_intelligence;
    int consensus_rounds;
    int self_organizing;
} HiveMind;

void hive_init(void);
HiveNode* hive_join(const char* hostname, const char* ip, int port);
void hive_leave(const char* node_id);
KnowledgeFragment* hive_share_knowledge(const char* type, const char* data, int urgency);
void hive_broadcast_threat(const char* type, const char* data, int severity);
WorkloadUnit* hive_assign_workload(WorkloadUnit* w);
int hive_reach_consensus(const char* topic, int vote_count);
void hive_sync_all(void);
void hive_show_nodes(void);
void hive_show_knowledge(void);
void hive_show_threats(void);
void hive_show_collective_stats(void);
double hive_calculate_intelligence(void);

#endif
