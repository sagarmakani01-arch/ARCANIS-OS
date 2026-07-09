import { TextDocument, Range, Position } from '../api/types';
import { AIAssistant } from './AIAssistant';

export interface CodeExplanation {
  summary: string;
  complexity: 'low' | 'medium' | 'high';
  lineByLine: Array<{ line: number; text: string; explanation: string }>;
  suggestions: string[];
}

export class CodeExplainer {
  private assistant: AIAssistant;

  constructor(assistant: AIAssistant) {
    this.assistant = assistant;
  }

  async explainCode(document: TextDocument, range: Range): Promise<CodeExplanation> {
    const text = document.getText(range);
    const lines = text.split('\n');
    const startLine = range.start.line;

    const aiExplanation = await this.assistant.explainCode(document, range);

    const complexity = this.estimateComplexity(text);
    const lineByLine = this.analyzeLines(lines, startLine);
    const suggestions = this.generateSuggestions(text, complexity);

    const summary = aiExplanation || this.generateFallbackSummary(text, complexity);

    return { summary, complexity, lineByLine, suggestions };
  }

  async explainSymbol(document: TextDocument, position: Position): Promise<string> {
    const line = document.lineAt(position.line);
    if (!line) return 'No symbol found.';

    const text = line.text;
    const symbolMatch = text.substring(0, position.column).match(/[\w_]+$/);
    const symbol = symbolMatch ? symbolMatch[0] : null;
    if (!symbol) return 'No symbol found at cursor position.';

    const explanation = this.heuristicSymbolExplain(symbol, text, document.languageId);
    return explanation;
  }

  private estimateComplexity(text: string): 'low' | 'medium' | 'high' {
    const lines = text.split('\n');
    if (lines.length > 50) return 'high';

    let cyclomaticScore = 0;
    const patterns = [/\bif\b/g, /\bfor\b/g, /\bwhile\b/g, /\bmatch\b/g, /\bcatch\b/g, /\bcase\b/g, /\belse\b/g, /\breturn\b/g];
    for (const pattern of patterns) {
      const matches = text.match(pattern);
      if (matches) cyclomaticScore += matches.length;
    }

    const nestingDepth = this.maxNestingDepth(text);

    if (cyclomaticScore > 15 || nestingDepth > 5 || lines.length > 30) return 'high';
    if (cyclomaticScore > 5 || nestingDepth > 3 || lines.length > 10) return 'medium';
    return 'low';
  }

  private maxNestingDepth(text: string): number {
    let depth = 0;
    let maxDepth = 0;
    for (const ch of text) {
      if (ch === '{') { depth++; if (depth > maxDepth) maxDepth = depth; }
      else if (ch === '}') { if (depth > 0) depth--; }
    }
    return maxDepth;
  }

  private analyzeLines(
    lines: string[],
    startLine: number,
  ): Array<{ line: number; text: string; explanation: string }> {
    const result: Array<{ line: number; text: string; explanation: string }> = [];

    for (let i = 0; i < lines.length; i++) {
      const text = lines[i];
      const trimmed = text.trim();
      let explanation = '';

      if (trimmed.startsWith('//') || trimmed.startsWith('#')) {
        explanation = 'Comment';
      } else if (trimmed.startsWith('import ') || trimmed.startsWith('use ') || trimmed.startsWith('from ')) {
        explanation = 'Import statement';
      } else if (trimmed.startsWith('fn ') || trimmed.startsWith('function ')) {
        explanation = 'Function declaration';
      } else if (trimmed.startsWith('class ')) {
        explanation = 'Class declaration';
      } else if (trimmed.startsWith('if ')) {
        explanation = 'Conditional branch';
      } else if (trimmed.startsWith('for ')) {
        explanation = 'For loop';
      } else if (trimmed.startsWith('while ')) {
        explanation = 'While loop';
      } else if (trimmed.startsWith('return ')) {
        explanation = 'Return statement';
      } else if (trimmed.startsWith('match ')) {
        explanation = 'Pattern matching expression';
      } else if (trimmed.startsWith('{') || trimmed.startsWith('}')) {
        explanation = 'Block delimiter';
      } else if (trimmed.startsWith('let ') || trimmed.startsWith('const ') || trimmed.startsWith('var ')) {
        explanation = 'Variable declaration';
      } else if (trimmed.length === 0) {
        explanation = '';
      } else if (trimmed.includes('=') && !trimmed.includes('==') && !trimmed.includes('!=')) {
        explanation = 'Assignment';
      } else if (trimmed.includes('(') && trimmed.includes(')')) {
        explanation = 'Function or method call';
      } else {
        explanation = 'Statement';
      }

      result.push({ line: startLine + i, text, explanation });
    }

    return result;
  }

  private generateSuggestions(text: string, complexity: 'low' | 'medium' | 'high'): string[] {
    const suggestions: string[] = [];
    const lines = text.split('\n');

    if (complexity === 'high') {
      suggestions.push('Consider breaking this code into smaller functions for better readability.');
      suggestions.push('Add type annotations to improve clarity and catch errors early.');
    }

    if (text.includes('  ') && !text.includes('\t')) {
      suggestions.push('Consider using consistent indentation throughout the code.');
    }

    const totalComments = lines.filter((l) => l.trim().startsWith('//') || l.trim().startsWith('#')).length;
    if (totalComments === 0 && lines.length > 10) {
      suggestions.push('Adding comments for complex logic would improve maintainability.');
    }

    return suggestions;
  }

  private generateFallbackSummary(text: string, complexity: 'low' | 'medium' | 'high'): string {
    const lines = text.split('\n');
    const firstMeaningfulLine = lines.find((l) => l.trim().length > 0 && !l.trim().startsWith('//'));
    const lineCount = lines.length;

    let summary = `This code block contains ${lineCount} line(s) with ${complexity} complexity.`;

    if (firstMeaningfulLine) {
      const trimmed = firstMeaningfulLine.trim();
      if (trimmed.startsWith('fn ') || trimmed.startsWith('function ')) {
        const name = trimmed.match(/(?:fn|function)\s+(\w+)/)?.[1] ?? 'anonymous';
        summary = `Function '${name}' with ${lineCount} line(s) and ${complexity} complexity.`;
      } else if (trimmed.startsWith('class ')) {
        const name = trimmed.match(/class\s+(\w+)/)?.[1] ?? 'anonymous';
        summary = `Class '${name}' with ${lineCount} line(s) and ${complexity} complexity.`;
      }
    }

    return summary;
  }

  private heuristicSymbolExplain(symbol: string, lineText: string, languageId: string): string {
    const isFunction = lineText.includes('fn ') || lineText.includes('function ');
    const isClass = lineText.includes('class ');
    const isVariable = lineText.includes('let ') || lineText.includes('const ') || lineText.includes('var ');
    const isImport = lineText.trim().startsWith('import ') || lineText.trim().startsWith('use ');
    const isCall = !isFunction && lineText.includes('(') && lineText.includes(')');

    if (isFunction) return `Symbol '${symbol}' is a function declaration.`;
    if (isClass) return `Symbol '${symbol}' is a class declaration.`;
    if (isVariable) return `Symbol '${symbol}' is a variable.`;
    if (isImport) return `Symbol '${symbol}' is imported from a module.`;
    if (isCall) return `Symbol '${symbol}' is a function/method call.`;

    if (lineText.includes(':')) {
      return `Symbol '${symbol}' is a property or key.`;
    }

    return `Symbol '${symbol}' is a named reference in this ${languageId} code.`;
  }
}
