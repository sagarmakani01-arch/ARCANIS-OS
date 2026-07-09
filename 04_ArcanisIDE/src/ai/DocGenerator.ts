import { TextDocument, Range, Position } from '../api/types';
import { AIAssistant } from './AIAssistant';

export interface GeneratedDoc {
  comment: string;
  summary: string;
  params?: Array<{ name: string; description: string }>;
  returns?: string;
  examples?: string[];
  throws?: Array<{ type: string; description: string }>;
}

export type DocFormat = 'jsdoc' | 'docstring' | 'arcanis';

export class DocGenerator {
  private assistant: AIAssistant;

  constructor(assistant: AIAssistant) {
    this.assistant = assistant;
  }

  async generateDocumentation(document: TextDocument, range: Range): Promise<GeneratedDoc> {
    const text = document.getText(range);
    const lines = text.split('\n');
    const firstLine = lines[0]?.trim() ?? '';

    let summary = '';
    const params: Array<{ name: string; description: string }> = [];
    let returns: string | undefined;
    const examples: string[] = [];
    const throws: Array<{ type: string; description: string }> = [];

    const fnMatch = firstLine.match(/(?:fn|function)\s+(\w+)\s*\(([^)]*)\)/);
    if (fnMatch) {
      const name = fnMatch[1];
      summary = `${name} - description`;

      const paramList = fnMatch[2].split(',').map((p) => p.trim()).filter(Boolean);
      for (const param of paramList) {
        const p = param.split(':')[0]?.trim() ?? param;
        params.push({ name: p, description: 'description' });
      }

      returns = 'description';
    }

    const classMatch = firstLine.match(/class\s+(\w+)/);
    if (classMatch) {
      summary = `${classMatch[1]} - description`;
    }

    const aiDoc = await this.assistant.generateDocumentation(document, range);
    if (aiDoc && !summary) {
      summary = aiDoc;
    }

    const format = this.detectFormat(document);
    const comment = this.formatComment(
      { comment: '', summary, params, returns, examples, throws },
      format,
    );

    return { comment, summary, params, returns, examples, throws };
  }

  async generateFileHeader(document: TextDocument): Promise<string> {
    const fileName = document.fileName;
    const text = document.getText();
    const lines = text.split('\n');
    const existingHeader = this.extractExistingHeader(lines);

    if (existingHeader) return existingHeader;

    const header = [
      '/**',
      ` * ${fileName}`,
      ' *',
      ' * @description',
      ' */',
      '',
    ].join('\n');

    return header;
  }

  async generateFunctionDoc(document: TextDocument, position: Position): Promise<string> {
    const line = document.lineAt(position.line);
    if (!line) return '';

    const text = line.text;
    const fnMatch = text.match(/(?:fn|function)\s+(\w+)\s*\(([^)]*)\)/);
    if (!fnMatch) {
      const adjacentLine = await this.findAdjacentFunction(document, position.line);
      if (adjacentLine) return adjacentLine;
      return '';
    }

    const name = fnMatch[1];
    const paramList = fnMatch[2].split(',').map((p) => p.trim()).filter(Boolean);

    let comment = '/**\n';
    comment += ` * ${name} - description\n`;

    if (paramList.length > 0) {
      comment += ' *\n';
      for (const param of paramList) {
        const parts = param.split(':').map((p) => p.trim());
        const paramName = parts[0];
        comment += ` * @param ${paramName} - description\n`;
      }
    }

    comment += ' * @returns description\n';
    comment += ' */';

    return comment;
  }

  private async findAdjacentFunction(document: TextDocument, lineNumber: number): Promise<string | undefined> {
    for (let offset = 1; offset <= 5; offset++) {
      const nextLine = document.lineAt(lineNumber + offset);
      if (nextLine) {
        const trimmed = nextLine.text.trim();
        const match = trimmed.match(/(?:fn|function)\s+(\w+)\s*\(([^)]*)\)/);
        if (match) {
          const pos: Position = { line: lineNumber + offset, column: 0 };
          return this.generateFunctionDoc(document, pos);
        }
      }
    }
    return undefined;
  }

  private detectFormat(document: TextDocument): DocFormat {
    const fileName = document.fileName.toLowerCase();
    const ext = fileName.split('.').pop() ?? '';

    if (['ts', 'tsx', 'js', 'jsx'].includes(ext)) return 'jsdoc';
    if (['py'].includes(ext)) return 'docstring';
    if (['arc', 'arcanis'].includes(ext) || document.languageId === 'arcanis') return 'arcanis';

    return 'jsdoc';
  }

  private formatComment(doc: GeneratedDoc, format: DocFormat): string {
    switch (format) {
      case 'docstring':
        return this.formatDocstring(doc);
      case 'arcanis':
        return this.formatArcanisDoc(doc);
      case 'jsdoc':
      default:
        return this.formatJSDoc(doc);
    }
  }

  private formatJSDoc(doc: GeneratedDoc): string {
    let comment = '/**\n';
    comment += ` * ${doc.summary}\n`;

    if (doc.params && doc.params.length > 0) {
      comment += ' *\n';
      for (const param of doc.params) {
        comment += ` * @param ${param.name} - ${param.description}\n`;
      }
    }

    if (doc.returns) {
      comment += ` * @returns ${doc.returns}\n`;
    }

    if (doc.throws && doc.throws.length > 0) {
      for (const t of doc.throws) {
        comment += ` * @throws {${t.type}} ${t.description}\n`;
      }
    }

    if (doc.examples && doc.examples.length > 0) {
      comment += ' *\n';
      for (const example of doc.examples) {
        comment += ` * @example\n * ${example.replace(/\n/g, '\n * ')}\n`;
      }
    }

    comment += ' */';
    return comment;
  }

  private formatDocstring(doc: GeneratedDoc): string {
    let comment = '"""\n';
    comment += `${doc.summary}\n`;

    if (doc.params && doc.params.length > 0) {
      comment += '\nArgs:\n';
      for (const param of doc.params) {
        comment += `    ${param.name}: ${param.description}\n`;
      }
    }

    if (doc.returns) {
      comment += `\nReturns:\n    ${doc.returns}\n`;
    }

    if (doc.throws && doc.throws.length > 0) {
      comment += '\nRaises:\n';
      for (const t of doc.throws) {
        comment += `    ${t.type}: ${t.description}\n`;
      }
    }

    comment += '"""';
    return comment;
  }

  private formatArcanisDoc(doc: GeneratedDoc): string {
    let comment = '//>doc\n';
    comment += `//>summary ${doc.summary}\n`;

    if (doc.params && doc.params.length > 0) {
      for (const param of doc.params) {
        comment += `//>param ${param.name} ${param.description}\n`;
      }
    }

    if (doc.returns) {
      comment += `//>returns ${doc.returns}\n`;
    }

    if (doc.throws && doc.throws.length > 0) {
      for (const t of doc.throws) {
        comment += `//>throws ${t.type} ${t.description}\n`;
      }
    }

    if (doc.examples && doc.examples.length > 0) {
      for (const example of doc.examples) {
        comment += `//>example\n//> ${example.replace(/\n/g, '\n//> ')}\n`;
      }
    }

    comment += '//>end';
    return comment;
  }

  private extractExistingHeader(lines: string[]): string | undefined {
    if (lines.length === 0) return undefined;

    const firstLine = lines[0].trim();
    if (firstLine === '/**' || firstLine === '"""' || firstLine === '//>doc') {
      const headerLines: string[] = [];
      if (firstLine === '/**') {
        for (let i = 0; i < lines.length; i++) {
          headerLines.push(lines[i]);
          if (lines[i].trim() === '*/') break;
        }
      } else if (firstLine === '"""') {
        for (let i = 0; i < lines.length; i++) {
          headerLines.push(lines[i]);
          if (i > 0 && lines[i].trim() === '"""') break;
        }
      } else if (firstLine === '//>doc') {
        for (let i = 0; i < lines.length; i++) {
          headerLines.push(lines[i]);
          if (lines[i].trim() === '//>end') break;
        }
      }
      return headerLines.length > 0 ? headerLines.join('\n') : undefined;
    }

    return undefined;
  }
}
