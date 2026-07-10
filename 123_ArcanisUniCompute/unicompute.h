#ifndef ARCANIS_UNICOMPUTE_H
#define ARCANIS_UNICOMPUTE_H

typedef enum {
    UNIT_CPU,
    UNIT_GPU,
    UNIT_TPU,
    UNIT_QPU,
    UNIT_FPGA,
    UNIT_NEUROMORPHIC,
    UNIT_OPTICAL,
    UNIT_BIOLOGICAL
} ComputeUnitType;

typedef struct {
    int id;
    ComputeUnitType type;
    char name[64];
    double flops;
    double memory_gb;
    double bandwidth_gbps;
    double power_w;
    double utilization;
    int online;
    int active_tasks;
} ComputeUnit;

typedef struct {
    int id;
    char name[64];
    double compute_requirement;
    double memory_requirement;
    double latency_sensitivity;
    ComputeUnitType preferred_unit;
    int parallelizable;
    int assigned_unit;
    double progress;
    int completed;
} ComputeTask;

typedef struct {
    ComputeUnitType type;
    double weight;
    double priority_bias;
    int max_tasks;
} SchedulingPolicy;

typedef struct {
    ComputeUnit units[16];
    int unit_count;
    ComputeTask tasks[64];
    int task_count;
    SchedulingPolicy policy;
    int scheduler_running;
    double total_throughput;
    double power_efficiency;
    int migrations;
    int auto_balance;
    int quantum_classical_split;
} UniComputeFabric;

void unicompute_init(void);
ComputeUnit* unicompute_add_unit(const char* name, ComputeUnitType type, double flops, double mem);
ComputeTask* unicompute_submit_task(const char* name, double compute, double mem, ComputeUnitType pref);
int unicompute_assign_task(ComputeTask* t);
int unicompute_execute_task(ComputeTask* t);
void unicompute_migrate_task(ComputeTask* t, ComputeUnitType target);
void unicompute_balance_load(void);
double unicompute_calculate_throughput(void);
double unicompute_calculate_efficiency(void);
void unicompute_show_units(void);
void unicompute_show_tasks(void);
void unicompute_show_fabric(void);
void unicompute_show_schedule(void);

#endif
