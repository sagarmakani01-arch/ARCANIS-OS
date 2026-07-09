import { DocComment, DocTag, DocumentedSymbol } from './types.js';

export class DocParser {
  parseComments(source: string): DocComment[] {
    const comments: DocComment[] = [];
    const jsdocRegex = /\/\*\*([\s\S]*?)\*\//g;
    let match: RegExpExecArray | null;
    while ((match = jsdocRegex.exec(source)) !== null) {
      const line = source.slice(0, match.index).split('\n').length;
      const content = match[1];
      const lines = content.split('\n').map(l => l.replace(/^\s*\*\s?/, '').trim()).filter(l => l);
      const description: string[] = [];
      const tags: DocTag[] = [];
      for (const line of lines) {
        const tagMatch = line.match(/^@(\w+)\s+(.+)/);
        if (tagMatch) {
          tags.push({ name: tagMatch[1], value: tagMatch[2] });
        } else {
          description.push(line);
        }
      }
      comments.push({ description: description.join(' '), tags, line });
    }
    return comments;
  }

  extractSymbols(source: string, comments: DocComment[]): DocumentedSymbol[] {
    const symbols: DocumentedSymbol[] = [];
    const patterns = [
      { regex: /export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)/g, type: 'function' as const },
      { regex: /export\s+(?:default\s+)?class\s+(\w+)/g, type: 'class' as const },
      { regex: /export\s+(?:default\s+)?interface\s+(\w+)/g, type: 'interface' as const },
      { regex: /export\s+(?:default\s+)?type\s+(\w+)/g, type: 'type' as const },
    ];

    for (const { regex, type } of patterns) {
      let m: RegExpExecArray | null;
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
