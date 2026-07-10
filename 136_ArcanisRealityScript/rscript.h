#ifndef RSCRIPT_H
#define RSCRIPT_H

typedef enum {
    RW_CREATE, RW_MODIFY, RW_DELETE, RW_OBSERVE, RW_COLLAPSE, RW_ENTANGLE, RW_SUPERPOSE
} RealityKeyword;

typedef struct {
    char id[32];
    char name[64];
    char code[4096];
    int line_count;
    int compiled;
    int execution_count;
    double reality_impact;
} RealityScript;

typedef struct {
    char name[64];
    char value[128];
} Variable;

typedef struct {
    char id[32];
    char state[8192];
    Variable stack[256];
    int stack_ptr;
    Variable variables[32];
    int program_counter;
    int running;
    int reality_layer;
} RealityVM;

typedef struct {
    RealityScript scripts[8];
    RealityVM vm;
    int total_executions;
    int paradoxes_created;
    int realities_modified;
} RealityProgram;

void rscript_init(RealityProgram *prog);
void rscript_compile(RealityScript *script);
void rscript_execute(RealityScript *script, int layer);
void rscript_create_reality(RealityProgram *prog, const char *name, const char *code);
void rscript_collapse_wave(RealityVM *vm);
void rscript_entangle(RealityVM *a, RealityVM *b);
void rscript_show_scripts(const RealityProgram *prog);
void rscript_show_vm(const RealityVM *vm);

#endif
