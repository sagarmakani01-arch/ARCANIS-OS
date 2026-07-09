import { DocumentationPage } from './types.js';
export declare class DocRenderer {
    toMarkdown(page: DocumentationPage): string;
    toHtml(page: DocumentationPage): string;
    private renderSymbols;
    private symbolToHtml;
}
