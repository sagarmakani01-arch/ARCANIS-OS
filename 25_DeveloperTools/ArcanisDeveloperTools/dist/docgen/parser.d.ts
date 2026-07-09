import { DocComment, DocumentedSymbol } from './types.js';
export declare class DocParser {
    parseComments(source: string): DocComment[];
    extractSymbols(source: string, comments: DocComment[]): DocumentedSymbol[];
}
