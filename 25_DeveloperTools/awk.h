/**
 * awk.h — Text Processing Language
 *
 * AWK-like pattern-action language for text processing.
 * Supports field splitting, patterns, actions, and built-in variables.
 */
#ifndef ARCANIS_AWK_H
#define ARCANIS_AWK_H

#include <arcanis/types.h>

#define AWK_MAX_PATTERNS   32
#define AWK_MAX_ACTIONS    32
#define AWK_MAX_FIELDS     64
#define AWK_MAX_LINE       1024
#define AWK_MAX_VAR_LEN    128
#define AWK_MAX_VAR_VALUE  512

typedef enum {
    AWK_PATTERN_BEGIN,
    AWK_PATTERN_END,
    AWK_PATTERN_REGEX,
    AWK_PATTERN_EXPR,
    AWK_PATTERN_RANGE
} awk_pattern_type_t;

typedef struct {
    awk_pattern_type_t type;
    char pattern[AWK_MAX_LINE];
    int  action_idx;
} awk_pattern_t;

typedef struct {
    char code[AWK_MAX_LINE];
} awk_action_t;

typedef struct {
    char name[AWK_MAX_VAR_LEN];
    char value[AWK_MAX_VAR_VALUE];
} awk_var_t;

typedef struct {
    awk_pattern_t patterns[AWK_MAX_PATTERNS];
    awk_action_t  actions[AWK_MAX_ACTIONS];
    awk_var_t     vars[AWK_MAX_VAR_LEN];
    uint32_t      num_patterns;
    uint32_t      num_actions;
    uint32_t      num_vars;

    /* Built-in variables */
    uint32_t      nr;          /* Current record number */
    uint32_t      nf;          /* Number of fields */
    char          fields[AWK_MAX_FIELDS][AWK_MAX_LINE];
    char          record[AWK_MAX_LINE];
    char          fs[16];      /* Field separator */
    char          ofs[16];     /* Output field separator */
    char          rs[16];      /* Record separator */
    char          filename[256];
    FILE*         input;
    FILE*         output;
} awk_context_t;

/* Initialize awk context */
void awk_init(awk_context_t* ctx);

/* Parse AWK program */
int  awk_parse(awk_context_t* ctx, const char* program);

/* Execute on input */
int  awk_execute(awk_context_t* ctx, FILE* input, FILE* output);

/* Execute on string */
int  awk_execute_string(awk_context_t* ctx, const char* input, const char* program,
                        char* output, uint32_t output_len);

/* Variable operations */
int  awk_set_var(awk_context_t* ctx, const char* name, const char* value);
char* awk_get_var(awk_context_t* ctx, const char* name);

/* Field operations */
void awk_split_record(awk_context_t* ctx);
char* awk_get_field(awk_context_t* ctx, uint32_t field_num);
void awk_set_field(awk_context_t* ctx, uint32_t field_num, const char* value);

/* Pattern matching */
int  awk_match_pattern(awk_context_t* ctx, const char* pattern, const char* text);

/* Built-in functions */
double awk_atof(const char* str);
int    awk_atoi(const char* str);

#endif
