import { TextDocument, AISuggestion, WorkspaceEdit, TextEdit } from '../api/types';
import { AIAssistant } from './AIAssistant';

export interface ImprovementSuggestion extends AISuggestion {
  category: 'performance' | 'security' | 'style' | 'maintainability' | 'best-practice';
  impact: 'low' | 'medium' | 'high';
  effort: 'low' | 'medium' | 'high';
  autoFix?: boolean;
}

export class SuggestionEngine {
  private assistant: AIAssistant;

  constructor(assistant: AIAssistant) {
    this.assistant = assistant;
  }

  async analyze(document: TextDocument): Promise<ImprovementSuggestion[]> {
    const suggestions: ImprovementSuggestion[] = [];

    suggestions.push(...this.analyzePerformance(document));
    suggestions.push(...this.analyzeSecurity(document));
    suggestions.push(...this.analyzeStyle(document));
    suggestions.push(...this.analyzeMaintainability(document));
    suggestions.push(...this.analyzeBestPractices(document));

    const aiSuggestions = await this.assistant.getSuggestions(document);
    for (const s of aiSuggestions) {
      const existing = suggestions.find((x) => x.id === s.id);
      if (!existing) {
        suggestions.push(this.toImprovementSuggestion(s));
      }
    }

    return suggestions.sort((a, b) => {
      const impactOrder = { high: 3, medium: 2, low: 1 };
      return (impactOrder[b.impact] || 0) - (impactOrder[a.impact] || 0);
    });
  }

  async applySuggestion(suggestion: ImprovementSuggestion): Promise<WorkspaceEdit | undefined> {
    if (!suggestion.range || !suggestion.code) return undefined;

    const edit: TextEdit = {
      range: suggestion.range,
      newText: suggestion.code,
    };

    return { changes: { ['']: [edit] } };
  }

  private analyzePerformance(document: TextDocument): ImprovementSuggestion[] {
    const text = document.getText();
    const lines = text.split('\n');
    const suggestions: ImprovementSuggestion[] = [];

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();

      if (trimmed.includes('.forEach(')) {
        suggestions.push({
          id: `perf-for-of-${i}`,
          type: 'performance',
          category: 'performance',
          title: 'Use for...of instead of forEach',
          description: `Line ${i + 1} uses forEach which creates a function scope. Prefer for...of for better performance.`,
          severity: 'low',
          impact: 'low',
          effort: 'low',
          autoFix: true,
          range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
          explanation: 'for...of avoids function call overhead per iteration and allows break/continue.',
        });
      }

      if (trimmed.match(/new\s+String\(/) || trimmed.match(/new\s+Number\(/) || trimmed.match(/new\s+Boolean\(/)) {
        suggestions.push({
          id: `perf-no-wrapper-${i}`,
          type: 'performance',
          category: 'performance',
          title: 'Avoid primitive wrappers',
          description: `Line ${i + 1} uses a primitive wrapper object. Use literal syntax instead.`,
          severity: 'low',
          impact: 'low',
          effort: 'low',
          autoFix: true,
          range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
          explanation: 'Primitive wrappers create unnecessary object allocations and can cause type confusion.',
        });
      }

      if (trimmed.includes('string + ') || trimmed.match(/['"`].*\s\+\s/)) {
        suggestions.push({
          id: `perf-template-${i}`,
          type: 'performance',
          category: 'performance',
          title: 'Use template literals',
          description: `Line ${i + 1} uses string concatenation. Template literals are more readable and often faster.`,
          severity: 'low',
          impact: 'low',
          effort: 'low',
          autoFix: true,
          range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
          explanation: 'Template literals avoid intermediate string allocations and improve readability.',
        });
      }
    }

    return suggestions;
  }

  private analyzeSecurity(document: TextDocument): ImprovementSuggestion[] {
    const text = document.getText();
    const lines = text.split('\n');
    const suggestions: ImprovementSuggestion[] = [];

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();

      if (trimmed.match(/eval\s*\(/)) {
        suggestions.push({
          id: `sec-eval-${i}`,
          type: 'security',
          category: 'security',
          title: 'Avoid eval()',
          description: `Line ${i + 1} uses eval() which is a security risk.`,
          severity: 'high',
          impact: 'high',
          effort: 'medium',
          range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
          explanation: 'eval() executes arbitrary code and can lead to code injection attacks.',
        });
      }

      if (trimmed.match(/innerHTML\s*=/)) {
        suggestions.push({
          id: `sec-innerhtml-${i}`,
          type: 'security',
          category: 'security',
          title: 'Avoid innerHTML',
          description: `Line ${i + 1} sets innerHTML which can lead to XSS vulnerabilities.`,
          severity: 'high',
          impact: 'high',
          effort: 'medium',
          range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
          explanation: 'Use textContent or safe DOM APIs instead of innerHTML to prevent XSS.',
        });
      }

      if (trimmed.includes('password') || trimmed.includes('secret') || trimmed.includes('token') || trimmed.includes('apiKey')) {
        if (!trimmed.includes('process.env') && !trimmed.includes('config') && !trimmed.includes('env.')) {
          suggestions.push({
            id: `sec-secret-hardcode-${i}`,
            type: 'security',
            category: 'security',
            title: 'Hardcoded secret detected',
            description: `Line ${i + 1} may contain a hardcoded secret. Use environment variables instead.`,
            severity: 'high',
            impact: 'high',
            effort: 'low',
            range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
            explanation: 'Hardcoded secrets in source code can be exposed through version control.',
          });
        }
      }
    }

    return suggestions;
  }

  private analyzeStyle(document: TextDocument): ImprovementSuggestion[] {
    const text = document.getText();
    const lines = text.split('\n');
    const suggestions: ImprovementSuggestion[] = [];

    const hasTabs = lines.some((l) => l.startsWith('\t'));
    const hasSpaces = lines.some((l) => l.startsWith(' '));
    if (hasTabs && hasSpaces) {
      suggestions.push({
        id: 'style-mixed-indent',
        type: 'style',
        category: 'style',
        title: 'Mixed indentation',
        description: 'File uses both tabs and spaces for indentation. Pick one style.',
        severity: 'low',
        impact: 'low',
        effort: 'low',
        autoFix: true,
        explanation: 'Mixed indentation hurts readability and consistency.',
      });
    }

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trimRight();
      if (lines[i] !== trimmed) {
        suggestions.push({
          id: `style-trailing-${i}`,
          type: 'style',
          category: 'style',
          title: 'Trailing whitespace',
          description: `Line ${i + 1} has trailing whitespace.`,
          severity: 'low',
          impact: 'low',
          effort: 'low',
          autoFix: true,
          range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
          explanation: 'Trailing whitespace causes unnecessary diffs and can trigger linter warnings.',
        });
        break;
      }
    }

    const snakeCaseVars = text.match(/\b[a-z]+_[a-z]+\b/g);
    const camelCaseVars = text.match(/\b[a-z]+[A-Z]\w+\b/g);
    if (snakeCaseVars && camelCaseVars) {
      suggestions.push({
        id: 'style-inconsistent-naming',
        type: 'style',
        category: 'style',
        title: 'Inconsistent naming convention',
        description: 'File mixes snake_case and camelCase identifiers.',
        severity: 'low',
        impact: 'low',
        effort: 'medium',
        explanation: 'Stick to one naming convention (prefer camelCase for JS/TS, snake_case for Python).',
      });
    }

    return suggestions;
  }

  private analyzeMaintainability(document: TextDocument): ImprovementSuggestion[] {
    const text = document.getText();
    const lines = text.split('\n');
    const suggestions: ImprovementSuggestion[] = [];

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();

      if (trimmed.match(/(?:fn|function)\s+\w+\s*\([^)]*\)\s*\{/) && (i + 1 < lines.length)) {
        let funcBody = '';
        let depth = 1;
        let j = i + 1;
        while (j < lines.length && depth > 0) {
          for (const ch of lines[j]) {
            if (ch === '{') depth++;
            else if (ch === '}') depth--;
          }
          if (depth > 0) funcBody += lines[j] + '\n';
          j++;
        }
        const bodyLines = funcBody.split('\n').filter((l) => l.trim().length > 0);
        if (bodyLines.length > 30) {
          const nameMatch = trimmed.match(/(?:fn|function)\s+(\w+)/);
          const name = nameMatch ? nameMatch[1] : 'anonymous';
          suggestions.push({
            id: `maintain-large-fn-${name}`,
            type: 'improvement',
            category: 'maintainability',
            title: `Function '${name}' is too large`,
            description: `Function has ${bodyLines.length} lines. Consider extracting smaller helper functions.`,
            severity: 'medium',
            impact: 'medium',
            effort: 'high',
            explanation: 'Large functions are difficult to test, understand, and reuse.',
          });
          break;
        }
      }
    }

    const emptyCatch = text.match(/catch\s*\([^)]*\)\s*\{\s*\n\s*\}/);
    if (emptyCatch) {
      suggestions.push({
        id: 'maintain-empty-catch',
        type: 'improvement',
        category: 'maintainability',
        title: 'Empty catch block',
        description: 'An empty catch block swallows errors silently.',
        severity: 'medium',
        impact: 'medium',
        effort: 'low',
        autoFix: true,
        explanation: 'Swallowing exceptions hides bugs and makes debugging difficult.',
      });
    }

    const magicNumbers = text.match(/\b\d{4,}\b/g);
    if (magicNumbers) {
      suggestions.push({
        id: 'maintain-magic-numbers',
        type: 'improvement',
        category: 'maintainability',
        title: 'Magic numbers in code',
        description: 'Replace magic numbers with named constants for clarity.',
        severity: 'low',
        impact: 'low',
        effort: 'low',
        explanation: 'Named constants make code self-documenting and easier to modify.',
      });
    }

    return suggestions;
  }

  private analyzeBestPractices(document: TextDocument): ImprovementSuggestion[] {
    const text = document.getText();
    const lines = text.split('\n');
    const suggestions: ImprovementSuggestion[] = [];
    const textLower = text.toLowerCase();

    if (textLower.includes('callback') || textLower.includes('.then(')) {
      const hasAsync = textLower.includes('async ') || textLower.includes('await ');
      if (!hasAsync) {
        suggestions.push({
          id: 'bp-async-await',
          type: 'improvement',
          category: 'best-practice',
          title: 'Consider using async/await',
          description: 'The code uses callbacks or promises. async/await improves readability.',
          severity: 'medium',
          impact: 'medium',
          effort: 'medium',
          explanation: 'async/await leads to more readable and maintainable asynchronous code.',
        });
      }
    }

    const functionCount = (text.match(/(?:fn|function)\s+\w+/g) || []).length;
    const testPatterns = text.match(/\b(test|it|describe|assert)\s*\(/g);
    if (functionCount > 3 && !testPatterns) {
      suggestions.push({
        id: 'bp-no-tests',
        type: 'improvement',
        category: 'best-practice',
        title: 'Missing tests',
        description: 'File exports multiple functions but has no visible test code.',
        severity: 'low',
        impact: 'high',
        effort: 'high',
        explanation: 'Test coverage ensures code reliability and prevents regressions.',
      });
    }

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();
      if (trimmed.startsWith('// TODO') || trimmed.startsWith('// TODO:')) {
        suggestions.push({
          id: `bp-todo-${i}`,
          type: 'improvement',
          category: 'best-practice',
          title: 'Outstanding TODO',
          description: `Line ${i + 1}: ${trimmed.substring(trimmed.indexOf('TODO'))}`,
          severity: 'low',
          impact: 'low',
          effort: 'medium',
          range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
          explanation: 'TODOs indicate incomplete work that should be tracked or addressed.',
        });
      }
    }

    return suggestions;
  }

  private toImprovementSuggestion(suggestion: AISuggestion): ImprovementSuggestion {
    return {
      id: suggestion.id,
      type: suggestion.type,
      category: 'best-practice',
      title: suggestion.title,
      description: suggestion.description,
      severity: suggestion.severity,
      impact: 'medium',
      effort: 'medium',
      range: suggestion.range,
      code: suggestion.code,
      explanation: suggestion.explanation,
    };
  }
}
