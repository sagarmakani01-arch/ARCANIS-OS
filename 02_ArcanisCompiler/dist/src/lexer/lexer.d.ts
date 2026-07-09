import { Token } from './token';
import { ErrorReporter } from '../error';
export declare class Lexer {
    private source;
    private sourceId;
    private start;
    private current;
    private line;
    private column;
    private tokens;
    private errors;
    constructor(source: string, sourceId: string | undefined, errors: ErrorReporter);
    tokenize(): Token[];
    private scanToken;
    private scanIdentifier;
    private scanNumber;
    private scanString;
    private skipLineComment;
    private skipBlockComment;
    private advance;
    private match;
    private peek;
    private peekNext;
    private isAtEnd;
    private isDigit;
    private isAlpha;
    private isAlphaNumeric;
    private location;
    private range;
    private addToken;
}
//# sourceMappingURL=lexer.d.ts.map