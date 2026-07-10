#include "probabilistic.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#define MAX_VALUES 20
#define MAX_PROCESSES 10
#define MAX_STATES 10

typedef struct {
    int id;
    char label[32];
    double probability;
    double value;
} ProbState;

typedef struct {
    char id[32];
    char name[48];
    char distribution[32];
    ProbState states[MAX_STATES];
    int state_count;
    int sample_count;
    int collapsed;
    double mean;
    double variance;
} ProbValue;

typedef struct {
    char id[32];
    char name[48];
    char inputs[128];
    double execution_probability;
    int observed;
    int collapsed;
    double result;
} ProbProcess;

typedef struct {
    ProbValue values[MAX_VALUES];
    int value_count;
    ProbProcess processes[MAX_PROCESSES];
    int process_count;
    int deterministic_mode;
    double global_uncertainty;
} ProbKernel;

static ProbKernel pk;

void prob_init(void) {
    srand(time(NULL));
    memset(&pk, 0, sizeof(pk));
    pk.deterministic_mode = 0;
    pk.global_uncertainty = 0.5;
    printf("[PROB] Kernel initialized, deterministic: %s\n", pk.deterministic_mode ? "yes" : "no");
}

void prob_create_value(const char *name, const char *distribution, int samples) {
    if (pk.value_count >= MAX_VALUES) { printf("[PROB] Value limit reached\n"); return; }
    ProbValue *v = &pk.values[pk.value_count++];
    snprintf(v->id, sizeof(v->id), "VAL-%03d", pk.value_count);
    strncpy(v->name, name, sizeof(v->name) - 1);
    strncpy(v->distribution, distribution, sizeof(v->distribution) - 1);
    v->sample_count = samples;
    v->collapsed = 0;
    v->state_count = 3;
    for (int i = 0; i < v->state_count; i++) {
        v->states[i].id = i;
        snprintf(v->states[i].label, sizeof(v->states[i].label), "state_%d", i);
        v->states[i].probability = (rand() % 1000) / 1000.0;
        v->states[i].value = (rand() % 1000) / 10.0;
    }
    double sum = 0;
    for (int i = 0; i < v->state_count; i++) sum += v->states[i].probability;
    for (int i = 0; i < v->state_count; i++) v->states[i].probability /= sum;
    v->mean = 0;
    for (int i = 0; i < v->state_count; i++) v->mean += v->states[i].value * v->states[i].probability;
    v->variance = 0;
    for (int i = 0; i < v->state_count; i++)
        v->variance += v->states[i].probability * (v->states[i].value - v->mean) * (v->states[i].value - v->mean);
    printf("[PROB] Created value '%s' (%s) dist=%s, samples=%d, mean=%.2f\n",
           v->name, v->id, distribution, samples, v->mean);
}

void prob_create_process(const char *name, const char *inputs) {
    if (pk.process_count >= MAX_PROCESSES) { printf("[PROB] Process limit reached\n"); return; }
    ProbProcess *p = &pk.processes[pk.process_count++];
    snprintf(p->id, sizeof(p->id), "PROC-%03d", pk.process_count);
    strncpy(p->name, name, sizeof(p->name) - 1);
    strncpy(p->inputs, inputs, sizeof(p->inputs) - 1);
    p->execution_probability = 0.5;
    p->observed = 0;
    p->collapsed = 0;
    p->result = 0.0;
    printf("[PROB] Created process '%s' (%s) with inputs: %s\n", p->name, p->id, inputs);
}

void prob_execute(const char *process_id) {
    for (int i = 0; i < pk.process_count; i++) {
        if (strcmp(pk.processes[i].id, process_id) == 0) {
            pk.processes[i].execution_probability = (rand() % 1000) / 1000.0;
            pk.processes[i].observed = 1;
            printf("[PROB] Executed process %s with probability %.3f\n", process_id, pk.processes[i].execution_probability);
            return;
        }
    }
    printf("[PROB] Process %s not found\n", process_id);
}

double prob_measure(const char *value_id) {
    for (int i = 0; i < pk.value_count; i++) {
        if (strcmp(pk.values[i].id, value_id) == 0) {
            printf("[PROB] Measured %s: mean=%.2f, variance=%.2f\n",
                   value_id, pk.values[i].mean, pk.values[i].variance);
            return pk.values[i].mean;
        }
    }
    printf("[PROB] Value %s not found\n", value_id);
    return 0.0;
}

void prob_collapse(const char *process_id) {
    for (int i = 0; i < pk.process_count; i++) {
        if (strcmp(pk.processes[i].id, process_id) == 0) {
            pk.processes[i].collapsed = 1;
            if (pk.value_count > 0)
                pk.processes[i].result = pk.values[0].states[0].value;
            printf("[PROB] Collapsed process %s -> result=%.2f\n", process_id, pk.processes[i].result);
            return;
        }
    }
    printf("[PROB] Process %s not found\n", process_id);
}

void prob_show_values(void) {
    printf("\n=== PROBABILISTIC VALUES ===\n");
    printf("%-10s %-20s %-15s %-10s %-10s %-12s\n", "ID", "Name", "Distribution", "Samples", "Collapsed", "Mean");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < pk.value_count; i++)
        printf("%-10s %-20s %-15s %-10d %-10s %-12.2f\n",
               pk.values[i].id, pk.values[i].name, pk.values[i].distribution,
               pk.values[i].sample_count,
               pk.values[i].collapsed ? "yes" : "no", pk.values[i].mean);
}

void prob_show_processes(void) {
    printf("\n=== PROBABILISTIC PROCESSES ===\n");
    printf("%-10s %-20s %-20s %-12s %-10s %-10s\n", "ID", "Name", "Inputs", "Exec Prob", "Observed", "Collapsed");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < pk.process_count; i++)
        printf("%-10s %-20s %-20s %-12.3f %-10s %-10s\n",
               pk.processes[i].id, pk.processes[i].name, pk.processes[i].inputs,
               pk.processes[i].execution_probability,
               pk.processes[i].observed ? "yes" : "no",
               pk.processes[i].collapsed ? "yes" : "no");
}

void prob_show_uncertainty(void) {
    printf("\n=== UNCERTAINTY REPORT ===\n");
    printf("Deterministic mode: %s\n", pk.deterministic_mode ? "yes" : "no");
    printf("Global uncertainty: %.3f\n", pk.global_uncertainty);
    printf("Number of values: %d\n", pk.value_count);
    printf("Number of processes: %d\n", pk.process_count);
    double total_var = 0;
    for (int i = 0; i < pk.value_count; i++) total_var += pk.values[i].variance;
    printf("Total variance across values: %.3f\n", total_var);
}
