#ifndef ARCANIS_COMPILER_H
#define ARCANIS_COMPILER_H

#include "vm.h"
#include "bytecode.h"
#include <stdint.h>
#include <stdbool.h>

typedef enum {
    TOKEN_EOF,
    TOKEN_ERROR,
    TOKEN_IDENTIFIER,
    TOKEN_NUMBER,
    TOKEN_STRING,
    TOKEN_INT,
    TOKEN_FLOAT,
    TOKEN_NIL,
    TOKEN_TRUE,
    TOKEN_FALSE,
    TOKEN_AND,
    TOKEN_OR,
    TOKEN_NOT,
    TOKEN_IF,
    TOKEN_ELSE,
    TOKEN_WHILE,
    TOKEN_FOR,
    TOKEN_FUN,
    TOKEN_VAR,
    TOKEN_LET,
    TOKEN_CONST,
    TOKEN_RETURN,
    TOKEN_CLASS,
    TOKEN_SUPER,
    TOKEN_THIS,
    TOKEN_IMPORT,
    TOKEN_EXPORT,
    TOKEN_MODULE,
    TOKEN_SWITCH,
    TOKEN_CASE,
    TOKEN_DEFAULT,
    TOKEN_BREAK,
    TOKEN_CONTINUE,
    TOKEN_TRY,
    TOKEN_CATCH,
    TOKEN_FINALLY,
    TOKEN_THROW,
    TOKEN_NEW,
    TOKEN_DELETE,
    TOKEN_DEBUGGER,
    TOKEN_LEFT_PAREN,
    TOKEN_RIGHT_PAREN,
    TOKEN_LEFT_BRACE,
    TOKEN_RIGHT_BRACE,
    TOKEN_LEFT_BRACKET,
    TOKEN_RIGHT_BRACKET,
    TOKEN_COMMA,
    TOKEN_DOT,
    TOKEN_SEMICOLON,
    TOKEN_COLON,
    TOKEN_ARROW,
    TOKEN_PLUS,
    TOKEN_MINUS,
    TOKEN_STAR,
    TOKEN_SLASH,
    TOKEN_PERCENT,
    TOKEN_EQ,
    TOKEN_EQ_EQ,
    TOKEN_BANG,
    TOKEN_BANG_EQ,
    TOKEN_LT,
    TOKEN_GT,
    TOKEN_LE,
    TOKEN_GE,
    TOKEN_AND_AND,
    TOKEN_OR_OR,
} TokenType;

typedef struct {
    TokenType type;
    const char* start;
    uint32_t length;
    uint32_t line;
} Token;

typedef struct Compiler Compiler;

typedef enum {
    PREC_NONE,
    PREC_ASSIGNMENT,
    PREC_OR,
    PREC_AND,
    PREC_EQUALITY,
    PREC_COMPARISON,
    PREC_TERM,
    PREC_FACTOR,
    PREC_UNARY,
    PREC_CALL,
    PREC_PRIMARY
} Precedence;

typedef void (*ParseFn)(Compiler* compiler, bool canAssign);

typedef struct {
    ParseFn prefix;
    ParseFn infix;
    Precedence precedence;
} ParseRule;

typedef struct {
    Token name;
    int32_t depth;
    bool isCaptured;
} Local;

typedef struct {
    uint8_t index;
    bool isLocal;
} Upvalue;

typedef enum {
    TYPE_FUNCTION,
    TYPE_SCRIPT,
    TYPE_METHOD,
    TYPE_INITIALIZER,
} FunctionType;

struct Compiler {
    Compiler* enclosing;
    ObjFunction* function;
    FunctionType type;
    Local locals[256];
    uint32_t localCount;
    Upvalue upvalues[256];
    uint32_t upvalueCount;
    uint32_t scopeDepth;
};

typedef struct {
    const char* source;
    uint32_t sourceLen;
    uint32_t currentPos;
    uint32_t currentLine;
    Token current;
    Token previous;
    bool hadError;
    bool panicMode;
    VM* vm;
} Parser;

ObjFunction* compile(VM* vm, const char* source, uint32_t sourceLen);

#endif
