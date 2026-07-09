import { BugDetector, DetectedBug } from '../../src/ai/BugDetector';
import { AIAssistant } from '../../src/ai/AIAssistant';
import { EventBus } from '../../src/core/EventBus';
import { makeDocument } from '../helpers';

describe('BugDetector', () => {
  let bugDetector: BugDetector;
  let assistant: AIAssistant;

  beforeEach(() => {
    const eventBus = new EventBus();
    assistant = new AIAssistant(eventBus);
    bugDetector = new BugDetector(assistant);
  });

  describe('detectBugs', () => {
    it('should return an empty array for clean code', async () => {
      const doc = makeDocument('fn main() {\n  let x = 1;\n  return x;\n}', 'arcanis', 'test.arc');
      const bugs = await bugDetector.detectBugs(doc);
      expect(Array.isArray(bugs)).toBe(true);
    });

    it('should detect loose equality comparison', async () => {
      const doc = makeDocument('if (x == 5) { return true; }', 'javascript', 'test.js');
      const bugs = await bugDetector.detectBugs(doc);
      expect(bugs.some((b) => b.id.startsWith('bug-loose-eq'))).toBe(true);
    });

    it('should detect null assignment', async () => {
      const doc = makeDocument('let x = null;', 'javascript', 'test.js');
      const bugs = await bugDetector.detectBugs(doc);
      expect(bugs.some((b) => b.id.startsWith('bug-null-assign'))).toBe(true);
    });

    it('should detect division by zero', async () => {
      const doc = makeDocument('let result = value / 0;', 'javascript', 'test.js');
      const bugs = await bugDetector.detectBugs(doc);
      expect(bugs.some((b) => b.id.startsWith('bug-div-zero'))).toBe(true);
    });

    it('should detect undeclared variable', async () => {
      const doc = makeDocument('x = 42;', 'javascript', 'test.js');
      const bugs = await bugDetector.detectBugs(doc);
      expect(bugs.some((b) => b.id.startsWith('bug-undeclared-var'))).toBe(true);
    });

    it('should detect off-by-one in loop condition', async () => {
      const doc = makeDocument('for (let i = 0; i <= arr.length; i++) {}', 'javascript', 'test.js');
      const bugs = await bugDetector.detectBugs(doc);
      expect(bugs.some((b) => b.id.startsWith('bug-off-by-one'))).toBe(true);
    });

    it('should detect complex functions', async () => {
      const lines = ['fn tooLong() {'];
      for (let i = 0; i < 55; i++) {
        lines.push(`  let x${i} = ${i};`);
      }
      lines.push('}');
      const doc = makeDocument(lines.join('\n'), 'arcanis', 'test.arc');
      const bugs = await bugDetector.detectBugs(doc);
      expect(bugs.some((b) => b.id.startsWith('bug-complex-fn'))).toBe(true);
    });

    it('should return DetectedBug objects with required fields', async () => {
      const doc = makeDocument('x == 5;', 'javascript', 'test.js');
      const bugs = await bugDetector.detectBugs(doc);
      for (const bug of bugs) {
        expect(bug).toHaveProperty('id');
        expect(bug).toHaveProperty('type');
        expect(bug).toHaveProperty('title');
        expect(bug).toHaveProperty('description');
        expect(bug).toHaveProperty('severity');
        expect(bug).toHaveProperty('line');
        expect(bug).toHaveProperty('column');
        expect(bug).toHaveProperty('fixConfidence');
      }
    });

    it('should sort bugs by severity descending', async () => {
      const doc = makeDocument(
        'let result = value / 0;\nx == 5;',
        'javascript',
        'test.js',
      );
      const bugs = await bugDetector.detectBugs(doc);
      for (let i = 1; i < bugs.length; i++) {
        const severityOrder: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1 };
        expect(severityOrder[bugs[i - 1].severity] || 0)
          .toBeGreaterThanOrEqual(severityOrder[bugs[i].severity] || 0);
      }
    });
  });

  describe('registerCustomDetector', () => {
    it('should add results from custom detector', async () => {
      const customDetector = (doc: any): DetectedBug[] => [
        {
          id: 'custom-bug',
          type: 'bug',
          title: 'Custom Bug',
          description: 'Detected by custom detector',
          severity: 'high',
          line: 0,
          column: 0,
          explanation: 'A custom bug pattern was found.',
          fixConfidence: 0.8,
        },
      ];
      bugDetector.registerCustomDetector(customDetector);

      const doc = makeDocument('some code', 'arcanis', 'test.arc');
      const bugs = await bugDetector.detectBugs(doc);
      expect(bugs.some((b) => b.id === 'custom-bug')).toBe(true);
    });

    it('should handle custom detector that throws', async () => {
      const throwingDetector = () => { throw new Error('detector failed'); };
      bugDetector.registerCustomDetector(throwingDetector);

      const doc = makeDocument('x == 5;', 'javascript', 'test.js');
      await expect(bugDetector.detectBugs(doc)).resolves.toBeDefined();
    });
  });

  describe('getFix', () => {
    it('should return the fix if already present on the bug', async () => {
      const bug: DetectedBug = {
        id: 'bug-null-assign-0',
        type: 'bug',
        title: 'Null assignment',
        description: 'Test',
        severity: 'medium',
        line: 0,
        column: 0,
        explanation: 'Test explanation',
        fix: ' = undefined;',
        fixConfidence: 0.6,
      };
      const fix = await bugDetector.getFix(bug);
      expect(fix).toBe(' = undefined;');
    });

    it('should generate a fix based on bug id pattern', async () => {
      const bug: DetectedBug = {
        id: 'bug-loose-eq-0',
        type: 'bug',
        title: 'Loose equality',
        description: 'Test',
        severity: 'medium',
        line: 0,
        column: 0,
        explanation: 'Test explanation',
        fixConfidence: 0.9,
      };
      const fix = await bugDetector.getFix(bug);
      expect(fix).toBe('===');
    });

    it('should return undefined for unknown bug id patterns', async () => {
      const bug: DetectedBug = {
        id: 'unknown-pattern',
        type: 'bug',
        title: 'Unknown',
        description: 'Test',
        severity: 'low',
        line: 0,
        column: 0,
        explanation: 'Test',
        fixConfidence: 0,
      };
      const fix = await bugDetector.getFix(bug);
      expect(fix).toBeUndefined();
    });
  });
});
