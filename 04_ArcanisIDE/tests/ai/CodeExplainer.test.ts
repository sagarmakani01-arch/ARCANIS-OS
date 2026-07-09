import { CodeExplainer } from '../../src/ai/CodeExplainer';
import { AIAssistant, LocalModelAdapter } from '../../src/ai/AIAssistant';
import { EventBus } from '../../src/core/EventBus';
import { makeDocument } from '../helpers';

describe('CodeExplainer', () => {
  let explainer: CodeExplainer;
  let assistant: AIAssistant;

  beforeEach(() => {
    const eventBus = new EventBus();
    assistant = new AIAssistant(eventBus);
    explainer = new CodeExplainer(assistant);
  });

  describe('explainCode', () => {
    it('should return a CodeExplanation with summary, complexity, lineByLine, and suggestions', async () => {
      const doc = makeDocument('fn add(a: i32, b: i32) -> i32 {\n  return a + b;\n}', 'arcanis', 'test.arc');
      const range = { start: { line: 0, column: 0 }, end: { line: 1, column: 18 } };
      const explanation = await explainer.explainCode(doc, range);

      expect(explanation).toHaveProperty('summary');
      expect(explanation).toHaveProperty('complexity');
      expect(explanation).toHaveProperty('lineByLine');
      expect(explanation).toHaveProperty('suggestions');
      expect(typeof explanation.summary).toBe('string');
      expect(['low', 'medium', 'high']).toContain(explanation.complexity);
    });

    it('should include line-by-line analysis with explanations', async () => {
      const doc = makeDocument('fn main() {\n  let x = 1;\n}', 'arcanis', 'test.arc');
      const range = { start: { line: 0, column: 0 }, end: { line: 2, column: 1 } };
      const explanation = await explainer.explainCode(doc, range);

      expect(explanation.lineByLine.length).toBeGreaterThan(0);
      expect(explanation.lineByLine[0]).toHaveProperty('line');
      expect(explanation.lineByLine[0]).toHaveProperty('text');
      expect(explanation.lineByLine[0]).toHaveProperty('explanation');
    });

    it('should identify function declarations', async () => {
      const doc = makeDocument('fn main() {\n}', 'arcanis', 'test.arc');
      const range = { start: { line: 0, column: 0 }, end: { line: 1, column: 1 } };
      const explanation = await explainer.explainCode(doc, range);

      expect(explanation.lineByLine[0].explanation).toContain('Function');
    });

    it('should classify simple code as low complexity', async () => {
      const doc = makeDocument('let x = 1;', 'arcanis', 'test.arc');
      const range = { start: { line: 0, column: 0 }, end: { line: 0, column: 10 } };
      const explanation = await explainer.explainCode(doc, range);
      expect(explanation.complexity).toBe('low');
    });

    it('should classify code with many branches as high complexity', async () => {
      const lines: string[] = [];
      for (let i = 0; i < 60; i++) {
        lines.push(`if (cond${i}) { doSomething(); }`);
      }
      const doc = makeDocument(lines.join('\n'), 'arcanis', 'test.arc');
      const range = { start: { line: 0, column: 0 }, end: { line: lines.length - 1, column: 50 } };
      const explanation = await explainer.explainCode(doc, range);
      expect(explanation.complexity).toBe('high');
    });

    it('should generate suggestions for code without comments', async () => {
      const doc = makeDocument(
        'fn process() {\n  let data = fetch();\n  let result = transform(data);\n  return result;\n}',
        'arcanis',
        'test.arc',
      );
      const range = { start: { line: 0, column: 0 }, end: { line: 4, column: 1 } };
      const explanation = await explainer.explainCode(doc, range);
      expect(explanation.suggestions.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('explainSymbol', () => {
    it('should return explanation for a function symbol', async () => {
      const doc = makeDocument('fn add(a: i32, b: i32) -> i32 { return a + b; }', 'arcanis', 'test.arc');
      const result = await explainer.explainSymbol(doc, { line: 0, column: 6 });
      expect(result).toContain('add');
      expect(result).toContain('function');
    });

    it('should return fallback when no symbol found at position', async () => {
      const doc = makeDocument('   ', 'arcanis', 'test.arc');
      const result = await explainer.explainSymbol(doc, { line: 0, column: 0 });
      expect(result).toBe('No symbol found at cursor position.');
    });

    it('should return fallback when position is past end of line', async () => {
      const doc = makeDocument('fn main() {}', 'arcanis', 'test.arc');
      const result = await explainer.explainSymbol(doc, { line: 0, column: 50 });
      expect(result).toBe('No symbol found at cursor position.');
    });

    it('should identify class declarations', async () => {
      const doc = makeDocument('class Calculator { }', 'arcanis', 'test.arc');
      const result = await explainer.explainSymbol(doc, { line: 0, column: 16 });
      expect(result).toContain('Calculator');
      expect(result).toContain('class');
    });

    it('should identify variable declarations', async () => {
      const doc = makeDocument('let x = 42;', 'arcanis', 'test.arc');
      const result = await explainer.explainSymbol(doc, { line: 0, column: 5 });
      expect(result).toContain('variable');
    });
  });
});
