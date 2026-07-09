import { DocParser } from './parser.js';
import { DocRenderer } from './renderer.js';
import { DocGenConfig, DocumentationPage } from './types.js';
export { DocParser, DocRenderer };
export type { DocGenConfig, DocumentationPage, DocComment, DocTag, DocumentedSymbol } from './types.js';
export declare class DocumentationGenerator {
    private parser;
    private renderer;
    private config;
    constructor(config?: Partial<DocGenConfig>);
    generate(files: Map<string, string>): Promise<DocumentationPage[]>;
    render(pages: DocumentationPage[]): string[];
}
