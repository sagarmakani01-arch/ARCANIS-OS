#ifndef ARCANIS_GENERATIVE_H
#define ARCANIS_GENERATIVE_H

typedef struct {
    char name[64];
    char description[256];
    int lines_of_code;
    char language[16];
    char generated_by[32];
    int tested;
    int deployed;
} GenModule;

typedef struct {
    char input[1024];
    char output[4096];
    double complexity;
    double accuracy;
    int iterations;
} GenOutput;

typedef struct {
    char template_name[64];
    char code[4096];
    double quality_score;
    int uses;
    int version;
} CodeTemplate;

typedef struct {
    GenModule modules[32];
    int module_count;
    GenOutput outputs[64];
    int output_count;
    CodeTemplate templates[32];
    int template_count;
    int total_lines_generated;
    int total_tests_generated;
    int self_modifications;
    double autonomy_level;
    int auto_improve;
} GenerativeEngine;

void gen_init(void);
GenModule* gen_generate_module(const char* name, const char* desc, const char* lang);
GenOutput* gen_generate_code(const char* input, const char* template_name);
void gen_generate_tests(GenModule* m);
void gen_self_improve(void);
void gen_show_modules(void);
void gen_show_stats(void);
void gen_show_autonomy(void);

#endif
