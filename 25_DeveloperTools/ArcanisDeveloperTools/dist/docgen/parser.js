"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DocParser = void 0;
class DocParser {
    parseComments(source) {
        const comments = [];
        const jsdocRegex = /\/\*\*([\s\S]*?)\*\//g;
        let match;
        while ((match = jsdocRegex.exec(source)) !== null) {
            const line = source.slice(0, match.index).split('\n').length;
            const content = match[1];
            const lines = content.split('\n').map(l => l.replace(/^\s*\*\s?/, '').trim()).filter(l => l);
            const description = [];
            const tags = [];
            for (const line of lines) {
                const tagMatch = line.match(/^@(\w+)\s+(.+)/);
                if (tagMatch) {
                    tags.push({ name: tagMatch[1], value: tagMatch[2] });
                }
                else {
                    description.push(line);
                }
            }
            comments.push({ description: description.join(' '), tags, line });
        }
        return comments;
    }
    extractSymbols(source, comments) {
        const symbols = [];
        const patterns = [
            { regex: /export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)/g, type: 'function' },
            { regex: /export\s+(?:default\s+)?class\s+(\w+)/g, type: 'class' },
            { regex: /export\s+(?:default\s+)?interface\s+(\w+)/g, type: 'interface' },
            { regex: /export\s+(?:default\s+)?type\s+(\w+)/g, type: 'type' },
        ];
        for (const { regex, type } of patterns) {
            let m;
            while ((m = regex.exec(source)) !== null) {
                const line = source.slice(0, m.index).split('\n').length;
                const comment = comments.find(c => Math.abs(c.line - line) <= 2) || null;
                symbols.push({
                    name: m[1],
                    type,
                    comment,
                    signature: m[0],
                    line,
                    children: [],
                });
            }
        }
        return symbols;
    }
}
exports.DocParser = DocParser;
//# sourceMappingURL=parser.js.map