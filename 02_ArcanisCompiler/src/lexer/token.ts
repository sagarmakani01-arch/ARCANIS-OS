import { SourceLocation, SourceRange, TokenKind } from '../types';

export class Token {
  constructor(
    public readonly kind: TokenKind,
    public readonly lexeme: string,
    public readonly location: SourceLocation,
    public readonly sourceId: string,
    public readonly literal?: string | number | boolean,
  ) {}

  get range(): SourceRange {
    return {
      start: this.location,
      end: {
        line: this.location.line,
        column: this.location.column + this.lexeme.length,
        offset: this.location.offset + this.lexeme.length,
      },
      sourceId: this.sourceId,
    };
  }

  toString(): string {
    const lit = this.literal !== undefined ? ` (${this.literal})` : '';
    return `${this.kind} '${this.lexeme}'${lit} at ${this.sourceId}:${this.location.line}:${this.location.column}`;
  }
}
