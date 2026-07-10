/**
 * make.h — Build Automation Tool
 *
 * Make-like build system with targets, dependencies, and rules.
 * Supports variable substitution, pattern rules, and phony targets.
 */
#ifndef ARCANIS_MAKE_H
#define ARCANIS_MAKE_H

#include <arcanis/types.h>

#define MAKE_MAX_TARGETS    64
#define MAKE_MAX_RULES      128
#define MAKE_MAX_DEPS       16
#define MAKE_MAX_VARIABLES  32
#define MAKE_MAX_LINE       256
#define MAKE_MAX_CMD        512
#define MAKE_MAX_NAME       128

typedef struct {
    char name[MAKE_MAX_NAME];
    char command[MAKE_MAX_CMD];
    int  phony;      /* Non-file target */
} make_rule_t;

typedef struct {
    char name[MAKE_MAX_NAME];
    char deps[MAKE_MAX_DEPS][MAKE_MAX_NAME];
    int  num_deps;
    int  rule_idx;   /* Index into rules array, -1 = no command */
} make_target_t;

typedef struct {
    char name[MAKE_MAX_NAME];
    char value[MAKE_MAX_CMD];
} make_var_t;

typedef struct {
    make_target_t targets[MAKE_MAX_TARGETS];
    make_rule_t   rules[MAKE_MAX_RULES];
    make_var_t    vars[MAKE_MAX_VARIABLES];
    uint32_t      num_targets;
    uint32_t      num_rules;
    uint32_t      num_vars;
    char          makefile[MAKE_MAX_LINE];
    int           verbose;
    int           dry_run;
} make_context_t;

/* Initialize make context */
void make_init(make_context_t* ctx);

/* Parse makefile */
int  make_parse_file(make_context_t* ctx, const char* filename);

/* Parse makefile from string */
int  make_parse_string(make_context_t* ctx, const char* content);

/* Build a target */
int  make_build(make_context_t* ctx, const char* target);

/* List all targets */
int  make_list_targets(make_context_t* ctx, char* buf, uint32_t buf_len);

/* Variable operations */
int  make_set_var(make_context_t* ctx, const char* name, const char* value);
char* make_get_var(make_context_t* ctx, const char* name);

/* Utility */
int  make_file_exists(const char* filename);
uint32_t make_file_mtime(const char* filename);
void make_print_rules(make_context_t* ctx);

/* Built-in variables */
#define MAKE_VAR_CC       "CC"
#define MAKE_VAR_CFLAGS   "CFLAGS"
#define MAKE_VAR_LDFLAGS  "LDFLAGS"
#define MAKE_VAR_AR       "AR"
#define MAKE_VAR_RM       "RM"

#endif
