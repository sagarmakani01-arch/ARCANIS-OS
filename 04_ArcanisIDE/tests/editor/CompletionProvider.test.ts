import { CompletionProvider } from '../../src/editor/CompletionProvider';
import { CompletionItemKind, CompletionTriggerKind } from '../../src/api/types';
import { makeDocument } from '../helpers';

describe('CompletionProvider', () => {
  let provider: CompletionProvider;

  beforeEach(() => {
    provider = new CompletionProvider();
  });

  describe('provideCompletions with no registered providers', () => {
    it('should return default completions', () => {
      const doc = makeDocument('', 'arcanis', 'test.arc');
      const completions = provider.provideCompletions(doc, { line: 0, column: 0 });

      expect(completions.length).toBeGreaterThan(0);
      expect(completions.some((c) => c.label === 'fn')).toBe(true);
      expect(completions.some((c) => c.label === 'let')).toBe(true);
      expect(completions.some((c) => c.label === 'if')).toBe(true);
    });

    it('should filter completions based on prefix', () => {
      const doc = makeDocument('if', 'arcanis', 'test.arc');
      const completions = provider.provideCompletions(doc, { line: 0, column: 2 });

      const allMatch = completions.every((c) =>
        (c.filterText ?? c.label).toLowerCase().startsWith('if'),
      );
      expect(allMatch).toBe(true);
      expect(completions.some((c) => c.label === 'if')).toBe(true);
      expect(completions.some((c) => c.label === 'ifelse')).toBe(true);
    });

    it('should return all items for empty document (no prefix)', () => {
      const doc = makeDocument('', 'arcanis', 'test.arc');
      const completions = provider.provideCompletions(doc, { line: 0, column: 0 });

      expect(completions).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ label: 'fn', kind: CompletionItemKind.Keyword }),
          expect.objectContaining({ label: 'ifelse', kind: CompletionItemKind.Snippet }),
        ]),
      );
    });

    it('should sort exact matches above prefix matches', () => {
      const doc = makeDocument('if', 'arcanis', 'test.arc');
      const completions = provider.provideCompletions(doc, { line: 0, column: 2 });

      const ifIndex = completions.findIndex((c) => c.label === 'if');
      const ifelseIndex = completions.findIndex((c) => c.label === 'ifelse');
      expect(ifIndex).toBeLessThan(ifelseIndex);
    });
  });

  describe('registerProvider', () => {
    it('should call registered provider and return its results', () => {
      const customProvider = jest.fn().mockReturnValue([
        { label: 'customItem', kind: CompletionItemKind.Function, detail: 'custom', insertText: 'customItem' },
      ]);
      provider.registerProvider('arcanis', customProvider);

      const doc = makeDocument('', 'arcanis', 'test.arc');
      const completions = provider.provideCompletions(doc, { line: 0, column: 0 });

      expect(customProvider).toHaveBeenCalledWith(doc, { line: 0, column: 0 }, undefined);
      expect(completions.some((c) => c.label === 'customItem')).toBe(true);
    });

    it('should aggregate results from multiple providers for same language', () => {
      const provider1 = jest.fn().mockReturnValue([
        { label: 'item1', kind: CompletionItemKind.Keyword, detail: 'p1', insertText: 'item1' },
      ]);
      const provider2 = jest.fn().mockReturnValue([
        { label: 'item2', kind: CompletionItemKind.Keyword, detail: 'p2', insertText: 'item2' },
      ]);
      provider.registerProvider('arcanis', provider1);
      provider.registerProvider('arcanis', provider2);

      const doc = makeDocument('', 'arcanis', 'test.arc');
      const completions = provider.provideCompletions(doc, { line: 0, column: 0 });

      expect(completions.some((c) => c.label === 'item1')).toBe(true);
      expect(completions.some((c) => c.label === 'item2')).toBe(true);
    });

    it('should not use default completions when a provider is registered', () => {
      const customProvider = jest.fn().mockReturnValue([
        { label: 'onlyCustom', kind: CompletionItemKind.Keyword, detail: 'c', insertText: 'c' },
      ]);
      provider.registerProvider('arcanis', customProvider);

      const doc = makeDocument('', 'arcanis', 'test.arc');
      const completions = provider.provideCompletions(doc, { line: 0, column: 0 });

      expect(completions.every((c) => c.label === 'onlyCustom')).toBe(true);
    });
  });

  describe('filtering', () => {
    it('should filter using filterText when available', () => {
      provider.registerProvider('test-lang', () => [
        { label: 'longLabel', filterText: 'short', kind: CompletionItemKind.Keyword, detail: 'd', insertText: 'longLabel' },
      ]);
      const doc = makeDocument('sh', 'test-lang', 'test.txt');
      const completions = provider.provideCompletions(doc, { line: 0, column: 2 });

      expect(completions.some((c) => c.label === 'longLabel')).toBe(true);
    });

    it('should return empty array when no completion matches prefix', () => {
      const doc = makeDocument('zzz', 'arcanis', 'test.arc');
      const completions = provider.provideCompletions(doc, { line: 0, column: 3 });
      expect(completions).toEqual([]);
    });
  });
});
