import { RefactoringEngine } from '../../src/editor/RefactoringEngine';
import { LanguageService } from '../../src/editor/languages/LanguageService';
import {
  CodeActionKind, CodeActionContext, DiagnosticSeverity, Range,
} from '../../src/api/types';
import { makeDocument } from '../helpers';

describe('RefactoringEngine', () => {
  let engine: RefactoringEngine;

  beforeEach(() => {
    engine = new RefactoringEngine();
  });

  describe('provideCodeActions', () => {
    it('should return empty array when no language service or provider is registered', () => {
      const doc = makeDocument('fn main() {}', 'arcanis', 'test.arc');
      const range: Range = { start: { line: 0, column: 0 }, end: { line: 0, column: 13 } };
      const context: CodeActionContext = { diagnostics: [] };
      const actions = engine.provideCodeActions(doc, range, context);
      expect(actions).toEqual([]);
    });

    it('should return actions from the language service', () => {
      const service = new (class extends LanguageService {
        constructor() {
          super('test-lang');
        }
        provideCodeActions() {
          return [
            {
              title: 'Extract function',
              kind: CodeActionKind.RefactorExtract,
            },
          ];
        }
      })();
      engine.registerLanguageService(service);

      const doc = makeDocument('fn main() {}', 'test-lang', 'test.txt');
      const actions = engine.provideCodeActions(
        doc,
        { start: { line: 0, column: 0 }, end: { line: 0, column: 13 } },
        { diagnostics: [] },
      );
      expect(actions).toHaveLength(1);
      expect(actions[0].title).toBe('Extract function');
      expect(actions[0].kind).toBe(CodeActionKind.RefactorExtract);
    });

    it('should include diagnostic-based quick fix actions', () => {
      const diag = {
        range: { start: { line: 0, column: 0 }, end: { line: 0, column: 2 } },
        severity: DiagnosticSeverity.Error,
        message: 'Unexpected token',
        source: 'test',
        code: 'E001',
      };
      const doc = makeDocument('fn', 'test-lang', 'test.txt');
      const actions = engine.provideCodeActions(
        doc,
        { start: { line: 0, column: 0 }, end: { line: 0, column: 2 } },
        { diagnostics: [diag] },
      );
      expect(actions).toHaveLength(1);
      expect(actions[0].title).toBe('Fix: Unexpected token');
      expect(actions[0].kind).toBe(CodeActionKind.QuickFix);
    });

    it('should return actions from custom code action providers', () => {
      engine.registerCodeActionProvider('test-lang', () => [
        {
          title: 'Custom action',
          kind: CodeActionKind.Refactor,
        },
      ]);
      const doc = makeDocument('code', 'test-lang', 'test.txt');
      const actions = engine.provideCodeActions(
        doc,
        { start: { line: 0, column: 0 }, end: { line: 0, column: 4 } },
        { diagnostics: [] },
      );
      expect(actions).toHaveLength(1);
      expect(actions[0].title).toBe('Custom action');
    });
  });

  describe('renameSymbol', () => {
    it('should return undefined when no language service or rename provider is registered', () => {
      const doc = makeDocument('let x = 1;', 'test-lang', 'test.txt');
      const result = engine.renameSymbol(doc, { line: 0, column: 4 }, 'y');
      expect(result).toBeUndefined();
    });

    it('should return workspace edit from language service', () => {
      const service = new (class extends LanguageService {
        constructor() {
          super('test-lang');
        }
        provideRename() {
          return {
            changes: {
              'file:///test.txt': [
                { range: { start: { line: 0, column: 4 }, end: { line: 0, column: 5 } }, newText: 'y' },
              ],
            },
          };
        }
      })();
      engine.registerLanguageService(service);

      const doc = makeDocument('let x = 1;', 'test-lang', 'test.txt');
      const result = engine.renameSymbol(doc, { line: 0, column: 4 }, 'y');
      expect(result).toBeDefined();
      expect(result!.changes['file:///test.txt']).toHaveLength(1);
      expect(result!.changes['file:///test.txt'][0].newText).toBe('y');
    });

    it('should use custom rename provider if language service returns undefined', () => {
      const service = new (class extends LanguageService {
        constructor() {
          super('test-lang');
        }
      })();
      engine.registerLanguageService(service);
      engine.registerRenameProvider('test-lang', () => ({
        changes: { 'file:///test.txt': [{ range: { start: { line: 0, column: 0 }, end: { line: 0, column: 1 } }, newText: 'z' }] },
      }));

      const doc = makeDocument('a = 1;', 'test-lang', 'test.txt');
      const result = engine.renameSymbol(doc, { line: 0, column: 0 }, 'z');
      expect(result).toBeDefined();
      expect(result!.changes['file:///test.txt'][0].newText).toBe('z');
    });
  });

  describe('extractFunction', () => {
    it('should return undefined for empty range', () => {
      const doc = makeDocument('', 'test-lang', 'test.txt');
      const result = engine.extractFunction(
        doc,
        { start: { line: 0, column: 0 }, end: { line: 0, column: 0 } },
        'newFunc',
      );
      expect(result).toBeUndefined();
    });

    it('should create function from selected text', () => {
      const doc = makeDocument('let x = 1;\nlet y = 2;', 'test-lang', 'test.txt');
      const result = engine.extractFunction(
        doc,
        { start: { line: 0, column: 0 }, end: { line: 1, column: 10 } },
        'init',
      );
      expect(result).toBeDefined();
      expect(result!.changes['file:///test.txt']).toHaveLength(2);
    });
  });

  describe('organizeImports', () => {
    it('should return empty array when no imports exist', () => {
      const doc = makeDocument('let x = 1;', 'test-lang', 'test.txt');
      const edits = engine.organizeImports(doc);
      expect(edits).toEqual([]);
    });

    it('should sort import lines alphabetically', () => {
      const doc = makeDocument(
        'import z\nimport a\nimport m\nlet x = 1;',
        'test-lang',
        'test.txt',
      );
      const edits = engine.organizeImports(doc);
      expect(edits).toHaveLength(1);
      expect(edits[0].newText).toBe('import a\nimport m\nimport z\n');
    });
  });
});
