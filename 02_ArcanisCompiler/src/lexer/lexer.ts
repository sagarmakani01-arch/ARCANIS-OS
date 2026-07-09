import { Token } from './token';
import { ErrorReporter, createCompilerError } from '../error';
import { SourceLocation, CompilerStage, Keyword } from '../types';

// Mapping of keyword strings to keywords
const KEYWORDS: Map<string, Keyword> = new Map(
  Object.values(Keyword).map((kw) => [kw, kw]),
);

export class Lexer {
  private source: string;
  private sourceId: string;
  private start: number = 0;
  private current: number = 0;
  private line: number = 1;
  private column: number = 1;
  private tokens: Token[] = [];
  private errors: ErrorReporter;

  constructor(source: string, sourceId: string = '<stdin>', errors: ErrorReporter) {
    this.source = source;
    this.sourceId = sourceId;
    this.errors = errors;
    this.errors.setSource(sourceId, source);
  }

  tokenize(): Token[] {
    while (!this.isAtEnd()) {
      this.start = this.current;
      this.scanToken();
    }

    this.tokens.push(
      new Token('EOF', '', this.location(), this.sourceId),
    );

    return this.tokens;
  }

  private scanToken(): void {
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
        } else {
          this.addToken('OPERATOR', '-');
        }
        break;
      case '*':
        this.addToken('OPERATOR', '*');
        break;
      case '/':
        if (this.match('/')) {
          this.skipLineComment();
        } else if (this.match('*')) {
          this.skipBlockComment();
        } else {
          this.addToken('OPERATOR', '/');
        }
        break;
      case '%':
        this.addToken('OPERATOR', '%');
        break;
      case '!':
        if (this.match('=')) {
          this.addToken('OPERATOR', '!=');
        } else {
          this.addToken('OPERATOR', '!');
        }
        break;
      case '=':
        if (this.match('=')) {
          this.addToken('OPERATOR', '==');
        } else {
          this.addToken('OPERATOR', '=');
        }
        break;
      case '<':
        if (this.match('=')) {
          this.addToken('OPERATOR', '<=');
        } else {
          this.addToken('OPERATOR', '<');
        }
        break;
      case '>':
        if (this.match('=')) {
          this.addToken('OPERATOR', '>=');
        } else {
          this.addToken('OPERATOR', '>');
        }
        break;
      case '&':
        if (this.match('&')) {
          this.addToken('OPERATOR', '&&');
        } else {
          this.errors.error(
            CompilerStage.Lexing,
            "Unexpected '&'. Did you mean '&&'?",
            this.range(),
            ["Use '&&' for logical AND"],
          );
        }
        break;
      case '|':
        if (this.match('|')) {
          this.addToken('OPERATOR', '||');
        } else {
          this.errors.error(
            CompilerStage.Lexing,
            "Unexpected '|'. Did you mean '||'?",
            this.range(),
            ["Use '||' for logical OR"],
          );
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
        } else if (this.isAlpha(c)) {
          this.scanIdentifier();
        } else {
          this.errors.error(
            CompilerStage.Lexing,
            `Unexpected character '${c}'`,
            this.range(),
          );
        }
        break;
    }
  }

  private scanIdentifier(): void {
    while (this.isAlphaNumeric(this.peek())) {
      this.advance();
    }

    const text = this.source.slice(this.start, this.current);
    const keyword = KEYWORDS.get(text);
    if (keyword !== undefined) {
      // Build literal value for true/false
      let literal: string | boolean | undefined;
      if (text === Keyword.True) {
        literal = true;
      } else if (text === Keyword.False) {
        literal = false;
      } else {
        literal = text;
      }
      this.tokens.push(
        new Token('KEYWORD', text, this.location(), this.sourceId, literal),
      );
    } else {
      this.tokens.push(
        new Token('IDENTIFIER', text, this.location(), this.sourceId),
      );
    }
  }

  private scanNumber(): void {
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
      this.tokens.push(
        new Token('FLOAT_LITERAL', text, this.location(), this.sourceId, value),
      );
    } else {
      const value = parseInt(text, 10);
      this.tokens.push(
        new Token('INT_LITERAL', text, this.location(), this.sourceId, value),
      );
    }
  }

  private scanString(): void {
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
      this.errors.error(
        CompilerStage.Lexing,
        'Unterminated string literal',
        this.range(),
        ["Add a closing '\"' to the string"],
      );
      return;
    }

    // closing "
    this.advance();

    const text = this.source.slice(this.start + 1, this.current - 1);
    this.tokens.push(
      new Token('STRING_LITERAL', text, this.location(), this.sourceId, text),
    );
  }

  private skipLineComment(): void {
    while (this.peek() !== '\n' && !this.isAtEnd()) {
      this.advance();
    }
  }

  private skipBlockComment(): void {
    let depth = 1;
    while (depth > 0 && !this.isAtEnd()) {
      const c = this.advance();
      if (c === '/' && this.peek() === '*') {
        depth++;
        this.advance();
      } else if (c === '*' && this.peek() === '/') {
        depth--;
        this.advance();
      } else if (c === '\n') {
        this.line++;
        this.column = 1;
      }
    }

    if (depth > 0) {
      this.errors.error(
        CompilerStage.Lexing,
        'Unterminated block comment',
        this.range(),
        ["Add a closing '*/' for the block comment"],
      );
    }
  }

  private advance(): string {
    this.current++;
    this.column++;
    return this.source[this.current - 1];
  }

  private match(expected: string): boolean {
    if (this.isAtEnd()) return false;
    if (this.source[this.current] !== expected) return false;
    this.current++;
    this.column++;
    return true;
  }

  private peek(): string {
    if (this.isAtEnd()) return '\0';
    return this.source[this.current];
  }

  private peekNext(): string {
    if (this.current + 1 >= this.source.length) return '\0';
    return this.source[this.current + 1];
  }

  private isAtEnd(): boolean {
    return this.current >= this.source.length;
  }

  private isDigit(c: string): boolean {
    return c >= '0' && c <= '9';
  }

  private isAlpha(c: string): boolean {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c === '_';
  }

  private isAlphaNumeric(c: string): boolean {
    return this.isAlpha(c) || this.isDigit(c);
  }

  private location(): SourceLocation {
    return {
      line: this.line,
      column: this.column,
      offset: this.current,
    };
  }

  private range() {
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

  private addToken(kind: Token['kind'], lexeme: string, literal?: string | number | boolean): void {
    this.tokens.push(
      new Token(kind, lexeme, this.location(), this.sourceId, literal),
    );
  }
}
