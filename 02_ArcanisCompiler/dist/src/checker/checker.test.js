"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const lexer_1 = require("../lexer/lexer");
const parser_1 = require("../parser/parser");
const checker_1 = require("./checker");
const error_1 = require("../error");
function check(source, sourceId = 'test.arc') {
    const errors = new error_1.ErrorReporter();
    const lexer = new lexer_1.Lexer(source, sourceId, errors);
    const tokens = lexer.tokenize();
    const parser = new parser_1.Parser(tokens, sourceId, errors);
    const program = parser.parse();
    if (errors.hasErrors()) {
        return errors;
    }
    const checker = new checker_1.TypeChecker(sourceId, errors);
    checker.check(program);
    return errors;
}
describe('TypeChecker', () => {
    it('accepts valid function', () => {
        const errors = check('fun main(): Int { return 0; }');
        expect(errors.hasErrors()).toBe(false);
    });
    it('rejects return type mismatch', () => {
        const errors = check('fun main(): Int { return true; }');
        expect(errors.hasErrors()).toBe(true);
    });
    it('accepts correct binary operations', () => {
        const errors = check('fun main(): Int { let x: Int = 5 + 3; return x; }');
        expect(errors.hasErrors()).toBe(false);
    });
    it('rejects type mismatch in binary operations', () => {
        const errors = check('fun main(): Bool { return 5 + true; }');
        expect(errors.hasErrors()).toBe(true);
    });
    it('rejects if condition that is not Bool', () => {
        const errors = check('fun main(): Unit { if (5) { } }');
        expect(errors.hasErrors()).toBe(true);
    });
    it('rejects undefined variable', () => {
        const errors = check('fun main(): Int { return x; }');
        expect(errors.hasErrors()).toBe(true);
    });
    it('accepts function calls with correct arguments', () => {
        const errors = check('fun main(): Int { return add(3, 4); } fun add(a: Int, b: Int): Int { return a + b; }');
        expect(errors.hasErrors()).toBe(false);
    });
    it('rejects function calls with wrong argument types', () => {
        const errors = check('fun main(): Int { return add(3, true); } fun add(a: Int, b: Int): Int { return a + b; }');
        expect(errors.hasErrors()).toBe(true);
    });
    it('rejects function calls with wrong argument count', () => {
        const errors = check('fun main(): Int { return add(3); } fun add(a: Int, b: Int): Int { return a + b; }');
        expect(errors.hasErrors()).toBe(true);
    });
    it('accepts variable declaration with type inference', () => {
        const errors = check('fun main(): Int { let x = 42; return x; }');
        expect(errors.hasErrors()).toBe(false);
    });
    it('handles scoped variables correctly', () => {
        const errors = check('fun main(): Unit { let x: Int = 5; if (true) { let x: Int = 10; } }');
        expect(errors.hasErrors()).toBe(false);
    });
    it('accepts while loops', () => {
        const errors = check('fun main(): Unit { let x: Int = 0; while (x < 10) { x = x + 1; } }');
        expect(errors.hasErrors()).toBe(false);
    });
    it('accepts string concatenation', () => {
        const errors = check('fun main(): String { return "hello" + " " + "world"; }');
        expect(errors.hasErrors()).toBe(false);
    });
    it('accepts builtin function println', () => {
        const errors = check('fun main(): Unit { println("hello"); }');
        expect(errors.hasErrors()).toBe(false);
    });
});
//# sourceMappingURL=checker.test.js.map