import {
  TextDocument, Token, Position, Range, CompletionItem, CompletionItemKind,
  CompletionContext, Diagnostic, DiagnosticSeverity, TokenType, CodeAction,
  CodeActionContext, WorkspaceEdit, TextEdit, FormattingOptions, Location, SignatureHelp,
} from '../../api/types';
import { LanguageService } from './LanguageService';
import { Tokenizer, TokenRule } from './Tokenizer';

const KEYWORDS = [
  'fn', 'let', 'mut', 'if', 'else', 'for', 'while', 'return',
  'struct', 'enum', 'trait', 'impl', 'pub', 'use', 'mod', 'type',
  'match', 'async', 'await', 'yield', 'import', 'export', 'as', 'in',
  'where', 'self', 'Super', 'True', 'False', 'None',
];

const TYPES = [
  'i32', 'i64', 'f32', 'f64', 'bool', 'string', 'char', 'void',
  'Array', 'Map', 'Option', 'Result',
];

const BUILTIN_FUNCTIONS = [
  'print', 'println', 'assert', 'len', 'push', 'pop', 'map', 'filter', 'reduce',
];

export class ArcanisLang extends LanguageService {
  private tokenizer: Tokenizer;

  constructor() {
    super('arcanis');

    const rules: TokenRule[] = [
      { pattern: /\/\/[^\n]*/, type: TokenType.Comment },
      { pattern: /\/\*[\s\S]*?\*\//, type: TokenType.Comment },
      { pattern: /"(?:[^"\\]|\\.)*"/, type: TokenType.String },
      { pattern: /'(?:[^'\\]|\\.)*'/, type: TokenType.String },
      { pattern: /\b(?:0b[01]+|0o[0-7]+|0x[0-9a-fA-F]+|\d+(?:\.\d+)?(?:e[+-]?\d+)?)\b/, type: TokenType.Number },
      { pattern: /\b(?:fn|let|mut|if|else|for|while|return|struct|enum|trait|impl|pub|use|mod|type|match|async|await|yield|import|export|as|in|where|self|Super|True|False|None)\b/, type: TokenType.Keyword },
      { pattern: /\b(?:i32|i64|f32|f64|bool|string|char|void|Array|Map|Option|Result)\b/, type: TokenType.Type },
      { pattern: /\b(?:print|println|assert|len|push|pop|map|filter|reduce)\b/, type: TokenType.Function },
      { pattern: /[+\-*/%=<>!&|^~]=?/, type: TokenType.Operator },
      { pattern: /[{}()\[\];,:.]/, type: TokenType.Punctuation },
      { pattern: /\s+/, type: TokenType.Whitespace },
      { pattern: /\b[a-zA-Z_]\w*\b/, type: TokenType.Identifier },
    ];

    this.tokenizer = new Tokenizer('arcanis', rules);
  }

  provideTokens(document: TextDocument): Token[] {
    return this.tokenizer.tokenize(document.getText());
  }

  provideCompletions(document: TextDocument, position: Position, context?: CompletionContext): CompletionItem[] {
    const items: CompletionItem[] = [];

    for (const kw of KEYWORDS) {
      items.push({
        label: kw,
        kind: CompletionItemKind.Keyword,
        detail: 'keyword',
        insertText: kw,
      });
    }

    for (const t of TYPES) {
      items.push({
        label: t,
        kind: CompletionItemKind.TypeParameter,
        detail: 'type',
        insertText: t,
      });
    }

    for (const fn of BUILTIN_FUNCTIONS) {
      items.push({
        label: fn,
        kind: CompletionItemKind.Function,
        detail: 'builtin function',
        insertText: `${fn}()`,
      });
    }

    items.push({
      label: 'fn',
      kind: CompletionItemKind.Snippet,
      detail: 'function definition',
      insertText: 'fn ${1:name}(${2:params}) {\n  ${3:}\n}',
    });

    items.push({
      label: 'if',
      kind: CompletionItemKind.Snippet,
      detail: 'if statement',
      insertText: 'if ${1:condition} {\n  ${2:}\n}',
    });

    items.push({
      label: 'for',
      kind: CompletionItemKind.Snippet,
      detail: 'for loop',
      insertText: 'for ${1:item} in ${2:iterable} {\n  ${3:}\n}',
    });

    items.push({
      label: 'while',
      kind: CompletionItemKind.Snippet,
      detail: 'while loop',
      insertText: 'while ${1:condition} {\n  ${2:}\n}',
    });

    items.push({
      label: 'match',
      kind: CompletionItemKind.Snippet,
      detail: 'match expression',
      insertText: 'match ${1:value} {\n  ${2:pattern} => ${3:},\n}',
    });

    return items;
  }

  provideDiagnostics(document: TextDocument): Diagnostic[] {
    const diagnostics: Diagnostic[] = [];
    const text = document.getText();
    const lines = text.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      const unclosedString = line.match(/(?<!\\)"/g);
      if (unclosedString && unclosedString.length % 2 !== 0) {
        const lastQuote = line.lastIndexOf('"');
        diagnostics.push({
          range: {
            start: { line: i, column: lastQuote },
            end: { line: i, column: lastQuote + 1 },
          },
          severity: DiagnosticSeverity.Error,
          message: 'Unclosed string literal',
          source: 'arcanis',
          code: 'E001',
        });
      }

      const unclosedChar = line.match(/(?<!\\)'/g);
      if (unclosedChar && unclosedChar.length % 2 !== 0) {
        const lastQuote = line.lastIndexOf("'");
        diagnostics.push({
          range: {
            start: { line: i, column: lastQuote },
            end: { line: i, column: lastQuote + 1 },
          },
          severity: DiagnosticSeverity.Error,
          message: 'Unclosed character literal',
          source: 'arcanis',
          code: 'E002',
        });
      }
    }

    const stack: { char: string; line: number; column: number }[] = [];
    const pairs: Record<string, string> = { '{': '}', '[': ']', '(': ')' };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      for (let j = 0; j < line.length; j++) {
        const ch = line[j];
        if (ch === '"' || ch === "'") {
          const quote = ch;
          j++;
          while (j < line.length) {
            if (line[j] === '\\') { j += 2; continue; }
            if (line[j] === quote) break;
            j++;
          }
          continue;
        }
        if (ch === '/' && line[j + 1] === '/') break;
        if (pairs[ch]) {
          stack.push({ char: ch, line: i, column: j });
        } else if (Object.values(pairs).includes(ch)) {
          if (stack.length === 0) {
            diagnostics.push({
              range: { start: { line: i, column: j }, end: { line: i, column: j + 1 } },
              severity: DiagnosticSeverity.Error,
              message: `Unexpected closing bracket '${ch}'`,
              source: 'arcanis',
              code: 'E003',
            });
          } else {
            const open = stack.pop()!;
            if (pairs[open.char] !== ch) {
              diagnostics.push({
                range: { start: { line: i, column: j }, end: { line: i, column: j + 1 } },
                severity: DiagnosticSeverity.Error,
                message: `Mismatched bracket: expected '${pairs[open.char]}' but found '${ch}'`,
                source: 'arcanis',
                code: 'E004',
              });
            }
          }
        }
      }
    }

    for (const unclosed of stack) {
      diagnostics.push({
        range: {
          start: { line: unclosed.line, column: unclosed.column },
          end: { line: unclosed.line, column: unclosed.column + 1 },
        },
        severity: DiagnosticSeverity.Error,
        message: `Unclosed bracket '${unclosed.char}'`,
        source: 'arcanis',
        code: 'E005',
      });
    }

    return diagnostics;
  }

  provideHover(document: TextDocument, position: Position): string | undefined {
    const line = document.lineAt(position.line);
    if (!line) return undefined;

    const wordMatch = line.text.substring(position.column).match(/^\w+/);
    const word = wordMatch ? wordMatch[0] : undefined;
    if (!word) return undefined;

    if (KEYWORDS.includes(word)) {
      return `**${word}** — ArcanisLang keyword`;
    }
    if (TYPES.includes(word)) {
      return `**${word}** — ArcanisLang type`;
    }
    if (BUILTIN_FUNCTIONS.includes(word)) {
      return `**${word}** — ArcanisLang builtin function`;
    }

    return undefined;
  }

  private getFileExtensions(): string[] {
    return ['.arc', '.arcanis'];
  }
}
