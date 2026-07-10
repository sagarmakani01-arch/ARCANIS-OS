#include "unicompute.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static UniComputeFabric uf;

static const char* unit_type_str(ComputeUnitType t) {
    static const char* s[] = {"CPU","GPU","TPU","QPU","FPGA","NEUROMORPHIC","OPTICAL","BIOLOGICAL"};
    return t <= UNIT_BIOLOGICAL ? s[t] : "UNKNOWN";
}

void unicompute_init(void) {
    memset(&uf, 0, sizeof(uf));
    uf.scheduler_running = 1;
    uf.total_throughput = 0.0;
    uf.power_efficiency = 0.0;
    uf.migrations = 0;
    uf.auto_balance = 1;
    uf.quantum_classical_split = 0;
    uf.policy.type = UNIT_CPU;
    uf.policy.weight = 1.0;
    uf.policy.priority_bias = 0.5;
    uf.policy.max_tasks = 8;
    srand((unsigned)time(NULL));

    unicompute_add_unit("CPU-A", UNIT_CPU, 1.0, 16.0);
    unicompute_add_unit("GPU-A", UNIT_GPU, 12.0, 24.0);
    unicompute_add_unit("TPU-A", UNIT_TPU, 45.0, 32.0);
    unicompute_add_unit("QPU-A", UNIT_QPU, 0.1, 1.0);
    printf("[UNICOMPUTE] Fabric initialized with %d units\n", uf.unit_count);
}

ComputeUnit* unicompute_add_unit(const char* name, ComputeUnitType type, double flops, double mem) {
    if (uf.unit_count >= 16) return NULL;
    ComputeUnit* u = &uf.units[uf.unit_count++];
    u->id = uf.unit_count;
    u->type = type;
    snprintf(u->name, sizeof(u->name), "%s", name);
    u->flops = flops;
    u->memory_gb = mem;
    u->bandwidth_gbps = flops * 10.0;
    u->power_w = flops * 50.0 + 100.0;
    u->utilization = 0.0;
    u->online = 1;
    u->active_tasks = 0;
    printf("[UNICOMPUTE] Unit '%s' added (%s, %.1f TFLOPS, %.1f GB)\n",
           name, unit_type_str(type), flops, mem);
    return u;
}

ComputeTask* unicompute_submit_task(const char* name, double compute, double mem, ComputeUnitType pref) {
    if (uf.task_count >= 64) return NULL;
    ComputeTask* t = &uf.tasks[uf.task_count++];
    t->id = uf.task_count;
    snprintf(t->name, sizeof(t->name), "%s", name);
    t->compute_requirement = compute;
    t->memory_requirement = mem;
    t->latency_sensitivity = (rand() % 100) / 100.0;
    t->preferred_unit = pref;
    t->parallelizable = rand() % 2;
    t->assigned_unit = -1;
    t->progress = 0.0;
    t->completed = 0;
    printf("[UNICOMPUTE] Task '%s' submitted (compute=%.1f, mem=%.1f, pref=%s)\n",
           name, compute, mem, unit_type_str(pref));
    return t;
}

int unicompute_assign_task(ComputeTask* t) {
    if (!t) return -1;
    int best_idx = -1;
    double best_score = -1.0;

    for (int i = 0; i < uf.unit_count; i++) {
        if (!uf.units[i].online) continue;
        double score = uf.units[i].flops * uf.policy.weight +
                       uf.units[i].memory_gb * (1.0 - uf.policy.weight) +
                       (uf.units[i].type == t->preferred_unit ? 10.0 : 0.0);
        score *= (1.0 - uf.units[i].utilization);
        if (score > best_score) {
            best_score = score;
            best_idx = i;
            t->assigned_unit = uf.units[i].id;
        }
    }

    if (best_idx >= 0) {
        uf.units[best_idx].active_tasks++;
        uf.units[best_idx].utilization = (double)uf.units[best_idx].active_tasks / uf.policy.max_tasks;
        printf("[UNICOMPUTE] Task '%s' assigned to '%s' (score=%.2f)\n", t->name, uf.units[best_idx].name, best_score);
        return uf.units[best_idx].id;
    }
    printf("[UNICOMPUTE] No suitable unit for task '%s'\n", t->name);
    return -1;
}

int unicompute_execute_task(ComputeTask* t) {
    if (!t || t->assigned_unit < 0) return 0;
    t->progress = 1.0;
    t->completed = 1;
    printf("[UNICOMPUTE] Task '%s' completed on unit %d\n", t->name, t->assigned_unit);
    return 1;
}

void unicompute_migrate_task(ComputeTask* t, ComputeUnitType target) {
    if (!t) return;
    int old_unit = t->assigned_unit;
    t->preferred_unit = target;
    uf.migrations++;
    printf("[UNICOMPUTE] Task '%s' migrated from unit %d to %s\n", t->name, old_unit, unit_type_str(target));
    unicompute_assign_task(t);
}

void unicompute_balance_load(void) {
    int total_tasks = 0;
    for (int i = 0; i < uf.unit_count; i++) {
        total_tasks += uf.units[i].active_tasks;
    }
    int ideal = uf.unit_count > 0 ? total_tasks / uf.unit_count : 0;
    for (int i = 0; i < uf.unit_count; i++) {
        if (uf.units[i].active_tasks > ideal + 1) {
            uf.units[i].active_tasks--;
            uf.units[i].utilization = (double)uf.units[i].active_tasks / uf.policy.max_tasks;
        }
    }
    printf("[UNICOMPUTE] Load balanced: %d tasks across %d units\n", total_tasks, uf.unit_count);
}

double unicompute_calculate_throughput(void) {
    uf.total_throughput = 0.0;
    for (int i = 0; i < uf.unit_count; i++) {
        if (uf.units[i].online) {
            uf.total_throughput += uf.units[i].flops * uf.units[i].utilization;
        }
    }
    printf("[UNICOMPUTE] Total throughput: %.2f TFLOPS\n", uf.total_throughput);
    return uf.total_throughput;
}

double unicompute_calculate_efficiency(void) {
    double total_power = 0.0;
    for (int i = 0; i < uf.unit_count; i++) {
        if (uf.units[i].online) {
            total_power += uf.units[i].power_w * uf.units[i].utilization;
        }
    }
    uf.power_efficiency = total_power > 0.0 ? uf.total_throughput / total_power : 0.0;
    printf("[UNICOMPUTE] Power efficiency: %.4f TFLOPS/W\n", uf.power_efficiency);
    return uf.power_efficiency;
}

void unicompute_show_units(void) {
    printf("=== Compute Units ===\n");
    printf("%-4s %-16s %-10s %-10s %-10s %-8s %-8s %s\n", "ID", "Name", "Type", "TFLOPS", "Mem(GB)", "Util%", "Tasks", "Status");
    for (int i = 0; i < uf.unit_count; i++) {
        ComputeUnit* u = &uf.units[i];
        printf("%-4d %-16s %-10s %-10.1f %-10.1f %-8.1f %-8d %s\n",
               u->id, u->name, unit_type_str(u->type), u->flops, u->memory_gb,
               u->utilization * 100.0, u->active_tasks, u->online ? "ONLINE" : "OFFLINE");
    }
}

void unicompute_show_tasks(void) {
    printf("=== Compute Tasks ===\n");
    printf("%-4s %-20s %-10s %-10s %-8s %-8s %-10s %s\n", "ID", "Name", "Compute", "Mem", "Pref", "Unit", "Progress", "Status");
    for (int i = 0; i < uf.task_count; i++) {
        ComputeTask* t = &uf.tasks[i];
        printf("%-4d %-20s %-10.1f %-10.1f %-8s %-8d %-10.2f %s\n",
               t->id, t->name, t->compute_requirement, t->memory_requirement,
               unit_type_str(t->preferred_unit), t->assigned_unit,
               t->progress, t->completed ? "DONE" : "PENDING");
    }
}

void unicompute_show_fabric(void) {
    printf("=== UniCompute Fabric ===\n");
    printf("  Units: %d\n", uf.unit_count);
    printf("  Tasks: %d\n", uf.task_count);
    printf("  Total Throughput: %.2f TFLOPS\n", uf.total_throughput);
    printf("  Power Efficiency: %.4f TFLOPS/W\n", uf.power_efficiency);
    printf("  Migrations: %d\n", uf.migrations);
    printf("  Scheduler: %s\n", uf.scheduler_running ? "RUNNING" : "STOPPED");
    printf("  Auto-Balance: %s\n", uf.auto_balance ? "ON" : "OFF");
    printf("  Quantum Split: %d%%\n", uf.quantum_classical_split);
}

void unicompute_show_schedule(void) {
    printf("=== Schedule ===\n");
    printf("%-20s %-10s %-8s %-8s %-8s\n", "Unit", "Type", "Tasks", "Util%", "Status");
    for (int i = 0; i < uf.unit_count; i++) {
        ComputeUnit* u = &uf.units[i];
        printf("%-20s %-10s %-8d %-8.1f %s\n",
               u->name, unit_type_str(u->type), u->active_tasks,
               u->utilization * 100.0, u->online ? "READY" : "DOWN");
    }
    printf("Policy: %s weight=%.2f max_tasks=%d\n",
           unit_type_str(uf.policy.type), uf.policy.weight, uf.policy.max_tasks);
}
