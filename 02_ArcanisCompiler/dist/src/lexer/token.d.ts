import { SourceLocation, SourceRange, TokenKind } from '../types';
export declare class Token {
    readonly kind: TokenKind;
    readonly lexeme: string;
    readonly location: SourceLocation;
    readonly sourceId: string;
    readonly literal?: string | number | boolean | undefined;
    constructor(kind: TokenKind, lexeme: string, location: SourceLocation, sourceId: string, literal?: string | number | boolean | undefined);
    get range(): SourceRange;
    toString(): string;
}
//# sourceMappingURL=token.d.ts.map