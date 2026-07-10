#include "rscript.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
    char name[32];
    int compiled;
    int code_lines;
    int execution_count;
    float reality_layer;
    int entangled;
} RealityScript;

typedef struct {
    int pc;
    float state[8];
    int superposition_active;
    float collapse_factor;
} VMState;

typedef struct {
    RealityScript scripts[16];
    int script_count;
    VMState vm;
} RealityProgram;

static RealityProgram rp;

void rscript_init(void) {
    rp.script_count = 0;
    rp.vm.pc = 0;
    rp.vm.superposition_active = 0;
    rp.vm.collapse_factor = 0.0f;
    for (int i = 0; i < 8; i++) rp.vm.state[i] = 0.0f;
    srand((unsigned)time(NULL));
}

void rscript_compile(const char *name, int line_count) {
    if (rp.script_count >= 16) return;
    RealityScript *rs = &rp.scripts[rp.script_count++];
    snprintf(rs->name, sizeof(rs->name), "%s", name);
    rs->compiled = 1;
    rs->code_lines = line_count;
    rs->execution_count = 0;
    rs->reality_layer = 0.0f;
    rs->entangled = 0;
    printf("Compiled '%s' (%d lines)\n", name, line_count);
}

void rscript_execute(int script_idx) {
    if (script_idx < 0 || script_idx >= rp.script_count) return;
    RealityScript *rs = &rp.scripts[script_idx];
    if (!rs->compiled) return;
    rs->execution_count++;
    rs->reality_layer += ((float)rand() / RAND_MAX) * 0.2f - 0.1f;
    if (rs->reality_layer < -1.0f) rs->reality_layer = -1.0f;
    if (rs->reality_layer > 1.0f) rs->reality_layer = 1.0f;
    rp.vm.pc = (rp.vm.pc + 1) % 8;
    printf("Executing '%s' (layer=%.2f, count=%d)\n",
           rs->name, rs->reality_layer, rs->execution_count);
}

void rscript_create_reality(const char *name, int lines) {
    rscript_compile(name, lines);
    rscript_execute(rp.script_count - 1);
    printf("Reality '%s' manifested\n", name);
}

void rscript_collapse_wave(void) {
    rp.vm.superposition_active = 0;
    rp.vm.collapse_factor = 1.0f;
    for (int i = 0; i < 8; i++) {
        rp.vm.state[i] = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
    }
    printf("Wavefunction collapsed\n");
}

void rscript_entangle(int idx1, int idx2) {
    if (idx1 >= 0 && idx1 < rp.script_count) rp.scripts[idx1].entangled = 1;
    if (idx2 >= 0 && idx2 < rp.script_count) rp.scripts[idx2].entangled = 1;
    printf("Scripts %d and %d entangled\n", idx1, idx2);
}

void rscript_show_scripts(void) {
    printf("\n%-4s %-20s %-8s %-6s %-8s %s\n",
           "Idx", "Name", "Compiled", "Lines", "Reality", "Entangled");
    printf("----------------------------------------------------------\n");
    for (int i = 0; i < rp.script_count; i++) {
        printf("%-4d %-20s %-8s %-6d %-8.2f %s\n",
               i, rp.scripts[i].name,
               rp.scripts[i].compiled ? "yes" : "no",
               rp.scripts[i].code_lines,
               rp.scripts[i].reality_layer,
               rp.scripts[i].entangled ? "yes" : "no");
    }
}

void rscript_show_vm(void) {
    printf("\nVM State:\n");
    printf("%-8s %d\n", "PC", rp.vm.pc);
    printf("%-8s %s\n", "Super", rp.vm.superposition_active ? "active" : "inactive");
    printf("State: ");
    for (int i = 0; i < 8; i++) printf("%.2f ", rp.vm.state[i]);
    printf("\n");
}
