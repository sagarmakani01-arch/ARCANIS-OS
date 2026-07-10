/**
 * shell_script.h — Shell Scripting Engine
 *
 * Bash-like scripting with variables, conditionals, loops, functions, and pipes.
 */
#ifndef ARCANIS_SHELL_SCRIPT_H
#define ARCANIS_SHELL_SCRIPT_H

#include <arcanis/types.h>

#define SCRIPT_MAX_LINE     1024
#define SCRIPT_MAX_VARS     128
#define SCRIPT_MAX_FUNCS    32
#define SCRIPT_MAX_STACK    32
#define SCRIPT_MAX_ARGS     16
#define SCRIPT_MAX_LOOP     256

typedef enum {
    TOK_WORD, TOK_STRING, TOK_NUMBER, TOK_OPERATOR,
    TOK_SEMICOLON, TOK_NEWLINE, TOK_PIPE, TOK_AMP,
    TOK_GT, TOK_LT, TOK_DGT, TOK_DLT, TOK_AMP_GT,
    TOK_EQUALS, TOK_LPAREN, TOK_RPAREN, TOK_LBRACE,
    TOK_RBRACE, TOK_LBRACKET, TOK_RBRACE_BRACKET,
    TOK_DOLLAR, TOK_BACKTICK, TOK_EOF
} token_type_t;

typedef struct {
    token_type_t type;
    char         value[256];
} token_t;

typedef enum {
    NODE_COMMAND, NODE_PIPELINE, NODE_AND, NODE_OR,
    NODE_SEQUENCE, NODE_IF, NODE_WHILE, NODE_FOR,
    NODE_FUNCTION, NODE_ASSIGN, NODE_SUBSHELL,
    NODE_REDIR_IN, NODE_REDIR_OUT, NODE_REDIR_APPEND,
    NODE_VAR, NODE_LITERAL, NODE_BUILTIN,
    NODE_CASE, NODE_SELECT, NODE_UNTIL
} node_type_t;

typedef struct ast_node {
    node_type_t type;
    char        value[256];
    struct ast_node* left;
    struct ast_node* right;
    struct ast_node* condition;
    struct ast_node* body;
    struct ast_node* else_body;
    struct ast_node* next;
    char        args[SCRIPT_MAX_ARGS][256];
    uint32_t    arg_count;
    char        redirect_in[256];
    char        redirect_out[256];
    int         redirect_append;
    int         background;
} ast_node_t;

typedef struct {
    char name[64];
    char value[1024];
    int  exported;
} script_var_t;

typedef struct {
    char        name[64];
    char        body[4096];
    char        params[SCRIPT_MAX_ARGS][64];
    uint32_t    param_count;
    int         defined;
} script_func_t;

typedef struct {
    script_var_t  vars[SCRIPT_MAX_VARS];
    uint32_t      num_vars;
    script_func_t funcs[SCRIPT_MAX_FUNCS];
    uint32_t      num_funcs;
    uint32_t      last_return;
    int           running;
    uint32_t      line_number;
    char          current_script[4096];
    ast_node_t*   ast;
} script_state_t;

/* Tokenizer */
int      script_tokenize(const char* input, token_t* tokens, uint32_t max_tokens);
const char* token_type_name(token_type_t type);

/* Parser */
ast_node_t* script_parse(const char* source);
ast_node_t* script_parse_line(const char* line);
void        script_free_ast(ast_node_t* node);

/* Interpreter */
int      script_execute(script_state_t* state, const char* source);
int      script_execute_line(script_state_t* state, const char* line);
int      script_execute_node(script_state_t* state, ast_node_t* node);
int      script_run_file(script_state_t* state, const char* filename);

/* Built-in commands */
int      script_builtin_exit(script_state_t* state, int argc, char** argv);
int      script_builtin_echo(script_state_t* state, int argc, char** argv);
int      script_builtin_cd(script_state_t* state, int argc, char** argv);
int      script_builtin_set(script_state_t* state, int argc, char** argv);
int      script_builtin_unset(script_state_t* state, int argc, char** argv);
int      script_builtin_export(script_state_t* state, int argc, char** argv);
int      script_builtin_test(script_state_t* state, int argc, char** argv);
int      script_builtin_return(script_state_t* state, int argc, char** argv);
int      script_builtin_source(script_state_t* state, int argc, char** argv);
int      script_builtin_local(script_state_t* state, int argc, char** argv);

/* Variable management */
int      script_var_set(script_state_t* state, const char* name, const char* value);
char*    script_var_get(script_state_t* state, const char* name);
int      script_var_exists(script_state_t* state, const char* name);
void     script_var_unset(script_state_t* state, const char* name);

/* Function management */
int      script_func_define(script_state_t* state, const char* name,
                            const char* body, char params[][64], uint32_t param_count);
script_func_t* script_func_find(script_state_t* state, const char* name);
int      script_func_call(script_state_t* state, const char* name,
                          int argc, char** argv);

/* String expansion */
int      script_expand_vars(script_state_t* state, const char* input, char* output, uint32_t max);
int      script_expand_command(script_state_t* state, const char* input, char* output, uint32_t max);

/* Condition evaluation */
int      script_test_condition(script_state_t* state, const char* op,
                               const char* left, const char* right);

/* Utility */
void     script_init(script_state_t* state);
int      script_atoi(const char* str);
void     script_itoa(int val, char* str);

#endif
