/**
 * awk.c — Text Processing Language Implementation
 *
 * AWK-like pattern-action language for text processing.
 */
#include <arcanis/awk.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <ctype.h>

/* ---- Initialization ---- */

void awk_init(awk_context_t* ctx) {
    if (!ctx) return;
    memset(ctx, 0, sizeof(awk_context_t));
    string_copy(ctx->fs, " ", sizeof(ctx->fs));
    string_copy(ctx->ofs, " ", sizeof(ctx->ofs));
    string_copy(ctx->rs, "\n", sizeof(ctx->rs));
}

/* ---- Variable operations ---- */

int awk_set_var(awk_context_t* ctx, const char* name, const char* value) {
    if (!ctx || !name || !value) return -1;

    /* Check if exists */
    for (uint32_t i = 0; i < ctx->num_vars; i++) {
        if (string_compare(ctx->vars[i].name, name) == 0) {
            string_copy(ctx->vars[i].value, value, AWK_MAX_VAR_VALUE);
            return 0;
        }
    }

    if (ctx->num_vars >= AWK_MAX_VAR_LEN) return -1;

    awk_var_t* var = &ctx->vars[ctx->num_vars++];
    string_copy(var->name, name, AWK_MAX_VAR_LEN);
    string_copy(var->value, value, AWK_MAX_VAR_VALUE);
    return 0;
}

char* awk_get_var(awk_context_t* ctx, const char* name) {
    if (!ctx || !name) return NULL;

    /* Check built-in vars */
    if (string_compare(name, "NR") == 0) {
        static char buf[32];
        snprintf(buf, 32, "%u", ctx->nr);
        return buf;
    }
    if (string_compare(name, "NF") == 0) {
        static char buf[32];
        snprintf(buf, 32, "%u", ctx->nf);
        return buf;
    }
    if (string_compare(name, "FS") == 0) return ctx->fs;
    if (string_compare(name, "OFS") == 0) return ctx->ofs;
    if (string_compare(name, "RS") == 0) return ctx->rs;
    if (string_compare(name, "FILENAME") == 0) return ctx->filename;

    /* Check user vars */
    for (uint32_t i = 0; i < ctx->num_vars; i++) {
        if (string_compare(ctx->vars[i].name, name) == 0)
            return ctx->vars[i].value;
    }
    return NULL;
}

/* ---- Field operations ---- */

void awk_split_record(awk_context_t* ctx) {
    if (!ctx || !ctx->record[0]) return;

    ctx->nf = 0;
    uint32_t pos = 0;
    uint32_t fs_len = string_length(ctx->fs);

    while (ctx->record[pos] && ctx->nf < AWK_MAX_FIELDS) {
        uint32_t fstart = pos;

        /* Find next field separator */
        while (ctx->record[pos]) {
            if (fs_len == 1 && ctx->record[pos] == ctx->fs[0]) {
                pos++;
                break;
            }
            if (fs_len > 1 && string_compare(ctx->record + pos, ctx->fs) == 0) {
                pos += fs_len;
                break;
            }
            pos++;
        }

        uint32_t flen = pos - fstart - (ctx->record[pos] ? 0 : 0);
        if (ctx->record[pos - 1] == ctx->fs[0] || pos == string_length(ctx->record))
            flen = pos - fstart - (ctx->record[pos - 1] == ctx->fs[0] ? 1 : 0);

        /* Copy field */
        uint32_t copy_len = flen;
        if (copy_len >= AWK_MAX_LINE) copy_len = AWK_MAX_LINE - 1;
        for (uint32_t k = 0; k < copy_len; k++)
            ctx->fields[ctx->nf][k] = ctx->record[fstart + k];
        ctx->fields[ctx->nf][copy_len] = '\0';
        ctx->nf++;
    }
}

char* awk_get_field(awk_context_t* ctx, uint32_t field_num) {
    if (!ctx || field_num >= ctx->nf) return NULL;
    return ctx->fields[field_num];
}

void awk_set_field(awk_context_t* ctx, uint32_t field_num, const char* value) {
    if (!ctx || !value) return;
    if (field_num >= AWK_MAX_FIELDS) return;

    string_copy(ctx->fields[field_num], value, AWK_MAX_LINE);
    if (field_num >= ctx->nf) ctx->nf = field_num + 1;
}

/* ---- Pattern matching ---- */

int awk_match_pattern(awk_context_t* ctx, const char* pattern, const char* text) {
    if (!pattern || !text) return 0;

    /* Range pattern: /start/, /end/ */
    char* comma = string_find(pattern, ',');
    if (comma) {
        /* Simplified range matching */
        return string_find(text, pattern) != NULL ? 1 : 0;
    }

    /* Regex pattern: /pattern/ */
    if (pattern[0] == '/' && pattern[string_length(pattern) - 1] == '/') {
        /* Simple substring match */
        char regex[AWK_MAX_LINE];
        uint32_t rlen = string_length(pattern) - 2;
        for (uint32_t i = 0; i < rlen; i++)
            regex[i] = pattern[i + 1];
        regex[rlen] = '\0';
        return string_find(text, regex) != NULL ? 1 : 0;
    }

    /* Relational pattern: field op value */
    if (string_find(pattern, "!=") || string_find(pattern, ">") ||
        string_find(pattern, "<") || string_find(pattern, ">=") ||
        string_find(pattern, "<=") || string_find(pattern, "==")) {
        /* Simplified: check if pattern contains in text */
        return string_find(text, pattern) != NULL ? 1 : 0;
    }

    /* Simple string match */
    return string_compare(pattern, text) == 0 ||
           string_find(text, pattern) != NULL;
}

/* ---- Expression evaluation ---- */

static double eval_expr(awk_context_t* ctx, const char* expr) {
    if (!expr) return 0;

    /* Check if it's a number */
    int is_num = 1;
    uint32_t len = string_length(expr);
    for (uint32_t i = 0; i < len; i++) {
        if (!isdigit((unsigned char)expr[i]) && expr[i] != '.' && expr[i] != '-')
            is_num = 0;
    }

    if (is_num) return awk_atof(expr);

    /* Check if it's a variable */
    char* val = awk_get_var(ctx, expr);
    if (val) return awk_atof(val);

    /* Check if it's $1, $2, etc */
    if (expr[0] == '$' && isdigit((unsigned char)expr[1])) {
        uint32_t field_num = awk_atoi(expr + 1);
        char* field = awk_get_field(ctx, field_num);
        if (field) return awk_atof(field);
    }

    return 0;
}

static void eval_action(awk_context_t* ctx, const char* action, char* output, uint32_t output_len) {
    if (!action || !output) return;

    output[0] = '\0';

    /* Simple print action */
    if (string_compare_n(action, "print", 5) == 0) {
        const char* arg = action + 5;
        while (*arg == ' ') arg++;

        if (*arg == '\0') {
            /* print entire record */
            string_copy(output, ctx->record, output_len);
            uint32_t slen = string_length(output);
            output[slen] = '\n';
            output[slen + 1] = '\0';
        } else {
            /* Print specific fields or variables */
            char* arg_copy = malloc(string_length(arg) + 1);
            string_copy(arg_copy, arg, string_length(arg) + 1);

            char* token = strtok(arg_copy, " ,");
            while (token) {
                char* val = awk_get_var(ctx, token);
                if (val) {
                    string_copy(output + string_length(output), val, output_len - string_length(output));
                } else if (token[0] == '$') {
                    uint32_t field_num = awk_atoi(token + 1);
                    char* field = awk_get_field(ctx, field_num);
                    if (field) {
                        string_copy(output + string_length(output), field, output_len - string_length(output));
                    }
                } else {
                    string_copy(output + string_length(output), token, output_len - string_length(output));
                }
                string_copy(output + string_length(output), ctx->ofs, output_len - string_length(output));
                token = strtok(NULL, " ,");
            }

            /* Remove trailing OFS */
            uint32_t olen = string_length(output);
            uint32_t ofs_len = string_length(ctx->ofs);
            if (olen >= ofs_len) {
                output[olen - ofs_len] = '\0';
            }

            string_copy(output + string_length(output), "\n", output_len - string_length(output));
            free(arg_copy);
        }
    }
    /* Variable assignment */
    else if (string_find(action, "=")) {
        char* eq = string_find(action, '=');
        char var_name[AWK_MAX_VAR_LEN];
        uint32_t vlen = eq - action;
        for (uint32_t i = 0; i < vlen; i++)
            var_name[i] = action[i];
        var_name[vlen] = '\0';

        char* val_str = eq + 1;
        while (*val_str == ' ') val_str++;

        double val = eval_expr(ctx, val_str);
        char val_buf[64];
        snprintf(val_buf, 64, "%.0f", val);
        awk_set_var(ctx, var_name, val_buf);
    }
    /* Simple expression */
    else {
        double val = eval_expr(ctx, action);
        char val_buf[64];
        snprintf(val_buf, 64, "%.0f", val);
        string_copy(output, val_buf, output_len);
    }
}

/* ---- Parsing ---- */

static void trim(char* str) {
    uint32_t len = string_length(str);
    while (len > 0 && (str[len - 1] == '\n' || str[len - 1] == '\r' ||
           str[len - 1] == ' ' || str[len - 1] == '\t'))
        str[--len] = '\0';
}

int awk_parse(awk_context_t* ctx, const char* program) {
    if (!ctx || !program) return -1;

    /* Simple parsing: split by newline */
    char line[AWK_MAX_LINE];
    const char* p = program;

    while (*p) {
        uint32_t li = 0;
        while (*p && *p != '\n' && li < AWK_MAX_LINE - 1)
            line[li++] = *p++;
        line[li] = '\0';
        if (*p == '\n') p++;

        trim(line);
        if (li == 0) continue;

        /* Check for BEGIN or END */
        if (string_compare_n(line, "BEGIN", 5) == 0) {
            if (ctx->num_patterns < AWK_MAX_PATTERNS) {
                awk_pattern_t* pat = &ctx->patterns[ctx->num_patterns++];
                pat->type = AWK_PATTERN_BEGIN;
                pat->action_idx = ctx->num_actions;
            }
        } else if (string_compare_n(line, "END", 3) == 0) {
            if (ctx->num_patterns < AWK_MAX_PATTERNS) {
                awk_pattern_t* pat = &ctx->patterns[ctx->num_patterns++];
                pat->type = AWK_PATTERN_END;
                pat->action_idx = ctx->num_actions;
            }
        }
        /* Pattern { action } */
        else {
            char* brace = string_find(line, '{');
            if (brace) {
                /* Extract action */
                char* action_start = brace + 1;
                char* action_end = string_find(action_start, '}');
                if (action_end) {
                    *action_end = '\0';
                    trim(action_start);

                    if (ctx->num_actions < AWK_MAX_ACTIONS) {
                        awk_action_t* act = &ctx->actions[ctx->num_actions];
                        string_copy(act->code, action_start, AWK_MAX_LINE);
                        ctx->num_actions++;
                    }
                }

                /* Extract pattern */
                *brace = '\0';
                trim(line);

                if (ctx->num_patterns < AWK_MAX_PATTERNS) {
                    awk_pattern_t* pat = &ctx->patterns[ctx->num_patterns++];
                    if (line[0] == '/' && line[string_length(line) - 1] == '/')
                        pat->type = AWK_PATTERN_REGEX;
                    else
                        pat->type = AWK_PATTERN_EXPR;
                    string_copy(pat->pattern, line, AWK_MAX_LINE);
                    pat->action_idx = ctx->num_actions - 1;
                }
            }
        }
    }

    return 0;
}

/* ---- Execution ---- */

int awk_execute_string(awk_context_t* ctx, const char* input, const char* program,
                        char* output, uint32_t output_len) {
    if (!ctx || !input || !program) return -1;

    awk_init(ctx);
    awk_parse(ctx, program);

    output[0] = '\0';

    /* Process BEGIN patterns */
    for (uint32_t i = 0; i < ctx->num_patterns; i++) {
        if (ctx->patterns[i].type == AWK_PATTERN_BEGIN) {
            char result[AWK_MAX_LINE];
            eval_action(ctx, ctx->actions[ctx->patterns[i].action_idx].code, result, AWK_MAX_LINE);
            if (result[0]) {
                string_copy(output + string_length(output), result, output_len - string_length(output));
            }
        }
    }

    /* Process input line by line */
    const char* p = input;
    while (*p) {
        /* Read record */
        uint32_t ri = 0;
        while (*p && *p != '\n' && ri < AWK_MAX_LINE - 1)
            ctx->record[ri++] = *p++;
        ctx->record[ri] = '\0';
        if (*p == '\n') p++;

        ctx->nr++;
        awk_split_record(ctx);

        /* Match patterns */
        for (uint32_t i = 0; i < ctx->num_patterns; i++) {
            if (ctx->patterns[i].type == AWK_PATTERN_BEGIN ||
                ctx->patterns[i].type == AWK_PATTERN_END) continue;

            if (awk_match_pattern(ctx, ctx->patterns[i].pattern, ctx->record)) {
                char result[AWK_MAX_LINE];
                eval_action(ctx, ctx->actions[ctx->patterns[i].action_idx].code, result, AWK_MAX_LINE);
                if (result[0]) {
                    string_copy(output + string_length(output), result, output_len - string_length(output));
                }
            }
        }
    }

    /* Process END patterns */
    for (uint32_t i = 0; i < ctx->num_patterns; i++) {
        if (ctx->patterns[i].type == AWK_PATTERN_END) {
            char result[AWK_MAX_LINE];
            eval_action(ctx, ctx->actions[ctx->patterns[i].action_idx].code, result, AWK_MAX_LINE);
            if (result[0]) {
                string_copy(output + string_length(output), result, output_len - string_length(output));
            }
        }
    }

    return 0;
}

int awk_execute(awk_context_t* ctx, FILE* input, FILE* output) {
    if (!ctx || !input || !output) return -1;

    /* Read entire input */
    fseek(input, 0, SEEK_END);
    long size = ftell(input);
    fseek(input, 0, SEEK_SET);

    char* content = malloc(size + 1);
    if (!content) return -1;

    fread(content, 1, size, input);
    content[size] = '\0';

    char result[4096];
    awk_execute_string(ctx, content, "", result, sizeof(result));

    fprintf(output, "%s", result);

    free(content);
    return 0;
}

/* ---- Utility ---- */

double awk_atof(const char* str) {
    if (!str) return 0.0;
    return atof(str);
}

int awk_atoi(const char* str) {
    if (!str) return 0;
    return atoi(str);
}
