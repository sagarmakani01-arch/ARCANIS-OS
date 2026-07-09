import { DiagnosticEngine } from '../../src/editor/DiagnosticEngine';
import { DiagnosticSeverity } from '../../src/api/types';
import { makeDocument } from '../helpers';

describe('DiagnosticEngine', () => {
  let engine: DiagnosticEngine;

  beforeEach(() => {
    engine = new DiagnosticEngine();
  });

  describe('runDiagnostics', () => {
    it('should return empty array when no providers are registered', () => {
      const doc = makeDocument('some code', 'arcanis', 'test.arc');
      const diagnostics = engine.runDiagnostics(doc);
      expect(diagnostics).toEqual([]);
    });

    it('should return diagnostics from a registered provider', () => {
      engine.registerProvider('arcanis', () => [
        {
          range: { start: { line: 0, column: 0 }, end: { line: 0, column: 4 } },
          severity: DiagnosticSeverity.Error,
          message: 'Test error',
          source: 'test',
          code: 'T001',
        },
      ]);

      const doc = makeDocument('some code', 'arcanis', 'test.arc');
      const diagnostics = engine.runDiagnostics(doc);
      expect(diagnostics).toHaveLength(1);
      expect(diagnostics[0].message).toBe('Test error');
    });
  });

  describe('multiple providers', () => {
    it('should aggregate diagnostics from multiple providers', () => {
      engine.registerProvider('arcanis', () => [
        {
          range: { start: { line: 0, column: 0 }, end: { line: 0, column: 1 } },
          severity: DiagnosticSeverity.Error,
          message: 'Error A',
          source: 'test',
          code: 'A',
        },
      ]);
      engine.registerProvider('arcanis', () => [
        {
          range: { start: { line: 1, column: 0 }, end: { line: 1, column: 1 } },
          severity: DiagnosticSeverity.Warning,
          message: 'Warning B',
          source: 'test',
          code: 'B',
        },
      ]);

      const doc = makeDocument('aa\nbb', 'arcanis', 'test.arc');
      const diagnostics = engine.runDiagnostics(doc);
      expect(diagnostics).toHaveLength(2);
    });

    it('should not call providers for other languages', () => {
      const provider = jest.fn().mockReturnValue([]);
      engine.registerProvider('typescript', provider);

      const doc = makeDocument('code', 'arcanis', 'test.arc');
      engine.runDiagnostics(doc);
      expect(provider).not.toHaveBeenCalled();
    });
  });

  describe('deduplication', () => {
    it('should deduplicate identical diagnostics from multiple providers', () => {
      const diag = {
        range: { start: { line: 0, column: 0 }, end: { line: 0, column: 5 } },
        severity: DiagnosticSeverity.Error,
        message: 'Duplicate error',
        source: 'test',
        code: 'D001',
      };

      engine.registerProvider('arcanis', () => [diag]);
      engine.registerProvider('arcanis', () => [diag]);

      const doc = makeDocument('hello', 'arcanis', 'test.arc');
      const diagnostics = engine.runDiagnostics(doc);
      expect(diagnostics).toHaveLength(1);
    });

    it('should keep diagnostics that differ only in message', () => {
      const base = {
        range: { start: { line: 0, column: 0 }, end: { line: 0, column: 5 } },
        severity: DiagnosticSeverity.Error,
        source: 'test',
        code: 'E',
      };

      engine.registerProvider('arcanis', () => [
        { ...base, message: 'First' },
      ]);
      engine.registerProvider('arcanis', () => [
        { ...base, message: 'Second' },
      ]);

      const doc = makeDocument('hello', 'arcanis', 'test.arc');
      const diagnostics = engine.runDiagnostics(doc);
      expect(diagnostics).toHaveLength(2);
    });
  });

  describe('onDiagnosticsUpdated', () => {
    it('should emit an event when diagnostics are run', () => {
      const handler = jest.fn();
      engine.registerProvider('arcanis', () => [
        {
          range: { start: { line: 0, column: 0 }, end: { line: 0, column: 1 } },
          severity: DiagnosticSeverity.Error,
          message: 'Error',
          source: 'test',
          code: 'E',
        },
      ]);

      engine.onDiagnosticsUpdated(handler);

      const doc = makeDocument('x', 'arcanis', 'test.arc');
      engine.runDiagnostics(doc);

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          uri: doc.uri,
          diagnostics: expect.arrayContaining([
            expect.objectContaining({ message: 'Error' }),
          ]),
        }),
      );
    });
  });
});
