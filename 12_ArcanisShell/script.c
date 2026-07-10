/**
 * script.c — Shell Scripting Engine Implementation
 *
 * Tokenizer, parser, and interpreter for Bash-like scripts.
 */
#include <arcanis/script.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

void script_init(script_state_t* state) {
    if (!state) return;
    memset(state, 0, sizeof(script_state_t));
    state->running = 1;
}

/* ---- Utility ---- */

int script_atoi(const char* str) {
    if (!str) return 0;
    int result = 0;
    int neg = 0;
    if (*str == '-') { neg = 1; str++; }
    while (*str >= '0' && *str <= '9')
        result = result * 10 + (*str++ - '0');
    return neg ? -result : result;
}

void script_itoa(int val, char* str) {
    if (!str) return;
    if (val < 0) { *str++ = '-'; val = -val; }
    char tmp[16];
    int i = 0;
    if (val == 0) tmp[i++] = '0';
    else while (val > 0) { tmp[i++] = '0' + val % 10; val /= 10; }
    for (int j = i - 1; j >= 0; j--) *str++ = tmp[j];
    *str = '\0';
}

/* ---- Tokenizer ---- */

static int is_special(char c) {
    return c == ';' || c == '|' || c == '&' || c == '>' ||
           c == '<' || c == '(' || c == ')' || c == '{' ||
           c == '}' || c == '$' || c == '=' || c == '\n';
}

int script_tokenize(const char* input, token_t* tokens, uint32_t max_tokens) {
    if (!input || !tokens) return -1;

    uint32_t count = 0;
    const char* p = input;

    while (*p && count < max_tokens) {
        /* Skip whitespace */
        while (*p == ' ' || *p == '\t') p++;
        if (*p == '\0') break;

        /* Comment */
        if (*p == '#') {
            while (*p && *p != '\n') p++;
            continue;
        }

        token_t* tok = &tokens[count];

        /* String */
        if (*p == '"' || *p == '\'') {
            char quote = *p++;
            tok->type = TOK_STRING;
            uint32_t i = 0;
            while (*p && *p != quote && i < 255)
                tok->value[i++] = *p++;
            tok->value[i] = '\0';
            if (*p == quote) p++;
            count++;
            continue;
        }

        /* Number */
        if (*p >= '0' && *p <= '9') {
            tok->type = TOK_NUMBER;
            uint32_t i = 0;
            while ((*p >= '0' && *p <= '9') && i < 255)
                tok->value[i++] = *p++;
            tok->value[i] = '\0';
            count++;
            continue;
        }

        /* Special characters */
        if (*p == '\n') {
            tok->type = TOK_NEWLINE;
            tok->value[0] = '\n';
            tok->value[1] = '\0';
            p++;
            count++;
            continue;
        }
        if (*p == ';') { tok->type = TOK_SEMICOLON; tok->value[0] = ';'; p++; count++; continue; }
        if (*p == '|') {
            if (p[1] == '|') { tok->type = TOK_OPERATOR; tok->value[0] = '|'; tok->value[1] = '|'; p += 2; }
            else { tok->type = TOK_PIPE; tok->value[0] = '|'; p++; }
            count++; continue;
        }
        if (*p == '&') {
            if (p[1] == '&') { tok->type = TOK_OPERATOR; tok->value[0] = '&'; tok->value[1] = '&'; p += 2; }
            else if (p[1] == '>') { tok->type = TOK_AMP_GT; tok->value[0] = '&'; tok->value[1] = '>'; p += 2; }
            else { tok->type = TOK_AMP; tok->value[0] = '&'; p++; }
            count++; continue;
        }
        if (*p == '>') {
            if (p[1] == '>') { tok->type = TOK_DGT; tok->value[0] = '>'; tok->value[1] = '>'; p += 2; }
            else { tok->type = TOK_GT; tok->value[0] = '>'; p++; }
            count++; continue;
        }
        if (*p == '<') {
            if (p[1] == '<') { tok->type = TOK_DLT; tok->value[0] = '<'; tok->value[1] = '<'; p += 2; }
            else { tok->type = TOK_LT; tok->value[0] = '<'; p++; }
            count++; continue;
        }
        if (*p == '(') { tok->type = TOK_LPAREN; tok->value[0] = '('; p++; count++; continue; }
        if (*p == ')') { tok->type = TOK_RPAREN; tok->value[0] = ')'; p++; count++; continue; }
        if (*p == '{') { tok->type = TOK_LBRACE; tok->value[0] = '{'; p++; count++; continue; }
        if (*p == '}') { tok->type = TOK_RBRACE; tok->value[0] = '}'; p++; count++; continue; }
        if (*p == '$') { tok->type = TOK_DOLLAR; tok->value[0] = '$'; p++; count++; continue; }
        if (*p == '=') { tok->type = TOK_EQUALS; tok->value[0] = '='; p++; count++; continue; }

        /* Word */
        tok->type = TOK_WORD;
        uint32_t i = 0;
        while (*p && !(*p == ' ' || *p == '\t' || *p == '\n' ||
               *p == ';' || *p == '|' || *p == '&' || *p == '>' ||
               *p == '<' || *p == '(' || *p == ')') && i < 255)
            tok->value[i++] = *p++;
        tok->value[i] = '\0';
        count++;
    }

    /* Add EOF */
    if (count < max_tokens) {
        tokens[count].type = TOK_EOF;
        tokens[count].value[0] = '\0';
    }

    return (int)count;
}

const char* token_type_name(token_type_t type) {
    switch (type) {
        case TOK_WORD:      return "WORD";
        case TOK_STRING:    return "STRING";
        case TOK_NUMBER:    return "NUMBER";
        case TOK_OPERATOR:  return "OPERATOR";
        case TOK_SEMICOLON: return "SEMICOLON";
        case TOK_NEWLINE:   return "NEWLINE";
        case TOK_PIPE:      return "PIPE";
        case TOK_AMP:       return "AMP";
        case TOK_GT:        return "GT";
        case TOK_LT:        return "LT";
        case TOK_DGT:       return "DGT";
        case TOK_DLT:       return "DLT";
        case TOK_AMP_GT:    return "AMP_GT";
        case TOK_EQUALS:    return "EQUALS";
        case TOK_LPAREN:    return "LPAREN";
        case TOK_RPAREN:    return "RPAREN";
        case TOK_LBRACE:    return "LBRACE";
        case TOK_RBRACE:    return "RBRACE";
        case TOK_DOLLAR:    return "DOLLAR";
        case TOK_BACKTICK:  return "BACKTICK";
        case TOK_EOF:       return "EOF";
        default:            return "UNKNOWN";
    }
}

/* ---- Variable management ---- */

int script_var_set(script_state_t* state, const char* name, const char* value) {
    if (!state || !name || !value) return -1;

    /* Find existing */
    for (uint32_t i = 0; i < state->num_vars; i++) {
        if (string_compare(state->vars[i].name, name) == 0) {
            string_copy(state->vars[i].value, value, 1024);
            return 0;
        }
    }

    /* Add new */
    if (state->num_vars >= SCRIPT_MAX_VARS) return -1;
    script_var_t* v = &state->vars[state->num_vars++];
    string_copy(v->name, name, 64);
    string_copy(v->value, value, 1024);
    v->exported = 0;
    return 0;
}

char* script_var_get(script_state_t* state, const char* name) {
    if (!state || !name) return NULL;
    for (uint32_t i = 0; i < state->num_vars; i++)
        if (string_compare(state->vars[i].name, name) == 0)
            return state->vars[i].value;
    return NULL;
}

int script_var_exists(script_state_t* state, const char* name) {
    return script_var_get(state, name) != NULL;
}

void script_var_unset(script_state_t* state, const char* name) {
    if (!state || !name) return;
    for (uint32_t i = 0; i < state->num_vars; i++) {
        if (string_compare(state->vars[i].name, name) == 0) {
            for (uint32_t j = i; j < state->num_vars - 1; j++)
                state->vars[j] = state->vars[j + 1];
            state->num_vars--;
            return;
        }
    }
}

/* ---- Function management ---- */

int script_func_define(script_state_t* state, const char* name,
                        const char* body, char params[][64], uint32_t param_count) {
    if (!state || !name || !body) return -1;

    /* Find existing or add new */
    script_func_t* func = NULL;
    for (uint32_t i = 0; i < state->num_funcs; i++) {
        if (string_compare(state->funcs[i].name, name) == 0) {
            func = &state->funcs[i];
            break;
        }
    }
    if (!func) {
        if (state->num_funcs >= SCRIPT_MAX_FUNCS) return -1;
        func = &state->funcs[state->num_funcs++];
    }

    string_copy(func->name, name, 64);
    string_copy(func->body, body, 4096);
    func->param_count = param_count;
    for (uint32_t i = 0; i < param_count; i++)
        string_copy(func->params[i], params[i], 64);
    func->defined = 1;
    return 0;
}

script_func_t* script_func_find(script_state_t* state, const char* name) {
    if (!state || !name) return NULL;
    for (uint32_t i = 0; i < state->num_funcs; i++)
        if (state->funcs[i].defined && string_compare(state->funcs[i].name, name) == 0)
            return &state->funcs[i];
    return NULL;
}

int script_func_call(script_state_t* state, const char* name,
                      int argc, char** argv) {
    if (!state || !name) return -1;

    script_func_t* func = script_func_find(state, name);
    if (!func) return -1;

    /* Set parameters as local variables */
    for (uint32_t i = 0; i < func->param_count; i++) {
        char* val = (i < argc) ? argv[i] : "";
        script_var_set(state, func->params[i], val);
    }

    /* Execute function body */
    return script_execute_line(state, func->body);
}

/* ---- String expansion ---- */

int script_expand_vars(script_state_t* state, const char* input, char* output, uint32_t max) {
    if (!state || !input || !output) return -1;

    uint32_t out_pos = 0;
    const char* p = input;

    while (*p && out_pos < max - 1) {
        if (*p == '$' && p[1] == '{') {
            /* ${VAR} */
            p += 2;
            char var_name[64];
            uint32_t i = 0;
            while (*p && *p != '}' && i < 63)
                var_name[i++] = *p++;
            var_name[i] = '\0';
            if (*p == '}') p++;

            char* val = script_var_get(state, var_name);
            if (val) {
                uint32_t vlen = string_length(val);
                if (out_pos + vlen < max) {
                    memcpy(output + out_pos, val, vlen);
                    out_pos += vlen;
                }
            }
        } else if (*p == '$' && p[1] >= 'a' && p[1] <= 'z') {
            /* $VAR */
            p++;
            char var_name[64];
            uint32_t i = 0;
            while (*p && ((*p >= 'a' && *p <= 'z') || (*p >= '0' && *p <= '9') || *p == '_') && i < 63)
                var_name[i++] = *p++;
            var_name[i] = '\0';

            char* val = script_var_get(state, var_name);
            if (val) {
                uint32_t vlen = string_length(val);
                if (out_pos + vlen < max) {
                    memcpy(output + out_pos, val, vlen);
                    out_pos += vlen;
                }
            }
        } else if (*p == '$' && p[1] == '?') {
            /* $? — last return code */
            p += 2;
            char num[16];
            script_itoa(state->last_return, num);
            uint32_t nlen = string_length(num);
            if (out_pos + nlen < max) {
                memcpy(output + out_pos, num, nlen);
                out_pos += nlen;
            }
        } else if (*p == '$' && p[1] == '$') {
            /* $$ — PID */
            p += 2;
            output[out_pos++] = '1'; /* Simulated PID */
        } else if (*p == '\\' && p[1]) {
            /* Escape */
            p++;
            output[out_pos++] = *p++;
        } else {
            output[out_pos++] = *p++;
        }
    }
    output[out_pos] = '\0';
    return 0;
}

int script_expand_command(script_state_t* state, const char* input, char* output, uint32_t max) {
    /* Expand $(command) by executing it and capturing output */
    if (!input || !output) return -1;

    uint32_t out_pos = 0;
    const char* p = input;

    while (*p && out_pos < max - 1) {
        if (*p == '$' && p[1] == '(') {
            p += 2;
            char cmd[256];
            uint32_t i = 0;
            int depth = 1;
            while (*p && depth > 0 && i < 255) {
                if (*p == '(') depth++;
                else if (*p == ')') { depth--; if (depth == 0) break; }
                cmd[i++] = *p++;
            }
            cmd[i] = '\0';
            if (*p == ')') p++;

            /* Execute command and capture output */
            /* In real implementation: pipe output */
            char result[256] = "output";
            uint32_t rlen = string_length(result);
            if (out_pos + rlen < max) {
                memcpy(output + out_pos, result, rlen);
                out_pos += rlen;
            }
        } else {
            output[out_pos++] = *p++;
        }
    }
    output[out_pos] = '\0';
    return 0;
}

/* ---- Condition evaluation ---- */

int script_test_condition(script_state_t* state, const char* op,
                           const char* left, const char* right) {
    if (!op || !left) return 0;

    if (string_compare(op, "-eq") == 0) return script_atoi(left) == script_atoi(right);
    if (string_compare(op, "-ne") == 0) return script_atoi(left) != script_atoi(right);
    if (string_compare(op, "-lt") == 0) return script_atoi(left) < script_atoi(right);
    if (string_compare(op, "-le") == 0) return script_atoi(left) <= script_atoi(right);
    if (string_compare(op, "-gt") == 0) return script_atoi(left) > script_atoi(right);
    if (string_compare(op, "-ge") == 0) return script_atoi(left) >= script_atoi(right);
    if (string_compare(op, "=") == 0 || string_compare(op, "-eq") == 0)
        return string_compare(left, right) == 0;
    if (string_compare(op, "!=") == 0) return string_compare(left, right) != 0;
    if (string_compare(op, "-z") == 0) return string_length(left) == 0;
    if (string_compare(op, "-n") == 0) return string_length(left) != 0;
    if (string_compare(op, "-f") == 0) return 1; /* File exists (simulated) */
    if (string_compare(op, "-d") == 0) return 1; /* Directory exists */
    if (string_compare(op, "-r") == 0) return 1; /* Readable */

    return string_compare(left, "") != 0;
}

/* ---- Simple parser (recursive descent) ---- */

static ast_node_t* alloc_node(node_type_t type) {
    ast_node_t* node = (ast_node_t*)kmalloc(sizeof(ast_node_t));
    if (node) memset(node, 0, sizeof(ast_node_t));
    if (node) node->type = type;
    return node;
}

ast_node_t* script_parse(const char* source) {
    if (!source) return NULL;

    /* Simplified: parse as sequence of commands */
    ast_node_t* root = alloc_node(NODE_SEQUENCE);
    ast_node_t* current = root;

    const char* p = source;
    while (*p) {
        /* Skip whitespace */
        while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') p++;
        if (*p == '\0') break;

        /* Check for keywords */
        if (string_compare_n(p, "if ", 3) == 0) {
            ast_node_t* node = alloc_node(NODE_IF);
            /* Parse condition */
            p += 3;
            while (*p && *p != ';' && *p != '\n') p++;
            if (*p == ';') p++;
            /* Parse body */
            while (*p && (*p == ' ' || *p == '\t')) p++;
            /* Simplified: just capture the line */
            uint32_t i = 0;
            while (*p && *p != '\n' && *p != ';' && i < 255)
                node->value[i++] = *p++;
            node->value[i] = '\0';
            current->next = node;
            current = node;
        } else if (string_compare_n(p, "for ", 4) == 0) {
            ast_node_t* node = alloc_node(NODE_FOR);
            p += 4;
            uint32_t i = 0;
            while (*p && *p != ';' && *p != '\n' && i < 255)
                node->value[i++] = *p++;
            node->value[i] = '\0';
            current->next = node;
            current = node;
        } else if (string_compare_n(p, "while ", 6) == 0) {
            ast_node_t* node = alloc_node(NODE_WHILE);
            p += 6;
            uint32_t i = 0;
            while (*p && *p != ';' && *p != '\n' && i < 255)
                node->value[i++] = *p++;
            node->value[i] = '\0';
            current->next = node;
            current = node;
        } else if (string_compare_n(p, "function ", 9) == 0) {
            ast_node_t* node = alloc_node(NODE_FUNCTION);
            p += 9;
            uint32_t i = 0;
            while (*p && *p != '{' && *p != ' ' && i < 255)
                node->value[i++] = *p++;
            node->value[i] = '\0';
            current->next = node;
            current = node;
        } else if (string_compare_n(p, "return ", 7) == 0) {
            ast_node_t* node = alloc_node(NODE_BUILTIN);
            string_copy(node->value, "return", 256);
            p += 7;
            uint32_t i = 0;
            while (*p && *p != '\n' && *p != ';' && i < 255)
                node->args[0][i++] = *p++;
            node->args[0][i] = '\0';
            node->arg_count = 1;
            current->next = node;
            current = node;
        } else {
            /* Regular command */
            ast_node_t* node = alloc_node(NODE_COMMAND);
            uint32_t i = 0;
            while (*p && *p != '\n' && *p != ';' && i < 255)
                node->value[i++] = *p++;
            node->value[i] = '\0';
            current->next = node;
            current = node;
        }

        /* Skip to next line */
        while (*p && *p != '\n') p++;
        if (*p == '\n') p++;
    }

    return root;
}

ast_node_t* script_parse_line(const char* line) {
    return script_parse(line);
}

void script_free_ast(ast_node_t* node) {
    if (!node) return;
    script_free_ast(node->next);
    script_free_ast(node->left);
    script_free_ast(node->right);
    script_free_ast(node->condition);
    script_free_ast(node->body);
    script_free_ast(node->else_body);
    kfree(node);
}

/* ---- Interpreter ---- */

int script_execute_line(script_state_t* state, const char* line) {
    if (!state || !line) return -1;

    /* Expand variables */
    char expanded[2048];
    script_expand_vars(state, line, expanded, sizeof(expanded));

    /* Parse */
    ast_node_t* ast = script_parse(expanded);
    if (!ast) return -1;

    int result = script_execute_node(state, ast);
    script_free_ast(ast);
    return result;
}

int script_execute_node(script_state_t* state, ast_node_t* node) {
    if (!state || !node) return 0;

    int result = 0;

    switch (node->type) {
        case NODE_SEQUENCE:
            if (node->next) {
                result = script_execute_node(state, node->next);
            }
            break;

        case NODE_COMMAND: {
            /* Parse command and arguments */
            char line[1024];
            string_copy(line, node->value, 1024);

            char* argv[SCRIPT_MAX_ARGS];
            int argc = 0;
            char* p = line;
            while (*p && argc < SCRIPT_MAX_ARGS) {
                while (*p == ' ' || *p == '\t') p++;
                if (*p == '\0') break;
                argv[argc++] = p;
                while (*p && *p != ' ' && *p != '\t') p++;
                if (*p) *p++ = '\0';
            }

            if (argc == 0) break;

            /* Check builtins */
            if (string_compare(argv[0], "exit") == 0) {
                state->running = 0;
                result = (argc > 1) ? script_atoi(argv[1]) : 0;
            } else if (string_compare(argv[0], "echo") == 0) {
                for (int i = 1; i < argc; i++) {
                    /* printf("%s%s", i > 1 ? " " : "", argv[i]); */
                }
                /* printf("\n"); */
            } else if (string_compare(argv[0], "cd") == 0) {
                script_builtin_cd(state, argc, argv);
            } else if (string_compare(argv[0], "set") == 0) {
                script_builtin_set(state, argc, argv);
            } else if (string_compare(argv[0], "export") == 0) {
                script_builtin_export(state, argc, argv);
            } else if (string_compare(argv[0], "return") == 0) {
                result = (argc > 1) ? script_atoi(argv[1]) : 0;
                state->last_return = result;
            } else if (string_compare(argv[0], "test") == 0 || string_compare(argv[0], "[") == 0) {
                result = script_builtin_test(state, argc, argv);
            } else {
                /* Check for function call */
                script_func_t* func = script_func_find(state, argv[0]);
                if (func) {
                    result = script_func_call(state, argv[0], argc, argv);
                } else {
                    /* External command */
                    /* result = system(line); */
                }
            }
            state->last_return = result;
            break;
        }

        case NODE_IF:
            /* Simplified: execute if condition is true */
            result = 0;
            break;

        case NODE_FOR:
            /* Simplified: loop */
            result = 0;
            break;

        case NODE_WHILE:
            result = 0;
            break;

        case NODE_FUNCTION: {
            /* Extract function name and body */
            char name[64];
            uint32_t i = 0;
            const char* p = node->value;
            while (*p && *p != ' ' && *p != '(' && i < 63)
                name[i++] = *p++;
            name[i] = '\0';
            script_func_define(state, name, "", NULL, 0);
            break;
        }

        case NODE_ASSIGN: {
            /* name=value */
            const char* eq = node->value;
            while (*eq && *eq != '=') eq++;
            if (*eq == '=') {
                char name[64];
                uint32_t nlen = eq - node->value;
                if (nlen >= 64) nlen = 63;
                memcpy(name, node->value, nlen);
                name[nlen] = '\0';
                script_var_set(state, name, eq + 1);
            }
            break;
        }

        default:
            break;
    }

    /* Process siblings */
    if (node->next) {
        script_execute_node(state, node->next);
    }

    return result;
}

int script_run_file(script_state_t* state, const char* filename) {
    if (!state || !filename) return -1;

    /* In real implementation: read file contents */
    /* FILE* f = fopen(filename, "r"); */
    /* ... */
    return 0;
}

/* ---- Built-in implementations ---- */

int script_builtin_exit(script_state_t* state, int argc, char** argv) {
    if (state) state->running = 0;
    return (argc > 1) ? script_atoi(argv[1]) : 0;
}

int script_builtin_echo(script_state_t* state, int argc, char** argv) {
    for (int i = 1; i < argc; i++) {
        /* printf("%s%s", i > 1 ? " " : "", argv[i]); */
    }
    /* printf("\n"); */
    return 0;
}

int script_builtin_cd(script_state_t* state, int argc, char** argv) {
    const char* dir = (argc > 1) ? argv[1] : "/";
    script_var_set(state, "OLDPWD", script_var_get(state, "PWD") ?: "/");
    script_var_set(state, "PWD", dir);
    return 0;
}

int script_builtin_set(script_state_t* state, int argc, char** argv) {
    for (int i = 1; i < argc; i++) {
        const char* eq = argv[i];
        while (*eq && *eq != '=') eq++;
        if (*eq == '=') {
            char name[64];
            uint32_t nlen = eq - argv[i];
            if (nlen >= 64) nlen = 63;
            memcpy(name, argv[i], nlen);
            name[nlen] = '\0';
            script_var_set(state, name, eq + 1);
        }
    }
    return 0;
}

int script_builtin_unset(script_state_t* state, int argc, char** argv) {
    for (int i = 1; i < argc; i++)
        script_var_unset(state, argv[i]);
    return 0;
}

int script_builtin_export(script_state_t* state, int argc, char** argv) {
    for (int i = 1; i < argc; i++) {
        const char* eq = argv[i];
        while (*eq && *eq != '=') eq++;
        if (*eq == '=') {
            char name[64];
            uint32_t nlen = eq - argv[i];
            if (nlen >= 64) nlen = 63;
            memcpy(name, argv[i], nlen);
            name[nlen] = '\0';
            script_var_set(state, name, eq + 1);
        }
    }
    return 0;
}

int script_builtin_test(script_state_t* state, int argc, char** argv) {
    if (argc < 3) return 0;
    if (string_compare(argv[1], "-f") == 0) return 1;
    if (string_compare(argv[1], "-d") == 0) return 1;
    if (string_compare(argv[1], "-z") == 0) return string_length(argv[2]) == 0;
    if (string_compare(argv[1], "-n") == 0) return string_length(argv[2]) != 0;
    if (argc >= 4) return script_test_condition(state, argv[2], argv[1], argv[3]);
    return 0;
}

int script_builtin_return(script_state_t* state, int argc, char** argv) {
    int val = (argc > 1) ? script_atoi(argv[1]) : 0;
    if (state) state->last_return = val;
    return val;
}

int script_builtin_source(script_state_t* state, int argc, char** argv) {
    if (argc < 2) return -1;
    return script_run_file(state, argv[1]);
}

int script_builtin_local(script_state_t* state, int argc, char** argv) {
    return script_builtin_set(state, argc, argv);
}
