import {
  TextDocument, Range, Position, AISuggestion, AICompletionContext,
  AICompletionResult, AICompletion,
} from '../api/types';
import { EventBus } from '../core/EventBus';

export interface AIAssistantConfig {
  enabled: boolean;
  model: string;
  maxTokens: number;
  temperature: number;
}

export interface ModelAdapter {
  complete(context: AICompletionContext): Promise<AICompletion[]>;
  explain(document: TextDocument, range: Range): Promise<string>;
  suggest(document: TextDocument): Promise<AISuggestion[]>;
  detectBugs(document: TextDocument): Promise<AISuggestion[]>;
  generateDocs(document: TextDocument, range: Range): Promise<string>;
}

export class LocalModelAdapter implements ModelAdapter {
  async complete(context: AICompletionContext): Promise<AICompletion[]> {
    const { prefix, language } = context;
    const lines = prefix.split('\n');
    const lastLine = lines[lines.length - 1]?.trim() ?? '';

    const completions: AICompletion[] = [];

    if (lastLine.endsWith('.')) {
      completions.push({
        text: 'map',
        confidence: 0.6,
        explanation: 'Common method access on object',
      });
    }

    if (lastLine.endsWith('(')) {
      completions.push({
        text: ')',
        confidence: 0.8,
        explanation: 'Closing parenthesis',
      });
    }

    if (lastLine.endsWith('{')) {
      const indent = '  ';
      completions.push({
        text: `\n${indent}\n}`,
        confidence: 0.7,
        explanation: 'Block completion',
      });
    }

    if (language === 'typescript' || language === 'javascript') {
      completions.push({
        text: ';\n',
        confidence: 0.5,
        explanation: 'Statement termination',
      });
    }

    return completions;
  }

  async explain(document: TextDocument, range: Range): Promise<string> {
    const text = document.getText(range);
    if (!text || text.trim().length === 0) return 'No code selected.';

    const lines = text.split('\n');
    const keywordPatterns = [
      { pattern: /\bif\b/, desc: 'conditional branching' },
      { pattern: /\bfor\b/, desc: 'loop iteration' },
      { pattern: /\bwhile\b/, desc: 'loop iteration' },
      { pattern: /\bfn\b/, desc: 'function declaration' },
      { pattern: /\bclass\b/, desc: 'class declaration' },
      { pattern: /\breturn\b/, desc: 'return statement' },
      { pattern: /\bmatch\b/, desc: 'pattern matching' },
      { pattern: /\bimport\b/, desc: 'module import' },
    ];

    const found = keywordPatterns.filter((k) => k.pattern.test(text));
    const structure = found.length > 0
      ? found.map((f) => f.desc).join(', ')
      : 'code block';

    const complexity = lines.length > 20 ? 'complex' : lines.length > 5 ? 'moderate' : 'simple';

    return `This ${complexity} ${structure} contains ${lines.length} line(s). ${
      text.includes('//') ? 'It includes inline comments. ' : ''
    }The block primarily involves ${structure}.`;
  }

  async suggest(document: TextDocument): Promise<AISuggestion[]> {
    const text = document.getText();
    const suggestions: AISuggestion[] = [];
    const lines = text.split('\n');

    if (lines.length > 200) {
      suggestions.push({
        id: 'perf-large-file',
        type: 'performance',
        title: 'Large file detected',
        description: 'This file has over 200 lines. Consider splitting it into smaller modules.',
        severity: 'medium',
        explanation: 'Large files are harder to maintain and navigate.',
      });
    }

    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim().startsWith('console.log')) {
        suggestions.push({
          id: `debug-log-${i}`,
          type: 'improvement',
          title: 'Debug logging',
          description: 'Remove console.log on line ' + (i + 1) + ' in production code.',
          severity: 'low',
          range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
          explanation: 'Console logs should be removed or replaced with a proper logging framework.',
        });
        break;
      }
    }

    const varPattern = /\b(var|let)\s+\w+/g;
    let match: RegExpExecArray | null;
    while ((match = varPattern.exec(text)) !== null) {
      const lineIdx = text.substring(0, match.index).split('\n').length - 1;
      suggestions.push({
        id: `const-suggest-${lineIdx}-${match.index}`,
        type: 'style',
        title: 'Prefer const',
        description: `'${match[1]}' on line ${lineIdx + 1} can likely be 'const' if not reassigned.`,
        severity: 'low',
        range: {
          start: { line: lineIdx, column: 0 },
          end: { line: lineIdx, column: lines[lineIdx].length },
        },
        explanation: 'Using const communicates intent and prevents accidental reassignment.',
      });
      break;
    }

    return suggestions;
  }

  async detectBugs(document: TextDocument): Promise<AISuggestion[]> {
    const text = document.getText();
    const bugs: AISuggestion[] = [];
    const lines = text.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();

      if (trimmed.includes('== ') && !trimmed.includes('===')) {
        bugs.push({
          id: `bug-eq-${i}`,
          type: 'bug',
          title: 'Loose equality comparison',
          description: `Line ${i + 1} uses '==' instead of '==='.`,
          severity: 'medium',
          range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
          explanation: 'Loose equality can cause unexpected type coercion bugs.',
        });
      }

      if (/for\s*\(\s*(let|var)\s+\w+\s*=\s*0\s*;\s*\w+\s*<=\s*\w+\.\w+\s*/.test(trimmed)) {
        bugs.push({
          id: `bug-off-by-one-${i}`,
          type: 'bug',
          title: 'Potential off-by-one error',
          description: `Line ${i + 1} uses <= in loop condition which may cause off-by-one.`,
          severity: 'low',
          range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
          explanation: 'Using <= in loop conditions can iterate one extra time past array bounds.',
        });
      }

      if (trimmed === '') continue;
      if (
        trimmed.includes('null') &&
        !trimmed.includes('== null') &&
        !trimmed.includes('=== null') &&
        !trimmed.includes('!= null') &&
        !trimmed.includes('!== null')
      ) {
        const nextLine = lines[i + 1]?.trim();
        if (nextLine && !nextLine.startsWith('if') && !nextLine.startsWith('//')) {
          bugs.push({
            id: `bug-null-ref-${i}`,
            type: 'bug',
            title: 'Possible null reference',
            description: `Line ${i + 1} references null without null check on the following line.`,
            severity: 'high',
            range: { start: { line: i, column: 0 }, end: { line: i, column: lines[i].length } },
            explanation: 'Accessing properties on null values will throw at runtime.',
          });
        }
      }
    }

    return bugs;
  }

  async generateDocs(document: TextDocument, range: Range): Promise<string> {
    const text = document.getText(range);
    if (!text || text.trim().length === 0) return '';

    const lines = text.split('\n');
    const firstLine = lines[0].trim();
    let comment = '/**\n';

    if (firstLine.startsWith('fn ') || firstLine.startsWith('function ')) {
      const nameMatch = firstLine.match(/(?:fn|function)\s+(\w+)/);
      const name = nameMatch ? nameMatch[1] : 'function';
      const params = firstLine.match(/(\w+)\s*:/g);
      comment += ` * ${name} - description\n *\n`;
      if (params) {
        for (const p of params) {
          const paramName = p.replace(':', '').trim();
          comment += ` * @param ${paramName} - description\n`;
        }
      }
      comment += ` * @returns description\n`;
    } else if (firstLine.startsWith('class ')) {
      const nameMatch = firstLine.match(/class\s+(\w+)/);
      const name = nameMatch ? nameMatch[1] : 'class';
      comment += ` * ${name} - description\n`;
    } else {
      comment += ` * ${firstLine.length > 50 ? firstLine.substring(0, 50) + '...' : firstLine}\n`;
    }

    comment += ' */';
    return comment;
  }
}

export class AIAssistant {
  private eventBus: EventBus;
  private modelAdapter: ModelAdapter;
  private config: AIAssistantConfig;

  constructor(eventBus: EventBus, config?: Partial<AIAssistantConfig>) {
    this.eventBus = eventBus;
    this.config = {
      enabled: config?.enabled ?? true,
      model: config?.model ?? 'local',
      maxTokens: config?.maxTokens ?? 1024,
      temperature: config?.temperature ?? 0.7,
    };
    this.modelAdapter = new LocalModelAdapter();
  }

  setModelAdapter(adapter: ModelAdapter): void {
    this.modelAdapter = adapter;
  }

  async generateCompletion(context: AICompletionContext): Promise<AICompletionResult> {
    const requestId = `ai-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    const completions = await this.modelAdapter.complete(context);
    const result: AICompletionResult = { completions, requestId };
    this.eventBus.emit('ai:completion', result);
    return result;
  }

  async getSuggestions(document: TextDocument): Promise<AISuggestion[]> {
    const suggestions = await this.modelAdapter.suggest(document);
    this.eventBus.emit('ai:suggestion', { uri: document.uri, suggestions });
    return suggestions;
  }

  async explainCode(document: TextDocument, range: Range): Promise<string> {
    const explanation = await this.modelAdapter.explain(document, range);
    this.eventBus.emit('ai:explanation', { uri: document.uri, range, explanation });
    return explanation;
  }

  async detectBugs(document: TextDocument): Promise<AISuggestion[]> {
    const bugs = await this.modelAdapter.detectBugs(document);
    this.eventBus.emit('ai:bug', { uri: document.uri, bugs });
    return bugs;
  }

  async generateDocumentation(document: TextDocument, range: Range): Promise<string> {
    const docs = await this.modelAdapter.generateDocs(document, range);
    this.eventBus.emit('ai:doc', { uri: document.uri, range, docs });
    return docs;
  }
}
