"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const lexer_1 = require("../lexer/lexer");
const parser_1 = require("../parser/parser");
const optimizer_1 = require("./optimizer");
const error_1 = require("../error");
const ast_1 = require("../parser/ast");
function optimize(source, sourceId = 'test.arc') {
    const errors = new error_1.ErrorReporter();
    const lexer = new lexer_1.Lexer(source, sourceId, errors);
    const tokens = lexer.tokenize();
    const parser = new parser_1.Parser(tokens, sourceId, errors);
    const program = parser.parse();
    const optimizer = new optimizer_1.Optimizer();
    const optimized = optimizer.optimize(program);
    return { program: optimized, optimizer };
}
describe('Optimizer', () => {
    it('folds constant integer addition', () => {
        const { program, optimizer } = optimize('fun main(): Int { return 2 + 3; }');
        expect(optimizer.getChangeCount()).toBeGreaterThan(0);
        const ret = program.functions[0].body.statements[0];
        expect(ret.value).toBeInstanceOf(ast_1.IntLiteral);
        expect(ret.value.value).toBe(5);
    });
    it('folds constant boolean comparison', () => {
        const { program, optimizer } = optimize('fun main(): Bool { return 5 == 5; }');
        expect(optimizer.getChangeCount()).toBeGreaterThan(0);
        const ret = program.functions[0].body.statements[0];
        expect(ret.value).toBeInstanceOf(ast_1.BoolLiteral);
        expect(ret.value.value).toBe(true);
    });
    it('folds logical operations', () => {
        const { program, optimizer } = optimize('fun main(): Bool { return true && false; }');
        expect(optimizer.getChangeCount()).toBeGreaterThan(0);
        const ret = program.functions[0].body.statements[0];
        expect(ret.value).toBeInstanceOf(ast_1.BoolLiteral);
        expect(ret.value.value).toBe(false);
    });
    it('folds logical OR', () => {
        const { program, optimizer } = optimize('fun main(): Bool { return true || false; }');
        expect(optimizer.getChangeCount()).toBeGreaterThan(0);
        const ret = program.functions[0].body.statements[0];
        expect(ret.value.value).toBe(true);
    });
    it('eliminates while(false)', () => {
        const { program, optimizer } = optimize('fun main(): Unit { while (false) { print("x"); } }');
        expect(optimizer.getChangeCount()).toBeGreaterThan(0);
    });
    it('folds comparison operators', () => {
        const { program, optimizer } = optimize('fun main(): Bool { return 10 > 5; }');
        expect(optimizer.getChangeCount()).toBeGreaterThan(0);
        const ret = program.functions[0].body.statements[0];
        expect(ret.value.value).toBe(true);
    });
    it('folds negation', () => {
        const { program, optimizer } = optimize('fun main(): Int { return -(-5); }');
        expect(optimizer.getChangeCount()).toBeGreaterThan(0);
    });
    it('folds float operations', () => {
        const { program, optimizer } = optimize('fun main(): Float { return 1.5 + 2.5; }');
        expect(optimizer.getChangeCount()).toBeGreaterThan(0);
        const ret = program.functions[0].body.statements[0];
        expect(ret.value).toBeInstanceOf(ast_1.FloatLiteral);
    });
    it('does not change already optimal code', () => {
        const { optimizer } = optimize('fun main(): Int { let x = a + b; return x; }');
        expect(optimizer.getChangeCount()).toBe(0);
    });
});
//# sourceMappingURL=optimizer.test.js.map