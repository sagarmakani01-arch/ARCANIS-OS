/**
 * calculator.c — Calculator Implementation
 *
 * Recursive descent parser for mathematical expressions.
 */
#include <arcanis/calculator.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <arcanis/stdio.h>
#include <math.h>

void calc_init(calculator_t* calc) {
    if (!calc) return;
    memset(calc, 0, sizeof(calculator_t));
    calc_set_var(calc, "pi", CALC_PI);
    calc_set_var(calc, "e", CALC_E);
}

/* ---- Variables ---- */

void calc_set_var(calculator_t* calc, const char* name, double value) {
    if (!calc || !name) return;
    for (uint32_t i = 0; i < calc->num_vars; i++) {
        if (string_compare(calc->vars[i].name, name) == 0) {
            calc->vars[i].value = value;
            calc->vars[i].defined = 1;
            return;
        }
    }
    if (calc->num_vars < 32) {
        string_copy(calc->vars[calc->num_vars].name, name, 32);
        calc->vars[calc->num_vars].value = value;
        calc->vars[calc->num_vars].defined = 1;
        calc->num_vars++;
    }
}

double calc_get_var(calculator_t* calc, const char* name) {
    if (!calc || !name) return 0;
    for (uint32_t i = 0; i < calc->num_vars; i++) {
        if (string_compare(calc->vars[i].name, name) == 0)
            return calc->vars[i].value;
    }
    return 0;
}

/* ---- Tokenizer ---- */

static double parse_number(const char* str, const char** end) {
    double result = 0;
    int neg = 0;
    if (*str == '-') { neg = 1; str++; }
    while (*str >= '0' && *str <= '9')
        result = result * 10 + (*str++ - '0');
    if (*str == '.') {
        str++;
        double frac = 0.1;
        while (*str >= '0' && *str <= '9') {
            result += (*str++ - '0') * frac;
            frac *= 0.1;
        }
    }
    if (end) *end = str;
    return neg ? -result : result;
}

int calc_tokenize(calculator_t* calc, const char* expr) {
    if (!calc || !expr) return -1;

    calc->pos = 0;
    const char* p = expr;

    while (*p && calc->pos < CALC_MAX_STACK) {
        while (*p == ' ') p++;
        if (*p == '\0') break;

        calc_token_t* tok = &calc->tokens[calc->pos];

        if ((*p >= '0' && *p <= '9') || (*p == '.' && p[1] >= '0' && p[1] <= '9')) {
            tok->type = TOK_NUM;
            tok->value = parse_number(p, &p);
            calc->pos++;
        } else if (*p == '+') { tok->type = TOK_PLUS; p++; calc->pos++; }
        else if (*p == '-') { tok->type = TOK_MINUS; p++; calc->pos++; }
        else if (*p == '*') { tok->type = TOK_MUL; p++; calc->pos++; }
        else if (*p == '/') { tok->type = TOK_DIV; p++; calc->pos++; }
        else if (*p == '%') { tok->type = TOK_MOD; p++; calc->pos++; }
        else if (*p == '^') { tok->type = TOK_POW; p++; calc->pos++; }
        else if (*p == '(') { tok->type = TOK_LPAREN; p++; calc->pos++; }
        else if (*p == ')') { tok->type = TOK_RPAREN; p++; calc->pos++; }
        else if (*p == ',') { tok->type = TOK_COMMA; p++; calc->pos++; }
        else if ((*p >= 'a' && *p <= 'z') || (*p >= 'A' && *p <= 'Z')) {
            char name[32];
            uint32_t i = 0;
            while ((*p >= 'a' && *p <= 'z') || (*p >= 'A' && *p <= 'Z') ||
                   (*p >= '0' && *p <= '9') || *p == '_')
                name[i++] = *p++;
            name[i] = '\0';

            if (string_compare(name, "sin") == 0) tok->type = TOK_SIN;
            else if (string_compare(name, "cos") == 0) tok->type = TOK_COS;
            else if (string_compare(name, "tan") == 0) tok->type = TOK_TAN;
            else if (string_compare(name, "asin") == 0) tok->type = TOK_ASIN;
            else if (string_compare(name, "acos") == 0) tok->type = TOK_ACOS;
            else if (string_compare(name, "atan") == 0) tok->type = TOK_ATAN;
            else if (string_compare(name, "log") == 0) tok->type = TOK_LOG;
            else if (string_compare(name, "ln") == 0) tok->type = TOK_LN;
            else if (string_compare(name, "sqrt") == 0) tok->type = TOK_SQRT;
            else if (string_compare(name, "abs") == 0) tok->type = TOK_ABS;
            else if (string_compare(name, "floor") == 0) tok->type = TOK_FLOOR;
            else if (string_compare(name, "ceil") == 0) tok->type = TOK_CEIL;
            else {
                tok->type = TOK_VARIABLE;
                string_copy(tok->name, name, 32);
                tok->value = calc_get_var(calc, name);
            }
            calc->pos++;
        } else {
            p++; /* Skip unknown characters */
        }
    }

    calc->tokens[calc->pos].type = TOK_END;
    calc->pos = 0;
    return 0;
}

/* ---- Recursive descent parser ---- */

static calc_token_t* current_token(calculator_t* calc) {
    return &calc->tokens[calc->pos];
}

static void next_token(calculator_t* calc) {
    if (calc->pos < CALC_MAX_STACK) calc->pos++;
}

double calc_parse_primary(calculator_t* calc) {
    calc_token_t* tok = current_token(calc);

    if (tok->type == TOK_NUM) {
        double val = tok->value;
        next_token(calc);
        return val;
    }

    if (tok->type == TOK_VARIABLE) {
        double val = tok->value;
        next_token(calc);
        return val;
    }

    if (tok->type == TOK_LPAREN) {
        next_token(calc);
        double val = calc_parse_addsub(calc);
        if (current_token(calc)->type == TOK_RPAREN)
            next_token(calc);
        return val;
    }

    /* Functions */
    if (tok->type == TOK_SIN || tok->type == TOK_COS || tok->type == TOK_TAN ||
        tok->type == TOK_ASIN || tok->type == TOK_ACOS || tok->type == TOK_ATAN ||
        tok->type == TOK_LOG || tok->type == TOK_LN || tok->type == TOK_SQRT ||
        tok->type == TOK_ABS || tok->type == TOK_FLOOR || tok->type == TOK_CEIL) {
        calc_token_type_t func = tok->type;
        next_token(calc);
        if (current_token(calc)->type == TOK_LPAREN) next_token(calc);
        double arg = calc_parse_addsub(calc);
        if (current_token(calc)->type == TOK_RPAREN) next_token(calc);
        switch (func) {
            case TOK_SIN:   return calc_func_sin(arg);
            case TOK_COS:   return calc_func_cos(arg);
            case TOK_TAN:   return calc_func_tan(arg);
            case TOK_ASIN:  return calc_func_asin(arg);
            case TOK_ACOS:  return calc_func_acos(arg);
            case TOK_ATAN:  return calc_func_atan(arg);
            case TOK_LOG:   return calc_func_log(arg);
            case TOK_LN:    return calc_func_ln(arg);
            case TOK_SQRT:  return calc_func_sqrt(arg);
            case TOK_ABS:   return calc_func_abs(arg);
            case TOK_FLOOR: return calc_func_floor(arg);
            case TOK_CEIL:  return calc_func_ceil(arg);
            default:        return 0;
        }
    }

    /* Unary minus */
    if (tok->type == TOK_MINUS) {
        next_token(calc);
        return -calc_parse_primary(calc);
    }

    /* Unary plus */
    if (tok->type == TOK_PLUS) {
        next_token(calc);
        return calc_parse_primary(calc);
    }

    return 0;
}

double calc_parse_power(calculator_t* calc) {
    double left = calc_parse_primary(calc);
    while (current_token(calc)->type == TOK_POW) {
        next_token(calc);
        double right = calc_parse_primary(calc);
        left = pow(left, right);
    }
    return left;
}

double calc_parse_muldiv(calculator_t* calc) {
    double left = calc_parse_power(calc);
    while (current_token(calc)->type == TOK_MUL ||
           current_token(calc)->type == TOK_DIV ||
           current_token(calc)->type == TOK_MOD) {
        calc_token_type_t op = current_token(calc)->type;
        next_token(calc);
        double right = calc_parse_power(calc);
        if (op == TOK_MUL) left *= right;
        else if (op == TOK_DIV) left /= right;
        else if (op == TOK_MOD) left = fmod(left, right);
    }
    return left;
}

double calc_parse_addsub(calculator_t* calc) {
    double left = calc_parse_muldiv(calc);
    while (current_token(calc)->type == TOK_PLUS ||
           current_token(calc)->type == TOK_MINUS) {
        calc_token_type_t op = current_token(calc)->type;
        next_token(calc);
        double right = calc_parse_muldiv(calc);
        if (op == TOK_PLUS) left += right;
        else left -= right;
    }
    return left;
}

double calc_eval_expr(calculator_t* calc) {
    return calc_parse_addsub(calc);
}

double calc_eval(calculator_t* calc, const char* expr) {
    if (!calc || !expr) return 0;

    string_copy(calc->expr, expr, CALC_MAX_EXPR);
    calc_tokenize(calc, expr);
    calc->last_result = calc_eval_expr(calc);
    return calc->last_result;
}

/* ---- Math functions ---- */

double calc_func_sin(double x)   { return sin(x); }
double calc_func_cos(double x)   { return cos(x); }
double calc_func_tan(double x)   { return tan(x); }
double calc_func_asin(double x)  { return asin(x); }
double calc_func_acos(double x)  { return acos(x); }
double calc_func_atan(double x)  { return atan(x); }
double calc_func_log(double x)   { return log10(x); }
double calc_func_ln(double x)    { return log(x); }
double calc_func_sqrt(double x)  { return sqrt(x); }
double calc_func_abs(double x)   { return fabs(x); }
double calc_func_floor(double x) { return floor(x); }
double calc_func_ceil(double x)  { return ceil(x); }
