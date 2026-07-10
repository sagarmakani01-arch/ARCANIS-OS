#include "evolve.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static EvolveEngine ee;

void evolve_init(void) {
    memset(&ee, 0, sizeof(ee));
    ee.evolution_speed = 1.0;
    ee.self_modifying = 1;
    ee.auto_deploy = 1;
    ee.total_generations = 0;
    ee.total_genomes = 0;
    srand((unsigned)time(NULL));

    evolve_create_genome("print(\"Hello, World!\")");
    evolve_create_genome("def init(): return 42");
    evolve_create_genome("class Agent: pass");
    evolve_create_genome("function compute() {}");
    printf("[EVOLVE] Engine initialized with %d genomes\n", ee.pool.individual_count);
}

Genome* evolve_create_genome(const char* code) {
    if (ee.pool.individual_count >= 64) return NULL;
    Genome* g = &ee.pool.individuals[ee.pool.individual_count++];
    g->id = ee.pool.individual_count;
    snprintf(g->code, sizeof(g->code), "%s", code);
    g->fitness = (rand() % 10000) / 100.0;
    g->generation = 0;
    g->mutations = 0;
    g->parents[0] = -1;
    g->parents[1] = -1;
    g->novelty = (rand() % 1000) / 1000.0;
    ee.total_genomes++;
    printf("[EVOLVE] Genome %d created: '%s' (fitness=%.2f)\n", g->id, code, g->fitness);
    return g;
}

void evolve_set_fitness(Genome* g, FitnessCriterion* criteria, int count) {
    if (!g || !criteria) return;
    double weighted = 0.0;
    for (int i = 0; i < count && i < 8; i++) {
        weighted += criteria[i].weight * (1.0 - fabs(criteria[i].target - criteria[i].current) / (criteria[i].target + 0.001));
    }
    g->fitness = weighted * 100.0;
    printf("[EVOLVE] Fitness set for genome %d: %.2f\n", g->id, g->fitness);
}

GeneticPool* evolve_create_pool(int size, double mutation_rate, double crossover_rate) {
    memset(&ee.pool, 0, sizeof(ee.pool));
    ee.pool.individual_count = 0;
    ee.pool.mutation_rate = mutation_rate;
    ee.pool.crossover_rate = crossover_rate;
    ee.pool.best_fitness = 0.0;
    ee.pool.avg_fitness = 0.0;
    ee.pool.elite_count = 2;
    ee.pool.stagnation_count = 0;

    for (int i = 0; i < size && i < 64; i++) {
        char code[32];
        snprintf(code, sizeof(code), "genome_%d", i + 1);
        evolve_create_genome(code);
    }
    ee.pool.generation = 0;
    printf("[EVOLVE] Pool created: %d individuals, mut=%.2f, cross=%.2f\n",
           size, mutation_rate, crossover_rate);
    return &ee.pool;
}

void evolve_generation(GeneticPool* pool) {
    if (!pool) return;
    pool->generation++;
    ee.total_generations++;

    double total = 0.0;
    pool->best_fitness = 0.0;
    for (int i = 0; i < pool->individual_count; i++) {
        total += pool->individuals[i].fitness;
        if (pool->individuals[i].fitness > pool->best_fitness)
            pool->best_fitness = pool->individuals[i].fitness;
    }
    pool->avg_fitness = pool->individual_count > 0 ? total / pool->individual_count : 0.0;

    int new_count = pool->individual_count;
    for (int i = 0; i < 4 && new_count < 64; i++) {
        Genome* p1 = evolve_select_parent(pool);
        Genome* p2 = evolve_select_parent(pool);
        if (p1 && p2) {
            Genome* child = evolve_crossover(p1, p2);
            if (child) {
                evolve_mutate(child);
                pool->individuals[new_count++] = *child;
            }
        }
    }
    pool->individual_count = new_count;

    printf("[EVOLVE] Generation %d: best=%.2f avg=%.2f pop=%d\n",
           pool->generation, pool->best_fitness, pool->avg_fitness, pool->individual_count);
}

Genome* evolve_select_parent(GeneticPool* pool) {
    if (!pool || pool->individual_count == 0) return NULL;
    int a = rand() % pool->individual_count;
    int b = rand() % pool->individual_count;
    return pool->individuals[a].fitness > pool->individuals[b].fitness ?
           &pool->individuals[a] : &pool->individuals[b];
}

Genome* evolve_crossover(Genome* a, Genome* b) {
    if (!a || !b) return NULL;
    static Genome child;
    memset(&child, 0, sizeof(child));
    child.id = ee.total_genomes + 1;
    child.generation = ee.pool.generation;
    child.parents[0] = a->id;
    child.parents[1] = b->id;
    child.mutations = 0;

    int len_a = (int)strlen(a->code);
    int len_b = (int)strlen(b->code);
    int point = rand() % (len_a + 1);
    int copy_len = point < 8192 ? point : 8191;
    strncpy(child.code, a->code, copy_len);
    child.code[copy_len] = '\0';
    if (copy_len + len_b < 8192) {
        strncat(child.code, b->code, 8191 - copy_len);
    }
    child.fitness = (a->fitness + b->fitness) / 2.0;
    child.novelty = (a->novelty + b->novelty) / 2.0;
    ee.total_genomes++;
    printf("[EVOLVE] Crossover %d x %d -> %d\n", a->id, b->id, child.id);
    return &child;
}

void evolve_mutate(Genome* g) {
    if (!g) return;
    if ((rand() % 1000) / 1000.0 < ee.pool.mutation_rate) {
        int pos = rand() % (int)strlen(g->code);
        char mutation[] = "MUT";
        if (pos + 3 < 8192) {
            memcpy(&g->code[pos], mutation, 3);
        }
        g->mutations++;
        g->fitness *= (0.9 + (rand() % 200) / 1000.0);
        g->novelty += 0.1;
        printf("[EVOLVE] Mutation at pos %d in genome %d\n", pos, g->id);
    }
}

AutoGenModule* evolve_create_module(const char* name, const char* template_code) {
    if (ee.module_count >= 16) return NULL;
    AutoGenModule* m = &ee.modules[ee.module_count++];
    snprintf(m->name, sizeof(m->name), "%s", name);
    snprintf(m->template_code, sizeof(m->template_code), "%s", template_code);
    snprintf(m->parameters, sizeof(m->parameters), "{}");
    m->generated_count = 0;
    m->deployed_count = 0;
    m->rollback_count = 0;
    printf("[EVOLVE] Module '%s' created\n", name);
    return m;
}

void evolve_generate_module(AutoGenModule* m, const char* params) {
    if (!m) return;
    m->generated_count++;
    snprintf(m->parameters, sizeof(m->parameters), "%s", params);
    printf("[EVOLVE] Generated module '%s' variant %d\n", m->name, m->generated_count);
}

int evolve_deploy_module(AutoGenModule* m) {
    if (!m) return 0;
    m->deployed_count++;
    printf("[EVOLVE] Deployed module '%s' (%d total)\n", m->name, m->deployed_count);
    return 1;
}

void evolve_show_population(void) {
    printf("=== Population ===\n");
    printf("%-4s %-8s %-10s %-8s %-6s %s\n", "ID", "Gen", "Fitness", "Mutat", "Novel", "Code");
    for (int i = 0; i < ee.pool.individual_count; i++) {
        Genome* g = &ee.pool.individuals[i];
        printf("%-4d %-8d %-10.2f %-8d %-6.2f %s\n",
               g->id, g->generation, g->fitness, g->mutations, g->novelty, g->code);
    }
}

void evolve_show_generation_stats(void) {
    printf("=== Generation Stats ===\n");
    printf("  Generation: %d\n", ee.pool.generation);
    printf("  Population: %d\n", ee.pool.individual_count);
    printf("  Best Fitness: %.2f\n", ee.pool.best_fitness);
    printf("  Avg Fitness: %.2f\n", ee.pool.avg_fitness);
    printf("  Mutation Rate: %.2f\n", ee.pool.mutation_rate);
    printf("  Crossover Rate: %.2f\n", ee.pool.crossover_rate);
    printf("  Elite Count: %d\n", ee.pool.elite_count);
    printf("  Total Generations: %d\n", ee.total_generations);
    printf("  Total Genomes: %d\n", ee.total_genomes);
}

void evolve_show_modules(void) {
    printf("=== Auto-Gen Modules ===\n");
    printf("%-20s %-8s %-8s %-8s %s\n", "Name", "Generated", "Deployed", "Rollback", "Params");
    for (int i = 0; i < ee.module_count; i++) {
        AutoGenModule* m = &ee.modules[i];
        printf("%-20s %-8d %-8d %-8d %s\n",
               m->name, m->generated_count, m->deployed_count, m->rollback_count, m->parameters);
    }
}
