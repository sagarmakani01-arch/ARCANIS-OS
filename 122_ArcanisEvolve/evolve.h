#ifndef ARCANIS_EVOLVE_H
#define ARCANIS_EVOLVE_H

typedef struct {
    int id;
    char code[8192];
    double fitness;
    int generation;
    int mutations;
    int parents[2];
    double novelty;
} Genome;

typedef struct {
    char metric[64];
    double target;
    double current;
    double weight;
} FitnessCriterion;

typedef struct {
    Genome individuals[64];
    int individual_count;
    int generation;
    double mutation_rate;
    double crossover_rate;
    double best_fitness;
    double avg_fitness;
    int elite_count;
    int stagnation_count;
} GeneticPool;

typedef struct {
    char name[64];
    char template_code[4096];
    char parameters[1024];
    int generated_count;
    int deployed_count;
    int rollback_count;
} AutoGenModule;

typedef struct {
    GeneticPool pool;
    AutoGenModule modules[16];
    int module_count;
    FitnessCriterion criteria[8];
    int criterion_count;
    int total_generations;
    int total_genomes;
    double evolution_speed;
    int self_modifying;
    int auto_deploy;
} EvolveEngine;

void evolve_init(void);
Genome* evolve_create_genome(const char* code);
void evolve_set_fitness(Genome* g, FitnessCriterion* criteria, int count);
GeneticPool* evolve_create_pool(int size, double mutation_rate, double crossover_rate);
void evolve_generation(GeneticPool* pool);
Genome* evolve_select_parent(GeneticPool* pool);
Genome* evolve_crossover(Genome* a, Genome* b);
void evolve_mutate(Genome* g);
AutoGenModule* evolve_create_module(const char* name, const char* template_code);
void evolve_generate_module(AutoGenModule* m, const char* params);
int evolve_deploy_module(AutoGenModule* m);
void evolve_show_population(void);
void evolve_show_generation_stats(void);
void evolve_show_modules(void);

#endif
