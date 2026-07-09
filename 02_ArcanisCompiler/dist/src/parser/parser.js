"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Parser = void 0;
const ast_1 = require("./ast");
const types_1 = require("../types");
const BINARY_PRECEDENCE = {
    '||': 1,
    '&&': 2,
    '==': 3, '!=': 3,
    '<': 4, '>': 4, '<=': 4, '>=': 4,
    '+': 5, '-': 5,
    '*': 6, '/': 6, '%': 6,
};
const UNARY_OPS = {
    '-': types_1.UnaryOp.Negate,
    '!': types_1.UnaryOp.Not,
};
const BINARY_OPS = {
    '+': types_1.BinaryOp.Add,
    '-': types_1.BinaryOp.Subtract,
    '*': types_1.BinaryOp.Multiply,
    '/': types_1.BinaryOp.Divide,
    '%': types_1.BinaryOp.Modulo,
    '==': types_1.BinaryOp.Equal,
    '!=': types_1.BinaryOp.NotEqual,
    '<': types_1.BinaryOp.LessThan,
    '>': types_1.BinaryOp.GreaterThan,
    '<=': types_1.BinaryOp.LessEqual,
    '>=': types_1.BinaryOp.GreaterEqual,
    '&&': types_1.BinaryOp.And,
    '||': types_1.BinaryOp.Or,
    '=': types_1.BinaryOp.Assign,
};
class Parser {
    constructor(tokens, sourceId, errors) {
        this.current = 0;
        this.tokens = tokens;
        this.sourceId = sourceId;
        this.errors = errors;
    }
    parse() {
        const functions = [];
        const statements = [];
        const start = this.peek();
        while (!this.isAtEnd()) {
            if (this.checkKeyword(types_1.Keyword.Fun)) {
                functions.push(this.parseFunctionDecl());
            }
            else {
                statements.push(this.parseStmt());
            }
        }
        const endToken = this.current > 0 ? this.previous() : this.peek();
        const range = this.mergeRange(start.range, endToken.range);
        return new ast_1.Program(range, functions, statements);
    }
    parseFunctionDecl() {
        const start = this.consumeKeyword(types_1.Keyword.Fun, "Expect 'fun' keyword");
        const nameToken = this.consume('IDENTIFIER', 'Expect function name');
        const name = nameToken.lexeme;
        this.consume('OPEN_PAREN', `Expect '(' after function name '${name}'`);
        const params = [];
        if (!this.check('CLOSE_PAREN')) {
            do {
                params.push(this.parseParamDecl());
            } while (this.match('COMMA'));
        }
        this.consume('CLOSE_PAREN', `Expect ')' after parameters`);
        let returnType = types_1.Type.unit();
        if (this.match('COLON')) {
            returnType = this.parseType();
        }
        this.consume('OPEN_BRACE', `Expect '{' before function body`);
        const body = this.parseBlockStmt();
        const end = this.previous();
        return new ast_1.FunctionDecl(this.mergeRange(start.range, end.range), name, params, returnType, body);
    }
    parseParamDecl() {
        const nameToken = this.consume('IDENTIFIER', 'Expect parameter name');
        this.consume('COLON', `Expect ':' after parameter name`);
        const paramType = this.parseType();
        return new ast_1.ParamDecl(nameToken.range, nameToken.lexeme, paramType);
    }
    parseStmt() {
        if (this.checkKeyword(types_1.Keyword.Let))
            return this.parseVarDecl();
        if (this.checkKeyword(types_1.Keyword.If))
            return this.parseIfStmt();
        if (this.checkKeyword(types_1.Keyword.While))
            return this.parseWhileStmt();
        if (this.checkKeyword(types_1.Keyword.Return))
            return this.parseReturnStmt();
        if (this.match('OPEN_BRACE'))
            return this.parseBlockStmt();
        return this.parseExprStmt();
    }
    parseVarDecl() {
        const start = this.consumeKeyword(types_1.Keyword.Let, "Expect 'let' keyword");
        const nameToken = this.consume('IDENTIFIER', 'Expect variable name');
        let varType = types_1.Type.infer();
        if (this.match('COLON')) {
            varType = this.parseType();
        }
        let initializer;
        if (this.matchOperator('=')) {
            initializer = this.parseExpr();
        }
        this.consume('SEMICOLON', "Expect ';' after variable declaration");
        return new ast_1.VarDecl(nameToken.range, nameToken.lexeme, varType, initializer);
    }
    parseBlockStmt() {
        const start = this.previous();
        const statements = [];
        while (!this.check('CLOSE_BRACE') && !this.isAtEnd()) {
            statements.push(this.parseStmt());
        }
        this.consume('CLOSE_BRACE', "Expect '}' after block");
        const end = this.previous();
        return new ast_1.BlockStmt(this.mergeRange(start.range, end.range), statements);
    }
    parseIfStmt() {
        const start = this.consumeKeyword(types_1.Keyword.If, "Expect 'if' keyword");
        this.consume('OPEN_PAREN', "Expect '(' after 'if'");
        const condition = this.parseExpr();
        this.consume('CLOSE_PAREN', "Expect ')' after condition");
        const thenBranch = this.parseStmt();
        let elseBranch;
        if (this.checkKeyword(types_1.Keyword.Else)) {
            this.advance();
            elseBranch = this.parseStmt();
        }
        const end = this.previous();
        return new ast_1.IfStmt(this.mergeRange(start.range, end.range), condition, thenBranch, elseBranch);
    }
    parseWhileStmt() {
        const start = this.consumeKeyword(types_1.Keyword.While, "Expect 'while' keyword");
        this.consume('OPEN_PAREN', "Expect '(' after 'while'");
        const condition = this.parseExpr();
        this.consume('CLOSE_PAREN', "Expect ')' after condition");
        const body = this.parseStmt();
        const end = this.previous();
        return new ast_1.WhileStmt(this.mergeRange(start.range, end.range), condition, body);
    }
    parseReturnStmt() {
        const start = this.consumeKeyword(types_1.Keyword.Return, "Expect 'return' keyword");
        let value;
        if (!this.check('SEMICOLON')) {
            value = this.parseExpr();
        }
        this.consume('SEMICOLON', "Expect ';' after return value");
        const end = this.previous();
        return new ast_1.ReturnStmt(this.mergeRange(start.range, end.range), value);
    }
    parseExprStmt() {
        const expr = this.parseExpr();
        this.consume('SEMICOLON', "Expect ';' after expression");
        return new ast_1.ExprStmt(expr.range, expr);
    }
    parseExpr() {
        return this.parseAssignment();
    }
    parseAssignment() {
        const expr = this.parseLogicalOr();
        if (this.matchOperator('=')) {
            const value = this.parseAssignment();
            if (expr instanceof ast_1.Identifier) {
                return new ast_1.BinaryExpr(this.mergeRange(expr.range, value.range), expr, types_1.BinaryOp.Assign, value);
            }
            this.errors.error(types_1.CompilerStage.Parsing, 'Invalid assignment target', this.previous().range);
        }
        return expr;
    }
    parseLogicalOr() {
        let expr = this.parseLogicalAnd();
        while (this.matchOperator('||')) {
            const op = this.previous();
            const right = this.parseLogicalAnd();
            expr = new ast_1.BinaryExpr(this.mergeRange(expr.range, right.range), expr, types_1.BinaryOp.Or, right);
        }
        return expr;
    }
    parseLogicalAnd() {
        let expr = this.parseEquality();
        while (this.matchOperator('&&')) {
            const op = this.previous();
            const right = this.parseEquality();
            expr = new ast_1.BinaryExpr(this.mergeRange(expr.range, right.range), expr, types_1.BinaryOp.And, right);
        }
        return expr;
    }
    parseEquality() {
        let expr = this.parseComparison();
        while (this.matchOperator('==') || this.matchOperator('!=')) {
            const op = this.previous();
            const right = this.parseComparison();
            const binOp = BINARY_OPS[op.lexeme];
            expr = new ast_1.BinaryExpr(this.mergeRange(expr.range, right.range), expr, binOp, right);
        }
        return expr;
    }
    parseComparison() {
        let expr = this.parseTerm();
        while (this.matchOperator('<') || this.matchOperator('>') ||
            this.matchOperator('<=') || this.matchOperator('>=')) {
            const op = this.previous();
            const right = this.parseTerm();
            const binOp = BINARY_OPS[op.lexeme];
            expr = new ast_1.BinaryExpr(this.mergeRange(expr.range, right.range), expr, binOp, right);
        }
        return expr;
    }
    parseTerm() {
        let expr = this.parseFactor();
        while (this.matchOperator('+') || this.matchOperator('-')) {
            const op = this.previous();
            const right = this.parseFactor();
            const binOp = BINARY_OPS[op.lexeme];
            expr = new ast_1.BinaryExpr(this.mergeRange(expr.range, right.range), expr, binOp, right);
        }
        return expr;
    }
    parseFactor() {
        let expr = this.parseUnary();
        while (this.matchOperator('*') || this.matchOperator('/') || this.matchOperator('%')) {
            const op = this.previous();
            const right = this.parseUnary();
            const binOp = BINARY_OPS[op.lexeme];
            expr = new ast_1.BinaryExpr(this.mergeRange(expr.range, right.range), expr, binOp, right);
        }
        return expr;
    }
    parseUnary() {
        if (this.matchOperator('-') || this.matchOperator('!')) {
            const opToken = this.previous();
            const op = UNARY_OPS[opToken.lexeme];
            const operand = this.parseUnary();
            return new ast_1.UnaryExpr(this.mergeRange(opToken.range, operand.range), op, operand);
        }
        return this.parseCall();
    }
    parseCall() {
        let expr = this.parsePrimary();
        while (true) {
            if (this.match('OPEN_PAREN')) {
                expr = this.finishCall(expr);
            }
            else {
                break;
            }
        }
        return expr;
    }
    finishCall(callee) {
        const args = [];
        if (!this.check('CLOSE_PAREN')) {
            do {
                args.push(this.parseExpr());
            } while (this.match('COMMA'));
        }
        const paren = this.consume('CLOSE_PAREN', "Expect ')' after arguments");
        return new ast_1.CallExpr(this.mergeRange(callee.range, paren.range), callee, args);
    }
    parsePrimary() {
        if (this.match('INT_LITERAL')) {
            const token = this.previous();
            return new ast_1.IntLiteral(token.range, token.literal);
        }
        if (this.match('FLOAT_LITERAL')) {
            const token = this.previous();
            return new ast_1.FloatLiteral(token.range, token.literal);
        }
        if (this.match('STRING_LITERAL')) {
            const token = this.previous();
            return new ast_1.StringLiteral(token.range, token.literal);
        }
        if (this.matchKeyword(types_1.Keyword.True)) {
            const token = this.previous();
            return new ast_1.BoolLiteral(token.range, true);
        }
        if (this.matchKeyword(types_1.Keyword.False)) {
            const token = this.previous();
            return new ast_1.BoolLiteral(token.range, false);
        }
        if (this.match('IDENTIFIER')) {
            const token = this.previous();
            return new ast_1.Identifier(token.range, token.lexeme);
        }
        if (this.match('OPEN_PAREN')) {
            if (this.check('CLOSE_PAREN')) {
                const closeToken = this.advance();
                return new ast_1.UnitLiteral(this.mergeRange(this.previous().range, closeToken.range));
            }
            const expr = this.parseExpr();
            this.consume('CLOSE_PAREN', "Expect ')' after expression");
            return new ast_1.GroupExpr(expr.range, expr);
        }
        const token = this.peek();
        this.errors.error(types_1.CompilerStage.Parsing, `Unexpected token '${token.lexeme}'`, token.range);
        // Try to recover by advancing
        this.advance();
        return new ast_1.UnitLiteral(token.range);
    }
    parseType() {
        const token = this.consume('IDENTIFIER', 'Expect type name');
        switch (token.lexeme) {
            case 'Int': return types_1.Type.int();
            case 'Float': return types_1.Type.float();
            case 'Bool': return types_1.Type.bool();
            case 'String': return types_1.Type.string();
            case 'Unit': return types_1.Type.unit();
            default:
                this.errors.error(types_1.CompilerStage.Parsing, `Unknown type '${token.lexeme}'`, token.range, ["Valid types: Int, Float, Bool, String, Unit"]);
                return types_1.Type.infer();
        }
    }
    // Helpers
    match(kind) {
        if (this.check(kind)) {
            this.advance();
            return true;
        }
        return false;
    }
    matchOperator(lexeme) {
        if (this.peek().kind === 'OPERATOR' && this.peek().lexeme === lexeme) {
            this.advance();
            return true;
        }
        return false;
    }
    matchKeyword(keyword) {
        if (this.peek().kind === 'KEYWORD' &&
            this.peek().lexeme === keyword) {
            this.advance();
            return true;
        }
        return false;
    }
    check(kind) {
        if (this.isAtEnd())
            return false;
        return this.peek().kind === kind;
    }
    checkKeyword(keyword) {
        if (this.isAtEnd())
            return false;
        return this.peek().kind === 'KEYWORD' && this.peek().lexeme === keyword;
    }
    advance() {
        if (!this.isAtEnd())
            this.current++;
        return this.previous();
    }
    consume(kind, message) {
        if (this.check(kind))
            return this.advance();
        const token = this.peek();
        this.errors.error(types_1.CompilerStage.Parsing, message, token.range);
        return token;
    }
    consumeKeyword(keyword, message) {
        if (this.checkKeyword(keyword))
            return this.advance();
        const token = this.peek();
        this.errors.error(types_1.CompilerStage.Parsing, message, token.range);
        return token;
    }
    isAtEnd() {
        return this.peek().kind === 'EOF';
    }
    peek() {
        return this.tokens[this.current];
    }
    previous() {
        return this.tokens[this.current - 1];
    }
    mergeRange(startRange, endRange) {
        return {
            start: { ...startRange.start },
            end: { ...endRange.end },
            sourceId: this.sourceId,
        };
    }
}
exports.Parser = Parser;
//# sourceMappingURL=parser.js.map