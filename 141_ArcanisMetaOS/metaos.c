#include "metaos.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
    char name[32];
    char version[16];
    int active;
} ModuleInterface;

typedef struct {
    int flow_id;
    char from_module[32];
    char to_module[32];
    char data_type[32];
    float bandwidth;
} DataFlow;

typedef struct {
    int endpoint_id;
    char path[64];
    int call_count;
    char method[8];
} APIEndpoint;

typedef struct {
    ModuleInterface modules[16];
    int module_count;
    DataFlow flows[16];
    int flow_count;
    APIEndpoint endpoints[16];
    int endpoint_count;
    int phases_completed;
} MetaOS;

static MetaOS mos;

void meta_init(void) {
    mos.module_count = 0;
    mos.flow_count = 0;
    mos.endpoint_count = 0;
    mos.phases_completed = 0;
    srand((unsigned)time(NULL));

    const char *default_modules[] = {
        "kernel", "fs", "net", "ai", "quantum", "blockchain"
    };
    for (int i = 0; i < 6; i++) {
        ModuleInterface *m = &mos.modules[mos.module_count++];
        snprintf(m->name, sizeof(m->name), "%s", default_modules[i]);
        snprintf(m->version, sizeof(m->version), "1.%d", i);
        m->active = 1;
    }
    mos.phases_completed = 6;
}

void meta_register_module(const char *name, const char *version) {
    if (mos.module_count >= 16) return;
    ModuleInterface *m = &mos.modules[mos.module_count++];
    snprintf(m->name, sizeof(m->name), "%s", name);
    snprintf(m->version, sizeof(m->version), "%s", version);
    m->active = 1;
    printf("Registered module: %s v%s\n", name, version);
}

void meta_connect(const char *from, const char *to, const char *data_type) {
    if (mos.flow_count >= 16) return;
    DataFlow *f = &mos.flows[mos.flow_count++];
    f->flow_id = mos.flow_count;
    snprintf(f->from_module, sizeof(f->from_module), "%s", from);
    snprintf(f->to_module, sizeof(f->to_module), "%s", to);
    snprintf(f->data_type, sizeof(f->data_type), "%s", data_type);
    f->bandwidth = ((float)rand() / RAND_MAX) * 100.0f;
    printf("Flow #%d: %s -> %s (%s, bw=%.1f)\n",
           f->flow_id, from, to, data_type, f->bandwidth);
}

void meta_discover_modules(void) {
    const char *new_modules[] = {
        "security", "storage", "analytics", "orchestrator"
    };
    int added = 0;
    for (int i = 0; i < 4 && mos.module_count < 16; i++) {
        int found = 0;
        for (int j = 0; j < mos.module_count; j++) {
            if (strcmp(mos.modules[j].name, new_modules[i]) == 0) { found = 1; break; }
        }
        if (!found) {
            ModuleInterface *m = &mos.modules[mos.module_count++];
            snprintf(m->name, sizeof(m->name), "%s", new_modules[i]);
            snprintf(m->version, sizeof(m->version), "1.0");
            m->active = 1;
            printf("Discovered module: %s\n", new_modules[i]);
            added++;
        }
    }
    if (added == 0) printf("No new modules to discover\n");
}

void meta_orchestrate_flow(const char *data_type) {
    if (mos.module_count < 2) return;
    meta_connect(mos.modules[0].name, mos.modules[1].name, data_type);
    printf("Orchestrated flow for %s\n", data_type);
}

void meta_api_call(const char *path, const char *method) {
    if (mos.endpoint_count >= 16) return;
    APIEndpoint *e = &mos.endpoints[mos.endpoint_count++];
    e->endpoint_id = mos.endpoint_count;
    snprintf(e->path, sizeof(e->path), "%s", path);
    snprintf(e->method, sizeof(e->method), "%s", method);
    e->call_count = 1;
    printf("API %s %s (call #%d)\n", method, path, e->call_count);
}

void meta_show_modules(void) {
    printf("\n%-16s %-10s %s\n", "Module", "Version", "Active");
    printf("--------------------------------\n");
    for (int i = 0; i < mos.module_count; i++) {
        printf("%-16s %-10s %s\n",
               mos.modules[i].name, mos.modules[i].version,
               mos.modules[i].active ? "yes" : "no");
    }
}

void meta_show_flows(void) {
    printf("\n%-4s %-16s %-16s %-16s %s\n",
           "ID", "From", "To", "DataType", "BW");
    printf("----------------------------------------------------------\n");
    for (int i = 0; i < mos.flow_count; i++) {
        printf("%-4d %-16s %-16s %-16s %.1f\n",
               mos.flows[i].flow_id,
               mos.flows[i].from_module, mos.flows[i].to_module,
               mos.flows[i].data_type, mos.flows[i].bandwidth);
    }
}

void meta_show_api(void) {
    printf("\n%-4s %-30s %-8s %s\n", "ID", "Path", "Method", "Calls");
    printf("------------------------------------------------\n");
    for (int i = 0; i < mos.endpoint_count; i++) {
        printf("%-4d %-30s %-8s %d\n",
               mos.endpoints[i].endpoint_id,
               mos.endpoints[i].path,
               mos.endpoints[i].method,
               mos.endpoints[i].call_count);
    }
}

void meta_show_system(void) {
    printf("\n=== MetaOS System ===\n");
    printf("%-20s %d\n", "Modules", mos.module_count);
    printf("%-20s %d\n", "Data Flows", mos.flow_count);
    printf("%-20s %d\n", "Endpoints", mos.endpoint_count);
    printf("%-20s %d\n", "Phases", mos.phases_completed);
}
