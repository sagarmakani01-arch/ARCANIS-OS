#ifndef PROBABILISTIC_H
#define PROBABILISTIC_H

#include <stddef.h>

typedef enum {
    DIST_NORMAL,
    DIST_UNIFORM,
    DIST_EXPONENTIAL,
    DIST_POISSON,
    DIST_BERNOULLI,
    DIST_CUSTOM
} ProbabilityDistribution;

typedef struct {
    char id[32];
    char name[64];
    ProbabilityDistribution distribution;
    double mean;
    double variance;
    double min_val;
    double max_val;
    double samples[128];
    int sample_count;
    double confidence_interval;
} ProbValue;

typedef struct {
    double prob;
    char result[128];
} ProbOutcome;

typedef struct {
    char id[32];
    char name[64];
    int inputs[8];
    ProbValue output;
    double execution_probability;
    ProbOutcome outcomes[8];
    int outcome_count;
    int observed;
} ProbProcess;

typedef struct {
    double amplitude;
    char value[128];
} SuperpositionState;

typedef struct {
    char id[32];
    SuperpositionState states[8];
    int state_count;
    int collapsed;
    char collapse_result[128];
    double interference_pattern;
} QuantumSuperposition;

typedef struct {
    ProbValue values[32];
    int value_count;
    ProbProcess processes[16];
    int process_count;
    QuantumSuperposition superpositions[8];
    int total_observations;
    double uncertainty_level;
    int deterministic_mode;
    int wave_function_collapse;
} ProbKernel;

void prob_init(ProbKernel *kernel);
int prob_create_value(ProbKernel *kernel, const char *name, ProbabilityDistribution dist, double mean, double var);
int prob_create_process(ProbKernel *kernel, const char *name, int *input_indices, int input_count);
int prob_execute(ProbKernel *kernel, int process_idx);
double prob_measure(ProbKernel *kernel, int value_idx);
int prob_collapse(ProbKernel *kernel, int super_idx);
int prob_entangle(ProbKernel *kernel, int a_idx, int b_idx);
void prob_show_values(ProbKernel *kernel);
void prob_show_processes(ProbKernel *kernel);
void prob_show_uncertainty(ProbKernel *kernel);

#endif /* PROBABILISTIC_H */
