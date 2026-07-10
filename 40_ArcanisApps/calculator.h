/**
 * calculator.h — Calculator Application
 *
 * Scientific calculator with expression parsing.
 * Supports +, -, *, /, %, ^, sin, cos, tan, log, sqrt.
 */
#ifndef ARCANIS_CALCULATOR_H
#define ARCANIS_CALCULATOR_H

#include <arcanis/types.h>

#define CALC_MAX_EXPR  256
#define CALC_MAX_STACK 64
#define CALC_PI        3.14159265358979323846
#define CALC_E         2.71828182845904523536

typedef enum {
    TOK_NUM, TOK_PLUS, TOK_MINUS, TOK_MUL, TOK_DIV, TOK_MOD,
    TOK_POW, TOK_LPAREN, TOK_RPAREN, TOK_COMMA,
    TOK_SIN, TOK_COS, TOK_TAN, TOK_ASIN, TOK_ACOS, TOK_ATAN,
    TOK_LOG, TOK_LN, TOK_SQRT, TOK_ABS, TOK_FLOOR, TOK_CEIL,
    TOK_VARIABLE, TOK_END
} calc_token_type_t;

typedef struct {
    calc_token_type_t type;
    double value;
    char   name[32];
} calc_token_t;

typedef struct {
    char     name[32];
    double   value;
    int      defined;
} calc_variable_t;

typedef struct {
    calc_token_t tokens[CALC_MAX_STACK];
    uint32_t     pos;
    char         expr[CALC_MAX_EXPR];
    uint32_t     expr_len;
    calc_variable_t vars[32];
    uint32_t     num_vars;
    double       last_result;
    int          error;
    char         error_msg[128];
} calculator_t;

/* Initialize calculator */
void calc_init(calculator_t* calc);

/* Evaluate expression */
double calc_eval(calculator_t* calc, const char* expr);
double calc_eval_expr(calculator_t* calc);

/* Tokenizer */
int    calc_tokenize(calculator_t* calc, const char* expr);

/* Recursive descent parser */
double calc_parse_addsub(calculator_t* calc);
double calc_parse_muldiv(calculator_t* calc);
double calc_parse_power(calculator_t* calc);
double calc_parse_unary(calculator_t* calc);
double calc_parse_primary(calculator_t* calc);

/* Math functions */
double calc_func_sin(double x);
double calc_func_cos(double x);
double calc_func_tan(double x);
double calc_func_asin(double x);
double calc_func_acos(double x);
double calc_func_atan(double x);
double calc_func_log(double x);
double calc_func_ln(double x);
double calc_func_sqrt(double x);
double calc_func_abs(double x);
double calc_func_floor(double x);
double calc_func_ceil(double x);

/* Variable management */
void   calc_set_var(calculator_t* calc, const char* name, double value);
double calc_get_var(calculator_t* calc, const char* name);

/* History */
void   calc_print_history(calculator_t* calc);

#endif
