import { TextDocument, Token } from '../api/types';
import { LanguageService } from './languages/LanguageService';

export interface TokenizedLine {
  lineNumber: number;
  tokens: Token[];
  text: string;
}

export class SyntaxHighlighter {
  private registry: Map<string, LanguageService>;
  private cache: Map<string, { version: number; lines: TokenizedLine[] }>;

  constructor(registry?: Map<string, LanguageService>) {
    this.registry = registry ?? new Map();
    this.cache = new Map();
  }

  highlight(document: TextDocument): TokenizedLine[] {
    const cached = this.cache.get(document.uri);
    if (cached && cached.version === document.version) {
      return cached.lines;
    }

    const languageService = this.registry.get(document.languageId);
    if (!languageService) {
      const result = this.buildEmptyLines(document);
      this.cache.set(document.uri, { version: document.version, lines: result });
      return result;
    }

    const tokens = languageService.provideTokens(document);
    const grouped = this.groupTokensByLine(tokens, document.lineCount);
    const result: TokenizedLine[] = [];

    for (let i = 0; i < document.lineCount; i++) {
      const text = document.lineAt(i)?.text ?? '';
      result.push({
        lineNumber: i,
        tokens: grouped.get(i) ?? [],
        text,
      });
    }

    this.cache.set(document.uri, { version: document.version, lines: result });
    return result;
  }

  registerLanguage(language: LanguageService): void {
    this.registry.set(language.languageId, language);
  }

  getLanguage(languageId: string): LanguageService | undefined {
    return this.registry.get(languageId);
  }

  invalidate(uri: string): void {
    this.cache.delete(uri);
  }

  private groupTokensByLine(tokens: Token[], lineCount: number): Map<number, Token[]> {
    const map = new Map<number, Token[]>();
    for (const token of tokens) {
      const line = token.range.start.line;
      if (!map.has(line)) {
        map.set(line, []);
      }
      map.get(line)!.push(token);
    }
    return map;
  }

  private buildEmptyLines(document: TextDocument): TokenizedLine[] {
    const result: TokenizedLine[] = [];
    for (let i = 0; i < document.lineCount; i++) {
      result.push({
        lineNumber: i,
        tokens: [],
        text: document.lineAt(i)?.text ?? '',
      });
    }
    return result;
  }
}
