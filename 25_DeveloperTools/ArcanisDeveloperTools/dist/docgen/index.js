"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DocumentationGenerator = exports.DocRenderer = exports.DocParser = void 0;
const parser_js_1 = require("./parser.js");
Object.defineProperty(exports, "DocParser", { enumerable: true, get: function () { return parser_js_1.DocParser; } });
const renderer_js_1 = require("./renderer.js");
Object.defineProperty(exports, "DocRenderer", { enumerable: true, get: function () { return renderer_js_1.DocRenderer; } });
class DocumentationGenerator {
    parser;
    renderer;
    config;
    constructor(config) {
        this.parser = new parser_js_1.DocParser();
        this.renderer = new renderer_js_1.DocRenderer();
        this.config = {
            outputDir: './docs',
            format: 'markdown',
            includePrivate: false,
            title: 'API Documentation',
            ...config,
        };
    }
    async generate(files) {
        const pages = [];
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
    render(pages) {
        return pages.map(p => {
            if (p.format === 'html')
                return this.renderer.toHtml(p);
            return this.renderer.toMarkdown(p);
        });
    }
}
exports.DocumentationGenerator = DocumentationGenerator;
//# sourceMappingURL=index.js.map