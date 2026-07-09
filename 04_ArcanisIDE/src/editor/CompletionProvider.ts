import {
  TextDocument, Position, CompletionItem, CompletionItemKind, CompletionContext,
} from '../api/types';

export type CompletionProviderFn = (
  document: TextDocument,
  position: Position,
  context?: CompletionContext,
) => CompletionItem[];

export class CompletionProvider {
  private providers = new Map<string, CompletionProviderFn[]>();

  private static readonly DEFAULT_COMPLETIONS: CompletionItem[] = [
    { label: 'fn', kind: CompletionItemKind.Keyword, detail: 'function definition', insertText: 'fn' },
    { label: 'let', kind: CompletionItemKind.Keyword, detail: 'variable binding', insertText: 'let' },
    { label: 'const', kind: CompletionItemKind.Keyword, detail: 'constant declaration', insertText: 'const' },
    { label: 'if', kind: CompletionItemKind.Keyword, detail: 'if statement', insertText: 'if' },
    { label: 'else', kind: CompletionItemKind.Keyword, detail: 'else clause', insertText: 'else' },
    { label: 'for', kind: CompletionItemKind.Keyword, detail: 'for loop', insertText: 'for' },
    { label: 'while', kind: CompletionItemKind.Keyword, detail: 'while loop', insertText: 'while' },
    { label: 'return', kind: CompletionItemKind.Keyword, detail: 'return expression', insertText: 'return' },
    { label: 'match', kind: CompletionItemKind.Keyword, detail: 'match expression', insertText: 'match' },
    { label: 'import', kind: CompletionItemKind.Keyword, detail: 'import statement', insertText: 'import' },
    { label: 'export', kind: CompletionItemKind.Keyword, detail: 'export statement', insertText: 'export' },
    { label: 'class', kind: CompletionItemKind.Keyword, detail: 'class declaration', insertText: 'class' },
    { label: 'struct', kind: CompletionItemKind.Keyword, detail: 'struct definition', insertText: 'struct' },
    { label: 'enum', kind: CompletionItemKind.Keyword, detail: 'enum definition', insertText: 'enum' },
    { label: 'true', kind: CompletionItemKind.Keyword, detail: 'boolean true', insertText: 'true' },
    { label: 'false', kind: CompletionItemKind.Keyword, detail: 'boolean false', insertText: 'false' },
    { label: 'null', kind: CompletionItemKind.Keyword, detail: 'null value', insertText: 'null' },
    {
      label: 'ifelse',
      kind: CompletionItemKind.Snippet,
      detail: 'if-else statement',
      insertText: 'if ${1:condition} {\n  ${2:}\n} else {\n  ${3:}\n}',
    },
    {
      label: 'forloop',
      kind: CompletionItemKind.Snippet,
      detail: 'for loop snippet',
      insertText: 'for ${1:item} in ${2:iterable} {\n  ${3:}\n}',
    },
  ];

  provideCompletions(
    document: TextDocument,
    position: Position,
    context?: CompletionContext,
  ): CompletionItem[] {
    const line = document.lineAt(position.line);
    if (!line) return [];

    const prefix = line.text.substring(0, position.column).match(/[\w.]+$/)?.[0] ?? '';
    const allProviders = this.providers.get(document.languageId) ?? [];
    const defaultProvider = (_doc: TextDocument) => CompletionProvider.DEFAULT_COMPLETIONS;

    let items: CompletionItem[] = [];

    if (allProviders.length === 0) {
      items = defaultProvider(document);
    } else {
      for (const provider of allProviders) {
        const results = provider(document, position, context);
        items.push(...results);
      }
    }

    const filtered = prefix
      ? items.filter((item) => {
          const matchText = item.filterText ?? item.label;
          return matchText.toLowerCase().startsWith(prefix.toLowerCase());
        })
      : items;

    return filtered.sort((a, b) => {
      const scoreA = this.getSortScore(a, prefix);
      const scoreB = this.getSortScore(b, prefix);
      return scoreB - scoreA;
    });
  }

  registerProvider(languageId: string, provider: CompletionProviderFn): void {
    if (!this.providers.has(languageId)) {
      this.providers.set(languageId, []);
    }
    this.providers.get(languageId)!.push(provider);
  }

  private getSortScore(item: CompletionItem, prefix: string): number {
    const text = item.filterText ?? item.label;

    if (text === prefix) return 100;
    if (text.startsWith(prefix)) return 50;

    if (item.kind === CompletionItemKind.Keyword) return 30;
    if (item.kind === CompletionItemKind.Snippet) return 10;

    return 0;
  }
}
