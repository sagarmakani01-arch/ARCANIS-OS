import { DocParser } from './parser.js';
import { DocRenderer } from './renderer.js';
import { DocGenConfig, DocumentationPage } from './types.js';

export { DocParser, DocRenderer };
export type { DocGenConfig, DocumentationPage, DocComment, DocTag, DocumentedSymbol } from './types.js';

export class DocumentationGenerator {
  private parser: DocParser;
  private renderer: DocRenderer;
  private config: DocGenConfig;

  constructor(config?: Partial<DocGenConfig>) {
    this.parser = new DocParser();
    this.renderer = new DocRenderer();
    this.config = {
      outputDir: './docs',
      format: 'markdown',
      includePrivate: false,
      title: 'API Documentation',
      ...config,
    };
  }

  async generate(files: Map<string, string>): Promise<DocumentationPage[]> {
    const pages: DocumentationPage[] = [];
    for (const [filePath, source] of files) {
      const comments = this.parser.parseComments(source);
      const symbols = this.parser.extractSymbols(source, comments);
      pages.push({
        title: this.config.title,
        description: `Auto-generated documentation for ${filePath}`,
        symbols,
        format: this.config.format,
      });
    }
    return pages;
  }

  render(pages: DocumentationPage[]): string[] {
    return pages.map(p => {
      if (p.format === 'html') return this.renderer.toHtml(p);
      return this.renderer.toMarkdown(p);
    });
  }
}
