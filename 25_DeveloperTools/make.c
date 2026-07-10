/**
 * make.c — Build Automation Tool Implementation
 *
 * Make-like build system with targets, dependencies, and rules.
 */
#include <arcanis/make.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

/* ---- Initialization ---- */

void make_init(make_context_t* ctx) {
    if (!ctx) return;
    memset(ctx, 0, sizeof(make_context_t));
    ctx->verbose = 0;
    ctx->dry_run = 0;

    /* Set default variables */
    make_set_var(ctx, MAKE_VAR_CC, "gcc");
    make_set_var(ctx, MAKE_VAR_CFLAGS, "-Wall -O2");
    make_set_var(ctx, MAKE_VAR_LDFLAGS, "");
    make_set_var(ctx, MAKE_VAR_AR, "ar");
    make_set_var(ctx, MAKE_VAR_RM, "rm -f");
}

/* ---- Variable operations ---- */

int make_set_var(make_context_t* ctx, const char* name, const char* value) {
    if (!ctx || !name || !value) return -1;

    /* Check if exists */
    for (uint32_t i = 0; i < ctx->num_vars; i++) {
        if (string_compare(ctx->vars[i].name, name) == 0) {
            string_copy(ctx->vars[i].value, value, MAKE_MAX_CMD);
            return 0;
        }
    }

    if (ctx->num_vars >= MAKE_MAX_VARIABLES) return -1;

    make_var_t* var = &ctx->vars[ctx->num_vars++];
    string_copy(var->name, name, MAKE_MAX_NAME);
    string_copy(var->value, value, MAKE_MAX_CMD);
    return 0;
}

char* make_get_var(make_context_t* ctx, const char* name) {
    if (!ctx || !name) return NULL;

    for (uint32_t i = 0; i < ctx->num_vars; i++) {
        if (string_compare(ctx->vars[i].name, name) == 0)
            return ctx->vars[i].value;
    }
    return NULL;
}

/* ---- Variable expansion ---- */

static void expand_vars(make_context_t* ctx, char* buf) {
    if (!ctx || !buf) return;

    char result[MAKE_MAX_CMD];
    uint32_t ri = 0;

    for (uint32_t i = 0; buf[i] && ri < MAKE_MAX_CMD - 1; i++) {
        if (buf[i] == '$' && buf[i + 1] == '(') {
            /* Find closing paren */
            uint32_t j = i + 2;
            while (buf[j] && buf[j] != ')') j++;

            if (buf[j] == ')') {
                char var_name[MAKE_MAX_NAME];
                uint32_t vlen = j - i - 2;
                for (uint32_t k = 0; k < vlen; k++)
                    var_name[k] = buf[i + 2 + k];
                var_name[vlen] = '\0';

                char* val = make_get_var(ctx, var_name);
                if (val) {
                    uint32_t vlen2 = string_length(val);
                    for (uint32_t k = 0; k < vlen2 && ri < MAKE_MAX_CMD - 1; k++)
                        result[ri++] = val[k];
                }
                i = j;
            } else {
                result[ri++] = buf[i];
            }
        } else {
            result[ri++] = buf[i];
        }
    }
    result[ri] = '\0';
    string_copy(buf, result, MAKE_MAX_CMD);
}

/* ---- File operations ---- */

int make_file_exists(const char* filename) {
    if (!filename) return 0;

    FILE* f = fopen(filename, "r");
    if (f) {
        fclose(f);
        return 1;
    }
    return 0;
}

uint32_t make_file_mtime(const char* filename) {
    /* Simplified: return 0 if file doesn't exist */
    if (!make_file_exists(filename)) return 0;

    /* In real implementation, use stat() */
    return 1;
}

/* ---- Parsing ---- */

static void trim_line(char* line) {
    uint32_t len = string_length(line);
    while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r' || line[len - 1] == ' '))
        line[--len] = '\0';
}

static void skip_spaces(char** p) {
    while (**p == ' ' || **p == '\t') (*p)++;
}

int make_parse_string(make_context_t* ctx, const char* content) {
    if (!ctx || !content) return -1;

    char line[MAKE_MAX_LINE];
    uint32_t line_idx = 0;
    const char* p = content;

    while (*p) {
        /* Extract line */
        uint32_t li = 0;
        while (*p && *p != '\n' && li < MAKE_MAX_LINE - 1)
            line[li++] = *p++;
        line[li] = '\0';
        if (*p == '\n') p++;

        trim_line(line);
        if (li == 0 || line[0] == '#') continue;

        skip_spaces((char**)&line);

        /* Variable assignment: VAR = value */
        char* eq = string_find(line, '=');
        if (eq && *(eq - 1) != ':' && *(eq + 1) != '=' ) {
            *eq = '\0';
            char* name = line;
            char* value = eq + 1;
            skip_spaces(&value);

            /* Trim trailing spaces from name */
            uint32_t nlen = string_length(name);
            while (nlen > 0 && (name[nlen - 1] == ' ' || name[nlen - 1] == '\t'))
                name[--nlen] = '\0';

            make_set_var(ctx, name, value);
            continue;
        }

        /* Target line: target: deps */
        char* colon = string_find(line, ':');
        if (colon) {
            *colon = '\0';
            char* target_name = line;
            char* deps_str = colon + 1;
            skip_spaces(&deps_str);

            if (ctx->num_targets >= MAKE_MAX_TARGETS) continue;

            make_target_t* target = &ctx->targets[ctx->num_targets++];
            string_copy(target->name, target_name, MAKE_MAX_NAME);

            /* Parse dependencies */
            char* dep = deps_str;
            while (*dep) {
                while (*dep == ' ') dep++;
                if (*dep == '\0') break;

                char* dep_start = dep;
                while (*dep && *dep != ' ') dep++;
                uint32_t dlen = dep - dep_start;
                if (dlen >= MAKE_MAX_NAME) dlen = MAKE_MAX_NAME - 1;

                if (target->num_deps < MAKE_MAX_DEPS) {
                    string_copy(target->deps[target->num_deps++], dep_start, dlen);
                }
            }

            /* Check if next line is a command */
            char cmd_line[MAKE_MAX_LINE];
            uint32_t cli = 0;
            while (*p && *p != '\n' && cli < MAKE_MAX_LINE - 1)
                cmd_line[cli++] = *p++;
            cmd_line[cli] = '\0';
            if (*p == '\n') p++;

            trim_line(cmd_line);
            if (cmd_line[0] == '\t' || cmd_line[0] == ' ') {
                /* Command line */
                char* cmd = cmd_line;
                skip_spaces(&cmd);

                if (ctx->num_rules < MAKE_MAX_RULES) {
                    make_rule_t* rule = &ctx->rules[ctx->num_rules];
                    string_copy(rule->command, cmd, MAKE_MAX_CMD);
                    rule->phony = (string_compare(target_name, ".PHONY") == 0);
                    target->rule_idx = ctx->num_rules++;
                }
            }
        }
    }

    return 0;
}

int make_parse_file(make_context_t* ctx, const char* filename) {
    if (!ctx || !filename) return -1;

    FILE* f = fopen(filename, "r");
    if (!f) return -1;

    /* Read file content */
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);

    char* content = malloc(size + 1);
    if (!content) { fclose(f); return -1; }

    fread(content, 1, size, f);
    content[size] = '\0';
    fclose(f);

    string_copy(ctx->makefile, filename, MAKE_MAX_LINE);
    int result = make_parse_string(ctx, content);
    free(content);

    return result;
}

/* ---- Building ---- */

static int needs_rebuild(make_context_t* ctx, const char* target, const char* dep) {
    uint32_t target_mtime = make_file_mtime(target);
    uint32_t dep_mtime = make_file_mtime(dep);

    /* If target doesn't exist or dep is newer */
    return target_mtime == 0 || dep_mtime > target_mtime;
}

int make_build(make_context_t* ctx, const char* target) {
    if (!ctx || !target) return -1;

    /* Find target */
    int target_idx = -1;
    for (uint32_t i = 0; i < ctx->num_targets; i++) {
        if (string_compare(ctx->targets[i].name, target) == 0) {
            target_idx = (int)i;
            break;
        }
    }

    if (target_idx == -1) {
        /* Phony target or missing */
        return 0;
    }

    make_target_t* tgt = &ctx->targets[target_idx];

    /* Build dependencies first */
    for (int d = 0; d < tgt->num_deps; d++) {
        make_build(ctx, tgt->deps[d]);
    }

    /* Check if rebuild needed */
    int rebuild = 0;
    for (int d = 0; d < tgt->num_deps; d++) {
        if (needs_rebuild(ctx, target, tgt->deps[d])) {
            rebuild = 1;
            break;
        }
    }

    if (!rebuild && !make_file_exists(target)) rebuild = 1;

    if (!rebuild) {
        if (ctx->verbose)
            printf("make: '%s' is up to date\n", target);
        return 0;
    }

    /* Execute rule */
    if (tgt->rule_idx >= 0) {
        make_rule_t* rule = &ctx->rules[tgt->rule_idx];

        if (ctx->verbose) {
            printf("make: %s\n", rule->command);
        }

        if (!ctx->dry_run) {
            expand_vars(ctx, rule->command);
            int result = system(rule->command);
            if (result != 0) {
                printf("make: *** [%s] Error %d\n", target, result);
                return result;
            }
        }
    }

    return 0;
}

int make_list_targets(make_context_t* ctx, char* buf, uint32_t buf_len) {
    if (!ctx || !buf) return 0;

    uint32_t pos = 0;
    for (uint32_t i = 0; i < ctx->num_targets && pos < buf_len - 1; i++) {
        uint32_t nlen = string_length(ctx->targets[i].name);
        if (pos + nlen + 2 < buf_len) {
            string_copy(buf + pos, ctx->targets[i].name, nlen);
            pos += nlen;
            buf[pos++] = '\n';
        }
    }
    buf[pos] = '\0';
    return (int)pos;
}

void make_print_rules(make_context_t* ctx) {
    if (!ctx) return;

    printf("Targets:\n");
    for (uint32_t i = 0; i < ctx->num_targets; i++) {
        printf("  %s:", ctx->targets[i].name);
        for (int d = 0; d < ctx->targets[i].num_deps; d++)
            printf(" %s", ctx->targets[i].deps[d]);
        printf("\n");
    }

    printf("\nVariables:\n");
    for (uint32_t i = 0; i < ctx->num_vars; i++) {
        printf("  %s = %s\n", ctx->vars[i].name, ctx->vars[i].value);
    }
}
