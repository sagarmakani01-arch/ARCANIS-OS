#ifndef POLYGLOT_H
#define POLYGLOT_H

#include <stddef.h>

typedef enum {
    LANG_PYTHON,
    LANG_JAVASCRIPT,
    LANG_RUST,
    LANG_GO,
    LANG_C,
    LANG_CPP,
    LANG_JAVA,
    LANG_RUBY,
    LANG_LUA,
    LANG_WASM,
    LANG_SWIFT
} LanguageType;

typedef struct {
    char id[32];
    char name[64];
    LanguageType language;
    char source_code[8192];
    char bytecode[4096];
    char exports[16][64];
    char imports[16][64];
    int linked;
    int optimized;
} PolyModule;

typedef struct {
    char id[32];
    LanguageType source_lang;
    LanguageType target_lang;
    char function_name[64];
    char args[512];
    char result[512];
    int conversion_time_us;
    int success;
} CrossLanguageCall;

typedef struct {
    char id[32];
    LanguageType languages[8];
    char bridge_type[32];
    double throughput;
    int latency_us;
    int auto_convert;
} VMBridge;

typedef struct {
    PolyModule modules[32];
    int module_count;
    CrossLanguageCall calls[128];
    int call_count;
    VMBridge bridges[8];
    int bridge_count;
    int total_executions;
    int avg_conversion_us;
    int jit_enabled;
    int cross_heap_enabled;
} PolyglotRuntime;

void poly_init(PolyglotRuntime *rt);
int poly_load_module(PolyglotRuntime *rt, const char *name, const char *code, LanguageType lang);
int poly_export_function(PolyglotRuntime *rt, int mod_idx, const char *name);
int poly_cross_call(PolyglotRuntime *rt, int src_mod, const char *func, const char *args, LanguageType target_lang);
int poly_optimize(PolyglotRuntime *rt, int mod_idx);
int poly_link(PolyglotRuntime *rt, int *mod_indices, int count);
void poly_show_modules(PolyglotRuntime *rt);
void poly_show_bridges(PolyglotRuntime *rt);
void poly_show_stats(PolyglotRuntime *rt);

#endif /* POLYGLOT_H */
