import { SyntaxHighlighter } from '../../src/editor/SyntaxHighlighter';
import { LanguageService } from '../../src/editor/languages/LanguageService';
import { TokenType } from '../../src/api/types';
import { makeDocument } from '../helpers';

describe('SyntaxHighlighter', () => {
  let highlighter: SyntaxHighlighter;

  beforeEach(() => {
    highlighter = new SyntaxHighlighter();
  });

  describe('highlight without language service', () => {
    it('should return empty tokenized lines', () => {
      const doc = makeDocument('hello world', 'unknown', 'test.txt');
      const lines = highlighter.highlight(doc);
      expect(lines).toHaveLength(1);
      expect(lines[0]).toEqual({
        lineNumber: 0,
        tokens: [],
        text: 'hello world',
      });
    });

    it('should return one TokenizedLine per document line', () => {
      const doc = makeDocument('line1\nline2\nline3', 'unknown', 'test.txt');
      const lines = highlighter.highlight(doc);
      expect(lines).toHaveLength(3);
      expect(lines[0].text).toBe('line1');
      expect(lines[1].text).toBe('line2');
      expect(lines[2].text).toBe('line3');
    });
  });

  describe('registerLanguage', () => {
    it('should register a language service', () => {
      const service = new (class extends LanguageService {
        constructor() {
          super('test-lang');
        }
      })();
      highlighter.registerLanguage(service);
      expect(highlighter.getLanguage('test-lang')).toBe(service);
    });

    it('should return undefined for unregistered language', () => {
      expect(highlighter.getLanguage('nonexistent')).toBeUndefined();
    });

    it('should override existing language registration', () => {
      const service1 = new (class extends LanguageService {
        constructor() {
          super('test-lang');
        }
      })();
      const service2 = new (class extends LanguageService {
        constructor() {
          super('test-lang');
        }
      })();
      highlighter.registerLanguage(service1);
      highlighter.registerLanguage(service2);
      expect(highlighter.getLanguage('test-lang')).toBe(service2);
    });
  });

  describe('highlight with language service', () => {
    it('should call provideTokens on the language service', () => {
      const service = new (class extends LanguageService {
        constructor() {
          super('test-lang');
        }
        provideTokens() {
          return [
            {
              type: TokenType.Keyword,
              value: 'fn',
              range: { start: { line: 0, column: 0 }, end: { line: 0, column: 2 } },
            },
          ];
        }
      })();
      highlighter.registerLanguage(service);
      const doc = makeDocument('fn main', 'test-lang', 'test.txt');
      const lines = highlighter.highlight(doc);
      expect(lines[0].tokens).toHaveLength(1);
      expect(lines[0].tokens[0]).toMatchObject({
        type: TokenType.Keyword,
        value: 'fn',
      });
    });

    it('should group tokens by line number', () => {
      const service = new (class extends LanguageService {
        constructor() {
          super('multi-lang');
        }
        provideTokens() {
          return [
            { type: TokenType.Keyword, value: 'fn', range: { start: { line: 0, column: 0 }, end: { line: 0, column: 2 } } },
            { type: TokenType.Identifier, value: 'foo', range: { start: { line: 0, column: 3 }, end: { line: 0, column: 6 } } },
            { type: TokenType.Keyword, value: 'let', range: { start: { line: 1, column: 0 }, end: { line: 1, column: 3 } } },
          ];
        }
      })();
      highlighter.registerLanguage(service);
      const doc = makeDocument('fn foo\nlet x', 'multi-lang', 'test.txt');
      const lines = highlighter.highlight(doc);
      expect(lines[0].tokens).toHaveLength(2);
      expect(lines[1].tokens).toHaveLength(1);
    });
  });

  describe('caching', () => {
    it('should return cached result for unchanged document version', () => {
      const provideTokens = jest.fn().mockReturnValue([]);
      const service = new (class extends LanguageService {
        constructor() {
          super('cached-lang');
        }
        provideTokens = provideTokens;
      })();
      highlighter.registerLanguage(service);
      const doc = makeDocument('test', 'cached-lang', 'file.txt', 1);
      const firstCall = highlighter.highlight(doc);
      const secondCall = highlighter.highlight(doc);
      expect(provideTokens).toHaveBeenCalledTimes(1);
      expect(secondCall).toBe(firstCall);
    });

    it('should re-highlight when document version changes', () => {
      const provideTokens = jest.fn().mockReturnValue([]);
      const service = new (class extends LanguageService {
        constructor() {
          super('cached-lang');
        }
        provideTokens = provideTokens;
      })();
      highlighter.registerLanguage(service);
      const doc1 = makeDocument('v1', 'cached-lang', 'file.txt', 1);
      highlighter.highlight(doc1);
      const doc2 = makeDocument('v2', 'cached-lang', 'file.txt', 2);
      highlighter.highlight(doc2);
      expect(provideTokens).toHaveBeenCalledTimes(2);
    });
  });

  describe('invalidate', () => {
    it('should clear cache for a given URI', () => {
      const provideTokens = jest.fn().mockReturnValue([]);
      const service = new (class extends LanguageService {
        constructor() {
          super('lang');
        }
        provideTokens = provideTokens;
      })();
      highlighter.registerLanguage(service);
      const doc = makeDocument('test', 'lang', 'file.txt', 1);
      highlighter.highlight(doc);
      highlighter.invalidate('file:///file.txt');
      highlighter.highlight(doc);
      expect(provideTokens).toHaveBeenCalledTimes(2);
    });
  });
});
