"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DocRenderer = void 0;
class DocRenderer {
    toMarkdown(page) {
        const lines = [];
        lines.push(`# ${page.title}`, '');
        lines.push(page.description, '');
        lines.push('## API Reference', '');
        lines.push(...this.renderSymbols(page.symbols, 2));
        return lines.join('\n');
    }
    toHtml(page) {
        const symbolsHtml = page.symbols.map(s => this.symbolToHtml(s, 0)).join('\n');
        return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>${page.title}</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; }
pre { background: #f5f5f5; padding: 1rem; border-radius: 4px; overflow-x: auto; }
.symbol { border-left: 3px solid #3b82f6; padding-left: 1rem; margin: 1.5rem 0; }
.symbol h3 { margin: 0 0 0.5rem; }
.tag { display: inline-block; background: #e0e7ff; padding: 0.1rem 0.5rem; border-radius: 3px; font-size: 0.8rem; margin: 0.2rem; }
</style>
</head>
<body>
<h1>${page.title}</h1>
<p>${page.description}</p>
<h2>API Reference</h2>
${symbolsHtml}
</body>
</html>`;
    }
    renderSymbols(symbols, indent) {
        const lines = [];
        for (const sym of symbols) {
            const prefix = '#'.repeat(indent);
            lines.push(`${prefix} ${sym.name}`, '');
            lines.push(`\`\`\`typescript\n${sym.signature}\n\`\`\``, '');
            if (sym.comment) {
                lines.push(sym.comment.description, '');
                for (const tag of sym.comment.tags) {
                    lines.push(`- **@${tag.name}**: ${tag.value}`);
                }
                lines.push('');
            }
            if (sym.children.length > 0) {
                lines.push(...this.renderSymbols(sym.children, indent + 1));
            }
        }
        return lines;
    }
    symbolToHtml(sym, depth) {
        const tag = depth === 0 ? 'h3' : 'h4';
        let html = `<div class="symbol">
<${tag}>${sym.name}</${tag}>
<pre>${escHtml(sym.signature)}</pre>`;
        if (sym.comment) {
            html += `<p>${escHtml(sym.comment.description)}</p>`;
            for (const t of sym.comment.tags) {
                html += `<span class="tag">@${t.name}: ${escHtml(t.value)}</span> `;
            }
        }
        for (const child of sym.children) {
            html += this.symbolToHtml(child, depth + 1);
        }
        html += '</div>';
        return html;
    }
}
exports.DocRenderer = DocRenderer;
function escHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
//# sourceMappingURL=renderer.js.map