"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const lexer_1 = require("../lexer/lexer");
const parser_1 = require("./parser");
const error_1 = require("../error");
const ast_1 = require("./ast");
function parse(source, sourceId = 'test.arc') {
    const errors = new error_1.ErrorReporter();
    const lexer = new lexer_1.Lexer(source, sourceId, errors);
    const tokens = lexer.tokenize();
    const parser = new parser_1.Parser(tokens, sourceId, errors);
    const program = parser.parse();
    if (errors.hasErrors()) {
        throw new Error(errors.formatAll());
    }
    return program;
}
describe('Parser', () => {
    it('parses an empty program', () => {
        const program = parse('');
        expect(program.functions).toHaveLength(0);
        expect(program.statements).toHaveLength(0);
    });
    it('parses a function declaration', () => {
        const program = parse('fun main(): Int { return 0; }');
        expect(program.functions).toHaveLength(1);
        const fn = program.functions[0];
        expect(fn.name).toBe('main');
        expect(fn.returnType.toString()).toBe('Int');
        expect(fn.body).toBeInstanceOf(ast_1.BlockStmt);
    });
    it('parses function with parameters', () => {
        const program = parse('fun add(a: Int, b: Int): Int { return a + b; }');
        expect(program.functions).toHaveLength(1);
        const fn = program.functions[0];
        expect(fn.params).toHaveLength(2);
        expect(fn.params[0].name).toBe('a');
        expect(fn.params[1].name).toBe('b');
    });
    it('parses variable declaration', () => {
        const program = parse('fun main(): Unit { let x: Int = 5; }');
        const stmts = program.functions[0].body.statements;
        const varDecl = stmts[0];
        expect(varDecl).toBeInstanceOf(ast_1.VarDecl);
        expect(varDecl.name).toBe('x');
        expect(varDecl.varType.toString()).toBe('Int');
    });
    it('parses variable declaration with type inference', () => {
        const program = parse('fun main(): Unit { let x = 5; }');
        const stmts = program.functions[0].body.statements;
        const varDecl = stmts[0];
        expect(varDecl.name).toBe('x');
        expect(varDecl.varType.kind).toBe('Infer');
    });
    it('parses binary expressions', () => {
        const program = parse('fun main(): Int { return 2 + 3 * 4; }');
        const stmts = program.functions[0].body.statements;
        const ret = stmts[0];
        const expr = ret.value;
        expect(expr).toBeInstanceOf(ast_1.BinaryExpr);
        expect(expr.op).toBe('+');
    });
    it('parses if statements', () => {
        const program = parse('fun main(): Int { if (true) { return 1; } else { return 2; } }');
        expect(program.functions[0].body.statements[0]).toBeDefined();
    });
    it('parses while statements', () => {
        const program = parse('fun main(): Int { while (x > 0) { x = x - 1; } }');
        expect(program.functions[0].body.statements[0]).toBeDefined();
    });
    it('parses function calls', () => {
        const program = parse('fun main(): Unit { print("hello"); }');
        expect(program.functions[0].body.statements[0]).toBeDefined();
    });
    it('parses standalone expressions at top level', () => {
        const program = parse('print("hello");');
        expect(program.statements).toHaveLength(1);
    });
    it('handles error recovery on unexpected tokens', () => {
        const errors = new error_1.ErrorReporter();
        const lexer = new lexer_1.Lexer('fun main() { @ }', 'test.arc', errors);
        const tokens = lexer.tokenize();
        const parser = new parser_1.Parser(tokens, 'test.arc', errors);
        parser.parse();
        expect(errors.hasErrors()).toBe(true);
    });
    it('parses unit literal as ()', () => {
        const program = parse('fun main(): Unit { return (); }');
        const stmts = program.functions[0].body.statements;
        const ret = stmts[0];
        expect(ret.value).toBeDefined();
    });
    it('parses comparison chains', () => {
        const program = parse('fun main(): Bool { return a < b && c > d; }');
        const stmts = program.functions[0].body.statements;
        const ret = stmts[0];
        expect(ret.value).toBeDefined();
    });
});
//# sourceMappingURL=parser.test.js.map