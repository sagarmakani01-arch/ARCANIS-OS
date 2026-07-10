/**
 * multicloud.h — Multi-Cloud Orchestration
 *
 * Multi-cloud provider abstraction, workload migration, cost optimization.
 */
#ifndef ARCANIS_MULTICLOUD_H
#define ARCANIS_MULTICLOUD_H

#include <arcanis/types.h>

#define MC_MAX_PROVIDERS     16
#define MC_MAX_RESOURCES     512
#define MC_MAX_WORKLOADS     256
#define MC_MAX_REGIONS       64
#define MC_MAX_NAME          64
#define MC_MAX_HOST          128

typedef enum {
    MC_PROVIDER_AWS,
    MC_PROVIDER_AZURE,
    MC_PROVIDER_GCP,
    MC_PROVIDER_OCI,
    MC_PROVIDER_DIGITALOCEAN,
    MC_PROVIDER_CUSTOM
} mc_provider_type_t;

typedef enum {
    MC_REGION_ACTIVE,
    MC_REGION_DEGRADED,
    MC_REGION_DOWN
} mc_region_state_t;

typedef struct {
    mc_provider_type_t provider;
    char name[32];
    mc_region_state_t state;
    double latency_ms;
    double cost_per_hour;
    uint64_t resources;
    int enabled;
} mc_region_t;

typedef enum {
    MC_RESOURCE_COMPUTE,
    MC_RESOURCE_STORAGE,
    MC_RESOURCE_DATABASE,
    MC_RESOURCE_NETWORK,
    MC_RESOURCE_ML
} mc_resource_type_t;

typedef struct {
    char resource_id[32];
    char name[MC_MAX_NAME];
    mc_resource_type_t type;
    mc_provider_type_t provider;
    char region[32];
    char instance_type[32];
    int running;
    double hourly_cost;
    double monthly_cost;
    uint64_t uptime_hours;
} mc_resource_t;

typedef enum {
    MC_WORKLOAD_RUNNING,
    MC_WORKLOAD_MIGRATING,
    MC_WORKLOAD_STOPPED,
    MC_WORKLOAD_FAILED
} mc_workload_state_t;

typedef struct {
    char workload_id[32];
    char name[MC_MAX_NAME];
    mc_workload_state_t state;
    mc_provider_type_t source_provider;
    mc_provider_type_t target_provider;
    char source_region[32];
    char target_region[32];
    double progress;
    double total_cost;
    uint64_t migrated_at;
} mc_workload_t;

typedef struct {
    mc_provider_type_t type;
    char name[32];
    char api_endpoint[128];
    char account_id[64];
    int connected;
    uint64_t total_spend;
    uint32_t resource_count;
    uint32_t region_count;
} mc_provider_t;

typedef struct {
    mc_provider_t providers[MC_MAX_PROVIDERS];
    uint32_t num_providers;

    mc_region_t regions[MC_MAX_REGIONS];
    uint32_t num_regions;

    mc_resource_t resources[MC_MAX_RESOURCES];
    uint32_t num_resources;

    mc_workload_t workloads[MC_MAX_WORKLOADS];
    uint32_t num_workloads;

    double total_monthly_cost;
    double total_yearly_cost;
    uint64_t total_migrations;
    int cost_optimization;
} mc_system_t;

void mc_init(mc_system_t* sys);

int  mc_add_provider(mc_system_t* sys, mc_provider_type_t type,
                     const char* name, const char* api_endpoint);
int  mc_connect_provider(mc_system_t* sys, mc_provider_type_t type);
int  mc_list_providers(mc_system_t* sys, char* buf, uint32_t buf_len);

int  mc_launch_resource(mc_system_t* sys, const char* name, mc_resource_type_t type,
                        mc_provider_type_t provider, const char* region);
int  mc_stop_resource(mc_system_t* sys, const char* resource_id);
int  mc_list_resources(mc_system_t* sys, char* buf, uint32_t buf_len);

int  mc_migrate_workload(mc_system_t* sys, const char* name, const char* resource_id,
                         mc_provider_type_t from_provider, mc_provider_type_t to_provider);
int  mc_get_migration_status(mc_system_t* sys, const char* workload_id,
                             char* buf, uint32_t buf_len);
int  mc_list_workloads(mc_system_t* sys, char* buf, uint32_t buf_len);

int  mc_optimize_costs(mc_system_t* sys);
int  mc_get_cost_report(mc_system_t* sys, char* buf, uint32_t buf_len);
int  mc_get_status(mc_system_t* sys, char* buf, uint32_t buf_len);

#endif
