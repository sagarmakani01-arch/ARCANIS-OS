"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const lexer_1 = require("./lexer");
const error_1 = require("../error");
function tokenize(source, sourceId = 'test.arc') {
    const errors = new error_1.ErrorReporter();
    const lexer = new lexer_1.Lexer(source, sourceId, errors);
    return lexer.tokenize();
}
function tokenKinds(source) {
    return tokenize(source).map((t) => t.kind);
}
describe('Lexer', () => {
    it('tokenizes empty source', () => {
        const tokens = tokenize('');
        expect(tokens).toHaveLength(1);
        expect(tokens[0].kind).toBe('EOF');
    });
    it('tokenizes parentheses', () => {
        expect(tokenKinds('()')).toEqual(['OPEN_PAREN', 'CLOSE_PAREN', 'EOF']);
    });
    it('tokenizes braces', () => {
        expect(tokenKinds('{}')).toEqual(['OPEN_BRACE', 'CLOSE_BRACE', 'EOF']);
    });
    it('tokenizes semicolons', () => {
        expect(tokenKinds(';;')).toEqual(['SEMICOLON', 'SEMICOLON', 'EOF']);
    });
    it('tokenizes operators', () => {
        expect(tokenKinds('+ - * / %')).toEqual([
            'OPERATOR', 'OPERATOR', 'OPERATOR', 'OPERATOR', 'OPERATOR', 'EOF',
        ]);
    });
    it('tokenizes comparison operators', () => {
        expect(tokenKinds('== != < > <= >=')).toEqual([
            'OPERATOR', 'OPERATOR', 'OPERATOR', 'OPERATOR', 'OPERATOR', 'OPERATOR',
            'EOF',
        ]);
    });
    it('tokenizes logical operators', () => {
        const kinds = tokenKinds('&& || !');
        expect(kinds).toEqual(['OPERATOR', 'OPERATOR', 'OPERATOR', 'EOF']);
    });
    it('tokenizes integers', () => {
        const tokens = tokenize('42');
        expect(tokens[0].kind).toBe('INT_LITERAL');
        expect(tokens[0].literal).toBe(42);
    });
    it('tokenizes floats', () => {
        const tokens = tokenize('3.14');
        expect(tokens[0].kind).toBe('FLOAT_LITERAL');
        expect(tokens[0].literal).toBe(3.14);
    });
    it('tokenizes strings', () => {
        const tokens = tokenize('"hello"');
        expect(tokens[0].kind).toBe('STRING_LITERAL');
        expect(tokens[0].literal).toBe('hello');
    });
    it('tokenizes keywords', () => {
        const tokens = tokenize('let fun if else while return');
        const keywords = tokens.filter((t) => t.kind === 'KEYWORD');
        expect(keywords).toHaveLength(6);
    });
    it('tokenizes identifiers', () => {
        const tokens = tokenize('foo bar _baz');
        const ids = tokens.filter((t) => t.kind === 'IDENTIFIER');
        expect(ids).toHaveLength(3);
        expect(ids[0].lexeme).toBe('foo');
        expect(ids[1].lexeme).toBe('bar');
    });
    it('tokenizes arrow', () => {
        expect(tokenKinds('->')).toEqual(['ARROW', 'EOF']);
    });
    it('skips line comments', () => {
        const tokens = tokenize('let x = 1 // this is a comment\n let y = 2');
        expect(tokens[0].kind).toBe('KEYWORD');
        expect(tokens[4].kind).toBe('KEYWORD');
        expect(tokens[5].kind).toBe('IDENTIFIER');
    });
    it('skips block comments', () => {
        const tokens = tokenize('let /* comment */ x = 1');
        expect(tokens).toHaveLength(5);
        expect(tokens[0].kind).toBe('KEYWORD');
        expect(tokens[1].kind).toBe('IDENTIFIER');
    });
    it('skips nested block comments', () => {
        const tokens = tokenize('/* outer /* inner */ */ let x = 1');
        expect(tokens[0].kind).toBe('KEYWORD');
    });
    it('reports error on unterminated string', () => {
        const errors = new error_1.ErrorReporter();
        const lexer = new lexer_1.Lexer('"hello', 'test.arc', errors);
        lexer.tokenize();
        expect(errors.hasErrors()).toBe(true);
    });
    it('reports error on unexpected character', () => {
        const errors = new error_1.ErrorReporter();
        const lexer = new lexer_1.Lexer('@', 'test.arc', errors);
        lexer.tokenize();
        expect(errors.hasErrors()).toBe(true);
    });
    it('handles true/false literals', () => {
        const tokens = tokenize('true false');
        expect(tokens[0].literal).toBe(true);
        expect(tokens[1].literal).toBe(false);
    });
});
//# sourceMappingURL=lexer.test.js.map