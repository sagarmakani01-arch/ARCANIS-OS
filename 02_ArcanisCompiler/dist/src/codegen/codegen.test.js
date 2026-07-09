"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const lexer_1 = require("../lexer/lexer");
const parser_1 = require("../parser/parser");
const checker_1 = require("../checker/checker");
const optimizer_1 = require("../optimizer/optimizer");
const codegen_1 = require("./codegen");
const error_1 = require("../error");
function compile(source, sourceId = 'test.arc') {
    const errors = new error_1.ErrorReporter();
    const lexer = new lexer_1.Lexer(source, sourceId, errors);
    const tokens = lexer.tokenize();
    const parser = new parser_1.Parser(tokens, sourceId, errors);
    let program = parser.parse();
    if (!errors.hasErrors()) {
        const checker = new checker_1.TypeChecker(sourceId, errors);
        checker.check(program);
    }
    if (!errors.hasErrors()) {
        const optimizer = new optimizer_1.Optimizer();
        program = optimizer.optimize(program);
    }
    const codegen = new codegen_1.JavaScriptCodeGen(sourceId);
    return codegen.generate(program);
}
describe('CodeGenerator', () => {
    it('generates function declaration', () => {
        const code = compile('fun main(): Int { return 0; }');
        expect(code).toContain('function main()');
        expect(code).toContain('return 0');
    });
    it('generates function with parameters', () => {
        const code = compile('fun add(a: Int, b: Int): Int { return a + b; }');
        expect(code).toContain('function add(a, b)');
        expect(code).toContain('return (a + b)');
    });
    it('generates variable declaration', () => {
        const code = compile('fun main(): Unit { let x: Int = 42; }');
        expect(code).toContain('let x = 42');
    });
    it('generates if-else statements', () => {
        const code = compile('fun main(): Int { if (true) { return 1; } else { return 2; } }');
        // Optimizer folds if(true) to the then-branch
        expect(code).toContain('return 1');
    });
    it('generates while loops', () => {
        const code = compile('fun main(): Unit { let x: Int = 0; while (x < 10) { x = x + 1; } }');
        expect(code).toContain('while (');
        expect(code).toContain('(x < 10)');
    });
    it('generates function calls', () => {
        const code = compile('fun main(): Unit { println("hello"); }');
        expect(code).toContain('console.log');
    });
    it('generates comparison operators', () => {
        const code = compile('fun main(): Bool { return a == b; }');
        expect(code).toContain('(a === b)');
    });
    it('generates logical operators', () => {
        const code = compile('fun main(): Bool { return a && b; }');
        expect(code).toContain('(a && b)');
    });
    it('generates valid JavaScript', () => {
        const code = compile('fun main(): Int { let x = 5; let y = 10; return x + y; }');
        expect(() => new Function(code)).not.toThrow();
    });
    it('generates correct expression precedence with optimizer', () => {
        const code = compile('fun main(): Int { return 2 + 3 * 4; }');
        // Optimizer folds to constant 14
        expect(code).toContain('return 14');
    });
});
//# sourceMappingURL=codegen.test.js.map