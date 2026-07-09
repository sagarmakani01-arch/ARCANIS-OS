import { TextDocument, AISuggestion } from '../api/types';
import { AIAssistant } from './AIAssistant';

export interface DetectedBug extends AISuggestion {
  line: number;
  column: number;
  fix?: string;
  fixConfidence: number;
}

export type BugDetectorFn = (document: TextDocument) => DetectedBug[];

export class BugDetector {
  private assistant: AIAssistant;
  private customDetectors: BugDetectorFn[] = [];

  constructor(assistant: AIAssistant) {
    this.assistant = assistant;
  }

  registerCustomDetector(detector: BugDetectorFn): void {
    this.customDetectors.push(detector);
  }

  async detectBugs(document: TextDocument): Promise<DetectedBug[]> {
    const allBugs: DetectedBug[] = [];

    const patternBugs = this.patternDetection(document);
    allBugs.push(...patternBugs);

    const complexityBugs = this.complexityDetection(document);
    allBugs.push(...complexityBugs);

    for (const detector of this.customDetectors) {
      try {
        const results = detector(document);
        allBugs.push(...results);
      } catch (err) {
        console.error('[BugDetector] Custom detector failed:', err);
      }
    }

    const aiSuggestions = await this.assistant.detectBugs(document);
    for (const s of aiSuggestions) {
      const existing = allBugs.find((b) => b.id === s.id);
      if (!existing) {
        allBugs.push(this.toDetectedBug(s));
      }
    }

    const merged = this.deduplicate(allBugs);
    return merged.sort((a, b) => {
      const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0);
    });
  }

  async getFix(bug: DetectedBug): Promise<string | undefined> {
    if (bug.fix) return bug.fix;

    const fix = this.generateFix(bug);
    return fix;
  }

  private patternDetection(document: TextDocument): DetectedBug[] {
    const text = document.getText();
    const bugs: DetectedBug[] = [];
    const lines = text.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();
      const line = i;
      const col = lines[i].indexOf(trimmed);

      const nullAssign = trimmed.match(/=\s*null\s*;/);
      if (nullAssign) {
        bugs.push({
          id: `bug-null-assign-${i}`,
          type: 'bug',
          title: 'Null assignment',
          description: `Line ${i + 1} assigns null directly.`,
          severity: 'medium',
          line,
          column: col + nullAssign.index!,
          explanation: 'Assigning null directly can lead to null reference errors later.',
          fix: ' = undefined;',
          fixConfidence: 0.6,
        });
      }

      const looseEq = trimmed.match(/[^!=]==[^=]/);
      if (looseEq && !trimmed.includes('===')) {
        bugs.push({
          id: `bug-loose-eq-${i}`,
          type: 'bug',
          title: 'Loose equality comparison',
          description: `Line ${i + 1} uses '==' instead of '==='.`,
          severity: 'medium',
          line,
          column: col + looseEq.index!,
          explanation: 'Loose equality can cause unexpected type coercion bugs in JavaScript/TypeScript.',
          fixConfidence: 0.9,
        });
      }

      const undeclaredVar = trimmed.match(/^(\w+)\s*=\s*/);
      if (undeclaredVar && !trimmed.startsWith('let ') && !trimmed.startsWith('const ') && !trimmed.startsWith('var ')) {
        bugs.push({
          id: `bug-undeclared-var-${i}`,
          type: 'bug',
          title: 'Undeclared variable',
          description: `Line ${i + 1}: '${undeclaredVar[1]}' is assigned without declaration.`,
          severity: 'high',
          line,
          column: col,
          explanation: 'Variables should be declared with let or const to avoid globals.',
          fix: `let ${undeclaredVar[1]} =`,
          fixConfidence: 0.8,
        });
      }

      const divByZero = trimmed.match(/\/\s*0\b/);
      if (divByZero) {
        bugs.push({
          id: `bug-div-zero-${i}`,
          type: 'bug',
          title: 'Division by zero',
          description: `Line ${i + 1} performs division by zero literal.`,
          severity: 'critical',
          line,
          column: col + divByZero.index!,
          explanation: 'Division by zero will result in Infinity or NaN at runtime.',
          fixConfidence: 0.95,
        });
      }

      if (trimmed.match(/for\s*\(\s*(let|var)\s+\w+\s*=\s*0\s*;\s*\w+\s*<=\s*\w+\./)) {
        bugs.push({
          id: `bug-off-by-one-${i}`,
          type: 'bug',
          title: 'Potential off-by-one error',
          description: `Line ${i + 1} uses <= in loop condition; consider using < to avoid extra iteration.`,
          severity: 'low',
          line,
          column: col,
          explanation: 'Array indices go from 0 to length-1. Using <= may access beyond bounds.',
          fixConfidence: 0.7,
        });
      }
    }

    return bugs;
  }

  private complexityDetection(document: TextDocument): DetectedBug[] {
    const text = document.getText();
    const bugs: DetectedBug[] = [];
    const lines = text.split('\n');

    let currentFunctionStart = -1;
    let currentFunctionName = '';
    let braceDepth = 0;
    let functionDepth = 0;

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();

      const fnMatch = trimmed.match(/(?:fn|function)\s+(\w+)/);
      if (fnMatch) {
        currentFunctionStart = i;
        currentFunctionName = fnMatch[1];
        functionDepth = 0;
      }

      for (const ch of trimmed) {
        if (ch === '{') braceDepth++;
        else if (ch === '}') braceDepth--;
      }

      if (currentFunctionStart >= 0) {
        functionDepth++;
        if (braceDepth === 0 && functionDepth > 1) {
          const funcLines = i - currentFunctionStart;
          if (funcLines > 50) {
            bugs.push({
              id: `bug-complex-fn-${currentFunctionName}`,
              type: 'bug',
              title: `Function '${currentFunctionName}' is too complex`,
              description: `Function spans ${funcLines} lines. Consider refactoring.`,
              severity: 'medium',
              line: currentFunctionStart,
              column: 0,
              explanation: 'Large functions are harder to understand, test, and maintain.',
              fixConfidence: 0.5,
            });
          }
          currentFunctionStart = -1;
          currentFunctionName = '';
        }
      }
    }

    return bugs;
  }

  private toDetectedBug(suggestion: AISuggestion): DetectedBug {
    return {
      id: suggestion.id,
      type: suggestion.type,
      title: suggestion.title,
      description: suggestion.description,
      severity: suggestion.severity,
      range: suggestion.range,
      code: suggestion.code,
      explanation: suggestion.explanation,
      line: suggestion.range?.start.line ?? 0,
      column: suggestion.range?.start.column ?? 0,
      fixConfidence: 0.4,
    };
  }

  private generateFix(bug: DetectedBug): string | undefined {
    if (bug.fix) return bug.fix;

    const id = bug.id;
    if (id.startsWith('bug-loose-eq')) return '===';
    if (id.startsWith('bug-div-zero')) return 'Ensure denominator is non-zero before division';
    if (id.startsWith('bug-off-by-one')) return 'Change <= to <';
    if (id.startsWith('bug-null-assign')) return 'Consider using undefined or a default value';
    if (id.startsWith('bug-null-ref')) return 'Add a null check before accessing properties';
    if (id.startsWith('bug-undeclared-var')) return 'Add let, const, or var keyword';

    return undefined;
  }

  private deduplicate(bugs: DetectedBug[]): DetectedBug[] {
    const seen = new Set<string>();
    return bugs.filter((b) => {
      if (seen.has(b.id)) return false;
      seen.add(b.id);
      return true;
    });
  }
}
