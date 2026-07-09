#include "compiler.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static Parser* parser = NULL;
static Compiler* current = NULL;

static void advance(void);
static void consume(TokenType type, const char* msg);
static bool matchToken(TokenType type);
static void emitByte(uint32_t instr);
static void emitBytes(uint32_t op, uint32_t arg);
static uint32_t emitJump(uint32_t op);
static void patchJump(uint32_t offset);
static void emitLoop(uint32_t loopStart);
static uint32_t makeConstant(Value value);
static void expression(void);
static void statement(void);
static void declaration(void);

static Token synthToken(const char* s, uint32_t len) {
    Token t; memset(&t, 0, sizeof(Token));
    t.type = TOKEN_IDENTIFIER; t.start = s; t.length = len; return t;
}

static int kwType(const char* s, uint32_t len) {
    switch (len) {
        case 2: if (!memcmp(s,"if",2)) return TOKEN_IF; if (!memcmp(s,"or",2)) return TOKEN_OR; break;
        case 3: if (!memcmp(s,"and",3)) return TOKEN_AND; if (!memcmp(s,"not",3)) return TOKEN_NOT;
                if (!memcmp(s,"var",3)) return TOKEN_VAR; if (!memcmp(s,"let",3)) return TOKEN_LET;
                if (!memcmp(s,"for",3)) return TOKEN_FOR; if (!memcmp(s,"try",3)) return TOKEN_TRY; break;
        case 4: if (!memcmp(s,"true",4)) return TOKEN_TRUE; if (!memcmp(s,"nil",3)) return TOKEN_NIL;
                if (!memcmp(s,"else",4)) return TOKEN_ELSE; if (!memcmp(s,"this",4)) return TOKEN_THIS;
                if (!memcmp(s,"fun",3)) return TOKEN_FUN; if (!memcmp(s,"case",4)) return TOKEN_CASE; break;
        case 5: if (!memcmp(s,"false",5)) return TOKEN_FALSE; if (!memcmp(s,"while",5)) return TOKEN_WHILE;
                if (!memcmp(s,"const",5)) return TOKEN_CONST; if (!memcmp(s,"super",5)) return TOKEN_SUPER;
                if (!memcmp(s,"class",5)) return TOKEN_CLASS; if (!memcmp(s,"break",5)) return TOKEN_BREAK;
                if (!memcmp(s,"throw",5)) return TOKEN_THROW; break;
        case 6: if (!memcmp(s,"return",6)) return TOKEN_RETURN; if (!memcmp(s,"import",6)) return TOKEN_IMPORT;
                if (!memcmp(s,"export",6)) return TOKEN_EXPORT; if (!memcmp(s,"switch",6)) return TOKEN_SWITCH;
                if (!memcmp(s,"delete",6)) return TOKEN_DELETE; break;
        case 7: if (!memcmp(s,"default",7)) return TOKEN_DEFAULT; if (!memcmp(s,"finally",7)) return TOKEN_FINALLY; break;
        case 8: if (!memcmp(s,"continue",8)) return TOKEN_CONTINUE; if (!memcmp(s,"debugger",8)) return TOKEN_DEBUGGER; break;
    }
    return TOKEN_IDENTIFIER;
}

static char peek(void) { return parser->source[parser->currentPos]; }

static void skipWS(void) {
    for (;;) {
        char c = peek();
        if (c == ' ' || c == '\r' || c == '\t') { parser->currentPos++; }
        else if (c == '\n') { parser->currentLine++; parser->currentPos++; }
        else if (c == '/') {
            if (parser->source[parser->currentPos+1] == '/') {
                while (parser->currentPos < parser->sourceLen && peek() != '\n') parser->currentPos++;
            } else if (parser->source[parser->currentPos+1] == '*') {
                parser->currentPos += 2;
                while (parser->currentPos < parser->sourceLen) {
                    if (peek() == '\n') parser->currentLine++;
                    if (peek() == '*' && parser->source[parser->currentPos+1] == '/') { parser->currentPos+=2; break; }
                    parser->currentPos++;
                }
            } else return;
        } else return;
    }
}

static void advance(void) {
    parser->previous = parser->current;
    if (parser->current.type == TOKEN_EOF) return;
    skipWS();
    parser->current.start = parser->source + parser->currentPos;
    parser->current.length = 0;
    parser->current.line = parser->currentLine;
    char c = parser->source[parser->currentPos++];
    switch (c) {
        case '\0': parser->current.type = TOKEN_EOF; break;
        case '(': parser->current.type = TOKEN_LEFT_PAREN; break;
        case ')': parser->current.type = TOKEN_RIGHT_PAREN; break;
        case '{': parser->current.type = TOKEN_LEFT_BRACE; break;
        case '}': parser->current.type = TOKEN_RIGHT_BRACE; break;
        case '[': parser->current.type = TOKEN_LEFT_BRACKET; break;
        case ']': parser->current.type = TOKEN_RIGHT_BRACKET; break;
        case ',': parser->current.type = TOKEN_COMMA; break;
        case '.': parser->current.type = TOKEN_DOT; break;
        case ';': parser->current.type = TOKEN_SEMICOLON; break;
        case ':': parser->current.type = TOKEN_COLON; break;
        case '+': parser->current.type = TOKEN_PLUS; break;
        case '-': parser->current.type = TOKEN_MINUS; break;
        case '*': parser->current.type = TOKEN_STAR; break;
        case '/': parser->current.type = TOKEN_SLASH; break;
        case '%': parser->current.type = TOKEN_PERCENT; break;
        case '!': parser->current.type = (peek()=='=')?(parser->currentPos++,TOKEN_BANG_EQ):TOKEN_BANG; break;
        case '=': parser->current.type = (peek()=='=')?(parser->currentPos++,TOKEN_EQ_EQ):TOKEN_EQ; break;
        case '<': parser->current.type = (peek()=='=')?(parser->currentPos++,TOKEN_LE):TOKEN_LT; break;
        case '>': parser->current.type = (peek()=='=')?(parser->currentPos++,TOKEN_GE):TOKEN_GT; break;
        case '&': if (peek()=='&') { parser->currentPos++; parser->current.type=TOKEN_AND_AND; } else parser->current.type=TOKEN_ERROR; break;
        case '|': if (peek()=='|') { parser->currentPos++; parser->current.type=TOKEN_OR_OR; } else parser->current.type=TOKEN_ERROR; break;
        case '"': case '\'': {
            char q = c;
            while (parser->currentPos < parser->sourceLen && parser->source[parser->currentPos] != q) {
                if (parser->source[parser->currentPos] == '\n') parser->currentLine++;
                if (parser->source[parser->currentPos] == '\\') parser->currentPos++;
                parser->currentPos++;
            }
            if (parser->currentPos < parser->sourceLen) parser->currentPos++;
            parser->current.type = TOKEN_STRING;
            parser->current.length = parser->currentPos - parser->current.start;
            break;
        }
        default:
            if (c >= '0' && c <= '9') {
                bool flt = false;
                while (parser->currentPos < parser->sourceLen &&
                    ((peek()>='0'&&peek()<='9')||peek()=='.')) {
                    if (peek() == '.') flt = true;
                    parser->currentPos++;
                }
                parser->current.type = flt ? TOKEN_FLOAT : TOKEN_INT;
                parser->current.length = parser->currentPos - parser->current.start;
            } else if ((c>='a'&&c<='z')||(c>='A'&&c<='Z')||c=='_') {
                while (parser->currentPos < parser->sourceLen &&
                    ((peek()>='a'&&peek()<='z')||(peek()>='A'&&peek()<='Z')||
                     (peek()>='0'&&peek()<='9')||peek()=='_'))
                    parser->currentPos++;
                parser->current.length = parser->currentPos - parser->current.start;
                parser->current.type = (TokenType)kwType(parser->current.start, parser->current.length);
            } else parser->current.type = TOKEN_ERROR;
            break;
    }
}

static void consume(TokenType type, const char* msg) {
    if (parser->current.type == type) { advance(); return; }
    fprintf(stderr, "Error line %d: %s\n", parser->currentLine, msg);
    parser->hadError = true;
}

static bool matchToken(TokenType type) {
    if (parser->current.type != type) return false;
    advance(); return true;
}

static void errAt(const char* msg) {
    if (parser->panicMode) return;
    parser->panicMode = true;
    fprintf(stderr, "Error line %d: %s\n", parser->previous.line, msg);
    parser->hadError = true;
}

static void sync(void) {
    parser->panicMode = false;
    while (parser->current.type != TOKEN_EOF) {
        if (parser->previous.type == TOKEN_SEMICOLON) return;
        switch (parser->current.type) {
            case TOKEN_CLASS: case TOKEN_FUN: case TOKEN_VAR: case TOKEN_LET:
            case TOKEN_FOR: case TOKEN_IF: case TOKEN_WHILE: case TOKEN_RETURN:
            case TOKEN_IMPORT: case TOKEN_EXPORT: return;
            default: advance();
        }
    }
}

static void emitByte(uint32_t instr) {
    ObjFunction* fn = current->function;
    if (fn->bytecodeLen >= fn->bytecodeCap) {
        uint32_t oc = fn->bytecodeCap;
        fn->bytecodeCap = oc < 8 ? 8 : oc * 2;
        fn->bytecode = realloc(fn->bytecode, fn->bytecodeCap * sizeof(uint32_t));
        fn->lines = realloc(fn->lines, fn->bytecodeCap * sizeof(uint32_t));
    }
    fn->bytecode[fn->bytecodeLen] = instr;
    fn->lines[fn->bytecodeLen] = parser->currentLine;
    fn->bytecodeLen++;
}

static void emitBytes(uint32_t op, uint32_t arg) { emitByte(makeOp(op, arg)); }

static uint32_t makeConstant(Value value) {
    ObjFunction* fn = current->function;
    for (uint32_t i = 0; i < fn->constants.count; i++)
        if (valuesEqual(fn->constants.values[i], value)) return i;
    writeValueArray(&fn->constants, value);
    return fn->constants.count - 1;
}

static uint32_t emitJump(uint32_t op) {
    emitBytes(op, 0xFFFF);
    return current->function->bytecodeLen - 1;
}

static void patchJump(uint32_t offset) {
    uint32_t jmp = current->function->bytecodeLen - offset - 1;
    current->function->bytecode[offset] = makeOp(getOp(current->function->bytecode[offset]), jmp);
}

static void emitLoop(uint32_t loopStart) {
    emitBytes(OP_LOOP, current->function->bytecodeLen - loopStart + 1);
}

static uint32_t identConst(Token* name) {
    char* s = malloc(name->length + 1);
    memcpy(s, name->start, name->length); s[name->length] = '\0';
    Value v = STRING_VAL((ObjString*)(uintptr_t)s);
    uint32_t idx = makeConstant(v); free(s); return idx;
}

static int resolveLocal(Token* name) {
    for (int i = (int)current->localCount - 1; i >= 0; i--) {
        Local* l = &current->locals[i];
        if (l->name.length == name->length && !memcmp(l->name.start, name->start, name->length)) {
            if (l->depth == -1) errAt("Cannot read local in initializer");
            return i;
        }
    }
    return -1;
}

static int addUpvalue(uint8_t index, bool isLocal) {
    for (uint32_t i = 0; i < current->upvalueCount; i++)
        if (current->upvalues[i].index == index && current->upvalues[i].isLocal == isLocal)
            return (int)i;
    if (current->upvalueCount >= 256) return -1;
    current->upvalues[current->upvalueCount].index = index;
    current->upvalues[current->upvalueCount].isLocal = isLocal;
    return (int)current->upvalueCount++;
}

static int resolveUpvalue(Token* name) {
    if (!current->enclosing) return -1;
    int local = resolveLocal(name);
    if (local != -1) {
        current->enclosing->locals[local].isCaptured = true;
        return addUpvalue((uint8_t)local, true);
    }
    int upvalue = resolveUpvalue(name);
    if (upvalue != -1) return addUpvalue((uint8_t)upvalue, false);
    return -1;
}

static void addLocal(Token name) {
    if (current->localCount >= 256) { errAt("Too many locals"); return; }
    current->locals[current->localCount].name = name;
    current->locals[current->localCount].depth = -1;
    current->locals[current->localCount].isCaptured = false;
    current->localCount++;
}

static void declareVar(void) {
    if (current->scopeDepth == 0) return;
    Token* name = &parser->previous;
    for (int i = (int)current->localCount - 1; i >= 0; i--) {
        Local* l = &current->locals[i];
        if (l->depth != -1 && l->depth < (int32_t)current->scopeDepth) break;
        if (l->name.length == name->length && !memcmp(l->name.start, name->start, name->length))
            errAt("Variable already declared");
    }
    addLocal(*name);
}

static uint32_t parseVar(const char* msg) {
    consume(TOKEN_IDENTIFIER, msg);
    declareVar();
    if (current->scopeDepth > 0) return 0;
    return identConst(&parser->previous);
}

static void markInit(void) {
    if (current->scopeDepth == 0) return;
    current->locals[current->localCount - 1].depth = (int32_t)current->scopeDepth;
}

static void defineVar(uint32_t global) {
    if (current->scopeDepth > 0) { markInit(); return; }
    emitBytes(OP_DEFINE_GLOBAL, global);
}

static void beginScope(void) { current->scopeDepth++; }
static void endScope(void) {
    current->scopeDepth--;
    while (current->localCount > 0 &&
           current->locals[current->localCount-1].depth > (int32_t)current->scopeDepth) {
        if (current->locals[current->localCount-1].isCaptured) emitByte(OP_CLOSE_UPVALUE);
        else emitByte(OP_POP);
        current->localCount--;
    }
}

static void parsePrec(Precedence prec);

typedef void (*ParseFn)(bool canAssign);
typedef struct { ParseFn prefix; ParseFn infix; Precedence prec; } Rule;

static void grouping(bool ca);
static void unary(bool ca);
static void binary(bool ca);
static void callExpr(bool ca);
static void dotExpr(bool ca);
static void arrLit(bool ca);
static void mapLit(bool ca);
static void numLit(bool ca);
static void strLit(bool ca);
static void nilLit(bool ca);
static void trueLit(bool ca);
static void falseLit(bool ca);
static void thisLit(bool ca);
static void superLit(bool ca);
static void varExpr(bool ca);

static Rule rules[] = {
    [TOKEN_LEFT_PAREN] =   {grouping, callExpr, PREC_CALL},
    [TOKEN_LEFT_BRACKET] = {arrLit, NULL, PREC_NONE},
    [TOKEN_LEFT_BRACE] =   {mapLit, NULL, PREC_NONE},
    [TOKEN_DOT] =          {NULL, dotExpr, PREC_CALL},
    [TOKEN_MINUS] =        {unary, binary, PREC_TERM},
    [TOKEN_PLUS] =         {NULL, binary, PREC_TERM},
    [TOKEN_STAR] =         {NULL, binary, PREC_FACTOR},
    [TOKEN_SLASH] =        {NULL, binary, PREC_FACTOR},
    [TOKEN_PERCENT] =      {NULL, binary, PREC_FACTOR},
    [TOKEN_BANG] =         {unary, NULL, PREC_NONE},
    [TOKEN_BANG_EQ] =      {NULL, binary, PREC_EQUALITY},
    [TOKEN_EQ_EQ] =        {NULL, binary, PREC_EQUALITY},
    [TOKEN_LT] =           {NULL, binary, PREC_COMPARISON},
    [TOKEN_GT] =           {NULL, binary, PREC_COMPARISON},
    [TOKEN_LE] =           {NULL, binary, PREC_COMPARISON},
    [TOKEN_GE] =           {NULL, binary, PREC_COMPARISON},
    [TOKEN_AND_AND] =      {NULL, binary, PREC_AND},
    [TOKEN_OR_OR] =        {NULL, binary, PREC_OR},
    [TOKEN_IDENTIFIER] =   {varExpr, NULL, PREC_NONE},
    [TOKEN_INT] =          {numLit, NULL, PREC_NONE},
    [TOKEN_FLOAT] =        {numLit, NULL, PREC_NONE},
    [TOKEN_STRING] =       {strLit, NULL, PREC_NONE},
    [TOKEN_NIL] =          {nilLit, NULL, PREC_NONE},
    [TOKEN_TRUE] =         {trueLit, NULL, PREC_NONE},
    [TOKEN_FALSE] =        {falseLit, NULL, PREC_NONE},
    [TOKEN_THIS] =         {thisLit, NULL, PREC_NONE},
    [TOKEN_SUPER] =        {superLit, NULL, PREC_NONE},
};

static void varExpr(bool ca) {
    Token name = parser->previous;
    int arg = resolveLocal(&name);
    uint32_t getOp, setOp;
    if (arg != -1) { getOp = OP_LOAD_LOCAL; setOp = OP_STORE_LOCAL; }
    else if ((arg = resolveUpvalue(&name)) != -1) { getOp = OP_LOAD_UPVALUE; setOp = OP_STORE_UPVALUE; }
    else { arg = (int)identConst(&name); getOp = OP_LOAD_GLOBAL; setOp = OP_STORE_GLOBAL; }
    if (ca && matchToken(TOKEN_EQ)) { expression(); emitBytes(setOp, (uint32_t)arg); }
    else emitBytes(getOp, (uint32_t)arg);
}

static void grouping(bool ca) { (void)ca; expression(); consume(TOKEN_RIGHT_PAREN,"Expected ')'"); }

static void numLit(bool ca) {
    (void)ca;
    double v = strtod(parser->previous.start, NULL);
    bool flt = parser->previous.type == TOKEN_FLOAT;
    emitBytes(OP_LOAD_CONST, makeConstant(flt ? FLOAT_VAL(v) : INT_VAL((int64_t)v)));
}

static void strLit(bool ca) {
    (void)ca;
    Token* t = &parser->previous;
    uint32_t rawLen = t->length - 2;
    const char* s = t->start + 1;
    char* buf = malloc(rawLen + 1);
    uint32_t j = 0;
    for (uint32_t i = 0; i < rawLen; i++) {
        if (s[i] == '\\') { i++;
            switch (s[i]) { case 'n': buf[j++]='\n'; break; case 't': buf[j++]='\t'; break;
                case 'r': buf[j++]='\r'; break; default: buf[j++]=s[i]; break; }
        } else buf[j++] = s[i];
    }
    buf[j] = '\0';
    emitBytes(OP_LOAD_CONST, makeConstant(STRING_VAL((ObjString*)(uintptr_t)buf)));
    free(buf);
}

static void nilLit(bool ca) { (void)ca; emitByte(OP_LOAD_NIL); }
static void trueLit(bool ca) { (void)ca; emitByte(OP_LOAD_TRUE); }
static void falseLit(bool ca) { (void)ca; emitByte(OP_LOAD_FALSE); }

static void unary(bool ca) {
    (void)ca;
    TokenType op = parser->previous.type;
    parsePrec(PREC_UNARY);
    switch (op) { case TOKEN_BANG: emitByte(OP_NOT); break; case TOKEN_MINUS: emitByte(OP_NEG); break; default: break; }
}

static void binary(bool ca) {
    (void)ca;
    TokenType op = parser->previous.type;
    parsePrec((Precedence)(rules[op].prec + 1));
    switch (op) {
        case TOKEN_PLUS: emitByte(OP_ADD); break; case TOKEN_MINUS: emitByte(OP_SUB); break;
        case TOKEN_STAR: emitByte(OP_MUL); break; case TOKEN_SLASH: emitByte(OP_DIV); break;
        case TOKEN_PERCENT: emitByte(OP_MOD); break; case TOKEN_EQ_EQ: emitByte(OP_EQ); break;
        case TOKEN_BANG_EQ: emitByte(OP_NE); break; case TOKEN_LT: emitByte(OP_LT); break;
        case TOKEN_GT: emitByte(OP_GT); break; case TOKEN_LE: emitByte(OP_LE); break;
        case TOKEN_GE: emitByte(OP_GE); break; case TOKEN_AND_AND: emitByte(OP_AND); break;
        case TOKEN_OR_OR: emitByte(OP_OR); break; default: break;
    }
}

static void callExpr(bool ca) {
    (void)ca;
    uint32_t ac = 0;
    if (!matchToken(TOKEN_RIGHT_PAREN)) {
        do { expression(); ac++; } while (matchToken(TOKEN_COMMA));
        consume(TOKEN_RIGHT_PAREN, "Expected ')'");
    }
    emitBytes(OP_CALL, ac);
}

static void dotExpr(bool ca) {
    consume(TOKEN_IDENTIFIER, "Expected property name");
    uint32_t name = identConst(&parser->previous);
    if (ca && matchToken(TOKEN_EQ)) { expression(); emitBytes(OP_PROP_SET, name); }
    else if (matchToken(TOKEN_LEFT_PAREN)) {
        uint32_t ac = 0;
        if (!matchToken(TOKEN_RIGHT_PAREN)) {
            do { expression(); ac++; } while (matchToken(TOKEN_COMMA));
            consume(TOKEN_RIGHT_PAREN, "Expected ')'");
        }
        emitBytes(makeOp(OP_INVOKE, ac), name);
    } else emitBytes(OP_PROP_GET, name);
}

static void arrLit(bool ca) {
    (void)ca;
    uint32_t cnt = 0;
    if (!matchToken(TOKEN_RIGHT_BRACKET)) {
        do { expression(); cnt++; } while (matchToken(TOKEN_COMMA));
        consume(TOKEN_RIGHT_BRACKET, "Expected ']'");
    }
    emitBytes(OP_NEW_ARRAY, cnt);
}

static void mapLit(bool ca) {
    (void)ca;
    uint32_t cnt = 0;
    if (!matchToken(TOKEN_RIGHT_BRACE)) {
        do { expression(); consume(TOKEN_COLON,"Expected ':'"); expression(); cnt++; }
        while (matchToken(TOKEN_COMMA));
        consume(TOKEN_RIGHT_BRACE, "Expected '}'");
    }
    emitBytes(OP_NEW_MAP, cnt);
}

static void thisLit(bool ca) {
    (void)ca;
    if (current->type != TYPE_METHOD && current->type != TYPE_INITIALIZER)
        errAt("Cannot use 'this' outside method");
    varExpr(false);
}

static void superLit(bool ca) {
    (void)ca;
    consume(TOKEN_DOT, "Expected '.' after 'super'");
    consume(TOKEN_IDENTIFIER, "Expected super method name");
    uint32_t name = identConst(&parser->previous);
    varExpr(false);
    emitBytes(OP_GET_SUPER, name);
}

static void parsePrec(Precedence prec) {
    advance();
    ParseFn prefix = rules[parser->previous.type].prefix;
    if (!prefix) { errAt("Expected expression"); return; }
    bool ca = prec <= PREC_ASSIGNMENT;
    prefix(ca);
    while (prec <= rules[parser->current.type].prec) {
        advance();
        ParseFn infix = rules[parser->previous.type].infix;
        if (!infix) return;
        infix(ca);
    }
    if (ca && matchToken(TOKEN_EQ)) errAt("Invalid assignment target");
}

static void expression(void) { parsePrec(PREC_ASSIGNMENT); }

static void block(void) {
    while (parser->current.type != TOKEN_RIGHT_BRACE && parser->current.type != TOKEN_EOF)
        declaration();
    consume(TOKEN_RIGHT_BRACE, "Expected '}'");
}

static void functionDef(FunctionType type) {
    Compiler inner;
    memset(&inner, 0, sizeof(Compiler));
    inner.enclosing = current;
    inner.type = type;
    inner.function = allocateFunction(&parser->vm->memory);
    if (!inner.function) return;
    current = &inner;
    beginScope();
    consume(TOKEN_LEFT_PAREN, "Expected '('");
    if (!matchToken(TOKEN_RIGHT_PAREN)) {
        do { inner.function->arity++; uint32_t p = parseVar("Expected param"); defineVar(p); }
        while (matchToken(TOKEN_COMMA));
        consume(TOKEN_RIGHT_PAREN, "Expected ')'");
    }
    consume(TOKEN_LEFT_BRACE, "Expected '{'");
    block();
    emitByte(OP_RETURN);
    ObjFunction* fn = inner.function;
    uint32_t idx = makeConstant(FUNCTION_VAL(fn));
    emitBytes(OP_CLOSURE, idx);
    for (uint32_t i = 0; i < inner.upvalueCount; i++)
        emitByte(makeOp(inner.upvalues[i].isLocal ? 1 : 0, inner.upvalues[i].index));
    current = inner.enclosing;
}

static void funDecl(void) {
    uint32_t g = parseVar("Expected function name");
    markInit();
    functionDef(TYPE_FUNCTION);
    defineVar(g);
}

static void varDecl(void) {
    uint32_t g = parseVar("Expected variable name");
    if (matchToken(TOKEN_EQ)) expression(); else emitByte(OP_LOAD_NIL);
    consume(TOKEN_SEMICOLON, "Expected ';'");
    defineVar(g);
}

static void exprStmt(void) { expression(); consume(TOKEN_SEMICOLON,"Expected ';'"); emitByte(OP_POP); }

static void ifStmt(void) {
    consume(TOKEN_LEFT_PAREN,"Expected '('"); expression(); consume(TOKEN_RIGHT_PAREN,"Expected ')'");
    uint32_t tj = emitJump(OP_JMP_IF_FALSE_POP);
    statement();
    uint32_t ej = emitJump(OP_JMP);
    patchJump(tj);
    if (matchToken(TOKEN_ELSE)) statement();
    patchJump(ej);
}

static void whileStmt(void) {
    uint32_t loop = current->function->bytecodeLen;
    consume(TOKEN_LEFT_PAREN,"Expected '('"); expression(); consume(TOKEN_RIGHT_PAREN,"Expected ')'");
    uint32_t exit = emitJump(OP_JMP_IF_FALSE_POP);
    statement();
    emitLoop(loop);
    patchJump(exit);
}

static void forStmt(void) {
    beginScope();
    consume(TOKEN_LEFT_PAREN,"Expected '('");
    if (matchToken(TOKEN_SEMICOLON));
    else if (matchToken(TOKEN_VAR)||matchToken(TOKEN_LET)) varDecl();
    else exprStmt();
    uint32_t loop = current->function->bytecodeLen;
    uint32_t exit = 0;
    if (!matchToken(TOKEN_SEMICOLON)) { expression(); consume(TOKEN_SEMICOLON,"Expected ';'"); exit = emitJump(OP_JMP_IF_FALSE_POP); }
    if (!matchToken(TOKEN_RIGHT_PAREN)) {
        uint32_t bodyJ = emitJump(OP_JMP);
        uint32_t inc = current->function->bytecodeLen;
        expression(); emitByte(OP_POP);
        consume(TOKEN_RIGHT_PAREN,"Expected ')'");
        emitLoop(loop); loop = inc; patchJump(bodyJ);
    }
    statement();
    emitLoop(loop);
    if (exit) patchJump(exit);
    endScope();
}

static void retStmt(void) {
    if (current->type == TYPE_SCRIPT) errAt("Cannot return from top-level");
    if (matchToken(TOKEN_SEMICOLON)) emitByte(OP_RETURN);
    else {
        if (current->type == TYPE_INITIALIZER) errAt("Cannot return value from init");
        expression(); consume(TOKEN_SEMICOLON,"Expected ';'"); emitByte(OP_RETURN_VALUE);
    }
}

static void classDecl(void) {
    uint32_t g = parseVar("Expected class name");
    markInit();
    if (matchToken(TOKEN_LT)) {
        consume(TOKEN_IDENTIFIER,"Expected superclass name");
        Token sn = parser->previous;
        varExpr(false);
        beginScope(); addLocal(synthToken("super",5)); defineVar(0);
    }
    consume(TOKEN_LEFT_BRACE,"Expected '{'");
    while (!matchToken(TOKEN_RIGHT_BRACE)) {
        consume(TOKEN_IDENTIFIER,"Expected method name");
        uint32_t name = identConst(&parser->previous);
        functionDef(TYPE_METHOD);
        emitBytes(OP_METHOD, name);
    }
    defineVar(g);
}

static void importDecl(void) {
    consume(TOKEN_STRING,"Expected module path");
    uint32_t idx = makeConstant(STRING_VAL((ObjString*)(uintptr_t)parser->previous.start));
    uint32_t modName = identConst(&parser->previous);
    emitBytes(OP_IMPORT, modName);
    consume(TOKEN_SEMICOLON,"Expected ';'");
}

static void exportDecl(void) {
    expression(); consume(TOKEN_SEMICOLON,"Expected ';'");
    emitBytes(OP_EXPORT, 0);
}

static void dbgStmt(void) { emitByte(OP_DEBUG_BREAK); consume(TOKEN_SEMICOLON,"Expected ';'"); }

static void switchStmt(void) {
    consume(TOKEN_LEFT_PAREN,"Expected '('"); expression(); consume(TOKEN_RIGHT_PAREN,"Expected ')'");
    consume(TOKEN_LEFT_BRACE,"Expected '{'");
    uint32_t jumps[64]; uint32_t jc = 0;
    while (parser->current.type == TOKEN_CASE || parser->current.type == TOKEN_DEFAULT) {
        advance();
        if (parser->previous.type == TOKEN_DEFAULT) emitByte(OP_POP);
        else { emitByte(OP_DUP); expression(); emitByte(OP_EQ); emitJump(OP_JMP_IF_FALSE_POP); }
        consume(TOKEN_COLON,"Expected ':'");
        while (parser->current.type != TOKEN_CASE && parser->current.type != TOKEN_DEFAULT &&
               parser->current.type != TOKEN_RIGHT_BRACE && parser->current.type != TOKEN_EOF)
            statement();
        if (jc < 64) jumps[jc++] = emitJump(OP_JMP);
    }
    consume(TOKEN_RIGHT_BRACE,"Expected '}'");
    emitByte(OP_POP);
    for (uint32_t i = 0; i < jc; i++) patchJump(jumps[i]);
}

static void tryStmt(void) {
    consume(TOKEN_LEFT_BRACE,"Expected '{'"); block();
    if (matchToken(TOKEN_CATCH)) {
        consume(TOKEN_LEFT_PAREN,"Expected '('"); consume(TOKEN_IDENTIFIER,"Expected variable");
        uint32_t c = 0; beginScope(); defineVar(c);
        consume(TOKEN_RIGHT_PAREN,"Expected ')'"); consume(TOKEN_LEFT_BRACE,"Expected '{'"); block(); endScope();
    }
    if (matchToken(TOKEN_FINALLY)) { consume(TOKEN_LEFT_BRACE,"Expected '{'"); block(); }
}

static void throwStmt(void) { expression(); consume(TOKEN_SEMICOLON,"Expected ';'"); }

static void statement(void) {
    if (matchToken(TOKEN_IF)) { ifStmt(); }
    else if (matchToken(TOKEN_WHILE)) { whileStmt(); }
    else if (matchToken(TOKEN_FOR)) { forStmt(); }
    else if (matchToken(TOKEN_RETURN)) { retStmt(); }
    else if (matchToken(TOKEN_SWITCH)) { switchStmt(); }
    else if (matchToken(TOKEN_TRY)) { tryStmt(); }
    else if (matchToken(TOKEN_THROW)) { throwStmt(); }
    else if (matchToken(TOKEN_DEBUGGER)) { dbgStmt(); }
    else if (matchToken(TOKEN_LEFT_BRACE)) { beginScope(); block(); endScope(); }
    else { exprStmt(); }
}

static void declaration(void) {
    if (matchToken(TOKEN_CLASS)) { classDecl(); }
    else if (matchToken(TOKEN_FUN)) { funDecl(); }
    else if (matchToken(TOKEN_VAR) || matchToken(TOKEN_LET)) { varDecl(); }
    else if (matchToken(TOKEN_IMPORT)) { importDecl(); }
    else { statement(); }
    if (parser->panicMode) sync();
}

ObjFunction* compile(VM* vm, const char* source, uint32_t sourceLen) {
    Parser p;
    memset(&p, 0, sizeof(Parser));
    p.source = source; p.sourceLen = sourceLen; p.currentLine = 1;
    p.currentPos = 0; p.hadError = false; p.panicMode = false; p.vm = vm;
    parser = &p;

    advance();

    Compiler c;
    memset(&c, 0, sizeof(Compiler));
    c.type = TYPE_SCRIPT;
    c.function = allocateFunction(&vm->memory);
    if (!c.function) return NULL;
    c.function->name = copyString(&vm->memory, "script", 6);
    current = &c;

    while (parser->current.type != TOKEN_EOF) declaration();

    emitByte(OP_RETURN);

    ObjFunction* fn = c.function;
    if (parser->hadError) { free(fn->bytecode); free(fn->lines); freeValueArray(&fn->constants); free(fn); return NULL; }
    return fn;
}
