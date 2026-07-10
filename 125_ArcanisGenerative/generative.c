#include "generative.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#define MAX_MODULES 30
#define MAX_OUTPUTS 50

typedef struct {
    char name[48];
    int lines;
    int is_tested;
    int is_documented;
} GenModule;

typedef struct {
    char id[32];
    char content[256];
    char template_used[48];
    int tested;
} GenOutput;

typedef struct {
    GenModule modules[MAX_MODULES];
    int module_count;
    GenOutput outputs[MAX_OUTPUTS];
    int output_count;
    int total_lines_generated;
    int total_tests_generated;
    int autonomy_level;
    int self_modifications;
    int templates_available;
    char templates[8][48];
} GenerativeEngine;

static GenerativeEngine ge;

void gen_init(void) {
    srand(time(NULL));
    memset(&ge, 0, sizeof(ge));
    ge.templates_available = 3;
    strncpy(ge.templates[0], "module", 48);
    strncpy(ge.templates[1], "driver", 48);
    strncpy(ge.templates[2], "test", 48);
    ge.autonomy_level = 1;
    printf("[GEN] Engine initialized with %d templates\n", ge.templates_available);
}

void gen_generate_module(const char *name) {
    if (ge.module_count >= MAX_MODULES) { printf("[GEN] Module storage full\n"); return; }
    GenModule *m = &ge.modules[ge.module_count++];
    strncpy(m->name, name, sizeof(m->name) - 1);
    m->lines = rand() % 500 + 50;
    m->is_tested = 0;
    m->is_documented = 0;
    ge.total_lines_generated += m->lines;
    printf("[GEN] Generated module '%s' (%d lines, total: %d)\n", m->name, m->lines, ge.total_lines_generated);
}

void gen_generate_code(const char *template_name) {
    if (ge.output_count >= MAX_OUTPUTS) { printf("[GEN] Output storage full\n"); return; }
    GenOutput *o = &ge.outputs[ge.output_count++];
    snprintf(o->id, sizeof(o->id), "OUT-%03d", ge.output_count);
    strncpy(o->template_used, template_name, sizeof(o->template_used) - 1);
    snprintf(o->content, sizeof(o->content), "// Auto-generated %s output %s", template_name, o->id);
    o->tested = 0;
    printf("[GEN] Generated code from template '%s' -> %s\n", template_name, o->id);
}

void gen_generate_tests(void) {
    if (ge.module_count == 0) { printf("[GEN] No modules to test\n"); return; }
    int idx = rand() % ge.module_count;
    ge.modules[idx].is_tested = 1;
    ge.total_tests_generated++;
    printf("[GEN] Generated tests for module '%s' (total tests: %d)\n", ge.modules[idx].name, ge.total_tests_generated);
}

void gen_self_improve(void) {
    ge.autonomy_level++;
    ge.self_modifications++;
    printf("[GEN] Self-improvement cycle %d complete. Autonomy: %d, Modifications: %d\n",
           ge.self_modifications, ge.autonomy_level, ge.self_modifications);
}

void gen_show_modules(void) {
    printf("\n=== GENERATED MODULES ===\n");
    printf("%-30s %-8s %-8s %-12s\n", "Name", "Lines", "Tested", "Documented");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < ge.module_count; i++)
        printf("%-30s %-8d %-8s %-12s\n",
               ge.modules[i].name, ge.modules[i].lines,
               ge.modules[i].is_tested ? "yes" : "no",
               ge.modules[i].is_documented ? "yes" : "no");
}

void gen_show_stats(void) {
    printf("\n=== GENERATIVE STATS ===\n");
    printf("Total modules: %d\n", ge.module_count);
    printf("Total outputs: %d\n", ge.output_count);
    printf("Lines generated: %d\n", ge.total_lines_generated);
    printf("Tests generated: %d\n", ge.total_tests_generated);
    printf("Autonomy level: %d\n", ge.autonomy_level);
    printf("Self modifications: %d\n", ge.self_modifications);
    printf("Templates available: %d\n", ge.templates_available);
}

void gen_show_autonomy(void) {
    printf("\n=== AUTONOMY REPORT ===\n");
    printf("Autonomy Level: %d\n", ge.autonomy_level);
    printf("Self Modifications: %d\n", ge.self_modifications);
    printf("Code Generation Rate: %.2f lines/cycle\n", ge.module_count > 0 ? (float)ge.total_lines_generated / ge.module_count : 0);
    printf("Test Coverage: %.2f%%\n", ge.module_count > 0 ? ((float)ge.total_tests_generated / ge.module_count) * 100 : 0);
}
