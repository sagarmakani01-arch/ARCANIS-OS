#ifndef METAOS_H
#define METAOS_H

typedef struct {
    char id[32];
    char name[64];
    int module_number;
    char version[16];
    char exposed_functions[8][64];
    char imports[4][64];
    int state;
} ModuleInterface;

typedef struct {
    char id[32];
    char source_module[32];
    char target_module[32];
    char data_type[32];
    double throughput;
    double latency_ms;
    int active;
    char transform[64];
} DataFlow;

typedef struct {
    char path[64];
    char module[32];
    char function[64];
    int call_count;
} Endpoint;

typedef struct {
    Endpoint endpoints[16];
    int endpoint_count;
    int total_api_calls;
    double avg_response_ms;
} UnifiedAPI;

typedef struct {
    ModuleInterface modules[32];
    int module_count;
    DataFlow flows[16];
    int flow_count;
    UnifiedAPI api;
    int total_modules;
    double orchestration_level;
    int auto_discover;
    int cross_module_cache;
    double system_coherence;
    int module_dependencies[32][32];
} MetaOS;

void meta_init(MetaOS *os);
void meta_register_module(MetaOS *os, const char *name, int num, const char *version);
void meta_connect(MetaOS *os, const char *source, const char *target, const char *data_type);
void meta_discover_modules(MetaOS *os);
void meta_orchestrate_flow(MetaOS *os, const char *data_type);
void meta_api_call(MetaOS *os, const char *module, const char *function, const char *args);
void meta_show_modules(const MetaOS *os);
void meta_show_flows(const MetaOS *os);
void meta_show_api(const MetaOS *os);
void meta_show_system(const MetaOS *os);

#endif
