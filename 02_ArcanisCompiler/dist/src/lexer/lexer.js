"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Lexer = void 0;
const token_1 = require("./token");
const types_1 = require("../types");
// Mapping of keyword strings to keywords
const KEYWORDS = new Map(Object.values(types_1.Keyword).map((kw) => [kw, kw]));
class Lexer {
    constructor(source, sourceId = '<stdin>', errors) {
        this.start = 0;
        this.current = 0;
        this.line = 1;
        this.column = 1;
        this.tokens = [];
        this.source = source;
        this.sourceId = sourceId;
        this.errors = errors;
        this.errors.setSource(sourceId, source);
    }
    tokenize() {
        while (!this.isAtEnd()) {
            this.start = this.current;
            this.scanToken();
        }
        this.tokens.push(new token_1.Token('EOF', '', this.location(), this.sourceId));
        return this.tokens;
    }
    scanToken() {
        const c = this.advance();
        switch (c) {
            case '(':
                this.addToken('OPEN_PAREN', '(');
                break;
            case ')':
                this.addToken('CLOSE_PAREN', ')');
                break;
            case '{':
                this.addToken('OPEN_BRACE', '{');
                break;
            case '}':
                this.addToken('CLOSE_BRACE', '}');
                break;
            case '[':
                this.addToken('OPEN_BRACKET', '[');
                break;
            case ']':
                this.addToken('CLOSE_BRACKET', ']');
                break;
            case ';':
                this.addToken('SEMICOLON', ';');
                break;
            case ':':
                this.addToken('COLON', ':');
                break;
            case ',':
                this.addToken('COMMA', ',');
                break;
            case '.':
                this.addToken('DOT', '.');
                break;
            case '+':
                this.addToken('OPERATOR', '+');
                break;
            case '-':
                if (this.match('>')) {
                    this.addToken('ARROW', '->');
                }
                else {
                    this.addToken('OPERATOR', '-');
                }
                break;
            case '*':
                this.addToken('OPERATOR', '*');
                break;
            case '/':
                if (this.match('/')) {
                    this.skipLineComment();
                }
                else if (this.match('*')) {
                    this.skipBlockComment();
                }
                else {
                    this.addToken('OPERATOR', '/');
                }
                break;
            case '%':
                this.addToken('OPERATOR', '%');
                break;
            case '!':
                if (this.match('=')) {
                    this.addToken('OPERATOR', '!=');
                }
                else {
                    this.addToken('OPERATOR', '!');
                }
                break;
            case '=':
                if (this.match('=')) {
                    this.addToken('OPERATOR', '==');
                }
                else {
                    this.addToken('OPERATOR', '=');
                }
                break;
            case '<':
                if (this.match('=')) {
                    this.addToken('OPERATOR', '<=');
                }
                else {
                    this.addToken('OPERATOR', '<');
                }
                break;
            case '>':
                if (this.match('=')) {
                    this.addToken('OPERATOR', '>=');
                }
                else {
                    this.addToken('OPERATOR', '>');
                }
                break;
            case '&':
                if (this.match('&')) {
                    this.addToken('OPERATOR', '&&');
                }
                else {
                    this.errors.error(types_1.CompilerStage.Lexing, "Unexpected '&'. Did you mean '&&'?", this.range(), ["Use '&&' for logical AND"]);
                }
                break;
            case '|':
                if (this.match('|')) {
                    this.addToken('OPERATOR', '||');
                }
                else {
                    this.errors.error(types_1.CompilerStage.Lexing, "Unexpected '|'. Did you mean '||'?", this.range(), ["Use '||' for logical OR"]);
                }
                break;
            case '"':
                this.scanString();
                break;
            case ' ':
            case '\r':
            case '\t':
                break;
            case '\n':
                this.line++;
                this.column = 1;
                break;
            default:
                if (this.isDigit(c)) {
                    this.scanNumber();
                }
                else if (this.isAlpha(c)) {
                    this.scanIdentifier();
                }
                else {
                    this.errors.error(types_1.CompilerStage.Lexing, `Unexpected character '${c}'`, this.range());
                }
                break;
        }
    }
    scanIdentifier() {
        while (this.isAlphaNumeric(this.peek())) {
            this.advance();
        }
        const text = this.source.slice(this.start, this.current);
        const keyword = KEYWORDS.get(text);
        if (keyword !== undefined) {
            // Build literal value for true/false
            let literal;
            if (text === types_1.Keyword.True) {
                literal = true;
            }
            else if (text === types_1.Keyword.False) {
                literal = false;
            }
            else {
                literal = text;
            }
            this.tokens.push(new token_1.Token('KEYWORD', text, this.location(), this.sourceId, literal));
        }
        else {
            this.tokens.push(new token_1.Token('IDENTIFIER', text, this.location(), this.sourceId));
        }
    }
    scanNumber() {
        let isFloat = false;
        while (this.isDigit(this.peek())) {
            this.advance();
        }
        // Look for a fractional part
        if (this.peek() === '.' && this.isDigit(this.peekNext())) {
            isFloat = true;
            this.advance(); // consume the '.'
            while (this.isDigit(this.peek())) {
                this.advance();
            }
        }
        const text = this.source.slice(this.start, this.current);
        if (isFloat) {
            const value = parseFloat(text);
            this.tokens.push(new token_1.Token('FLOAT_LITERAL', text, this.location(), this.sourceId, value));
        }
        else {
            const value = parseInt(text, 10);
            this.tokens.push(new token_1.Token('INT_LITERAL', text, this.location(), this.sourceId, value));
        }
    }
    scanString() {
        while (this.peek() !== '"' && !this.isAtEnd()) {
            if (this.peek() === '\n') {
                this.line++;
            }
            if (this.peek() === '\\') {
                this.advance(); // consume escape character
            }
            this.advance();
        }
        if (this.isAtEnd()) {
            this.errors.error(types_1.CompilerStage.Lexing, 'Unterminated string literal', this.range(), ["Add a closing '\"' to the string"]);
            return;
        }
        // closing "
        this.advance();
        const text = this.source.slice(this.start + 1, this.current - 1);
        this.tokens.push(new token_1.Token('STRING_LITERAL', text, this.location(), this.sourceId, text));
    }
    skipLineComment() {
        while (this.peek() !== '\n' && !this.isAtEnd()) {
            this.advance();
        }
    }
    skipBlockComment() {
        let depth = 1;
        while (depth > 0 && !this.isAtEnd()) {
            const c = this.advance();
            if (c === '/' && this.peek() === '*') {
                depth++;
                this.advance();
            }
            else if (c === '*' && this.peek() === '/') {
                depth--;
                this.advance();
            }
            else if (c === '\n') {
                this.line++;
                this.column = 1;
            }
        }
        if (depth > 0) {
            this.errors.error(types_1.CompilerStage.Lexing, 'Unterminated block comment', this.range(), ["Add a closing '*/' for the block comment"]);
        }
    }
    advance() {
        this.current++;
        this.column++;
        return this.source[this.current - 1];
    }
    match(expected) {
        if (this.isAtEnd())
            return false;
        if (this.source[this.current] !== expected)
            return false;
        this.current++;
        this.column++;
        return true;
    }
    peek() {
        if (this.isAtEnd())
            return '\0';
        return this.source[this.current];
    }
    peekNext() {
        if (this.current + 1 >= this.source.length)
            return '\0';
        return this.source[this.current + 1];
    }
    isAtEnd() {
        return this.current >= this.source.length;
    }
    isDigit(c) {
        return c >= '0' && c <= '9';
    }
    isAlpha(c) {
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c === '_';
    }
    isAlphaNumeric(c) {
        return this.isAlpha(c) || this.isDigit(c);
    }
    location() {
        return {
            line: this.line,
            column: this.column,
            offset: this.current,
        };
    }
    range() {
        return {
            start: {
                line: this.line,
                column: this.column - 1,
                offset: this.start,
            },
            end: {
                line: this.line,
                column: this.column,
                offset: this.current,
            },
            sourceId: this.sourceId,
        };
    }
    addToken(kind, lexeme, literal) {
        this.tokens.push(new token_1.Token(kind, lexeme, this.location(), this.sourceId, literal));
    }
}
exports.Lexer = Lexer;
//# sourceMappingURL=lexer.js.map