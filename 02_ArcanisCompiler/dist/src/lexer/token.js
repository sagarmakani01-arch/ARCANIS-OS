"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Token = void 0;
class Token {
    constructor(kind, lexeme, location, sourceId, literal) {
        this.kind = kind;
        this.lexeme = lexeme;
        this.location = location;
        this.sourceId = sourceId;
        this.literal = literal;
    }
    get range() {
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
    toString() {
        const lit = this.literal !== undefined ? ` (${this.literal})` : '';
        return `${this.kind} '${this.lexeme}'${lit} at ${this.sourceId}:${this.location.line}:${this.location.column}`;
    }
}
exports.Token = Token;
//# sourceMappingURL=token.js.map