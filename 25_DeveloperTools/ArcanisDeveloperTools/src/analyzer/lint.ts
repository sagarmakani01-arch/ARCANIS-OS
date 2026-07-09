import { AnalysisIssue, LintRule } from './types.js';

export const defaultRules: LintRule[] = [
  {
    name: 'no-console-log',
    severity: 'warning',
    check: (source: string) => {
      const issues: AnalysisIssue[] = [];
      const regex = /console\.(log|debug|info|warn|error)\(/g;
      let match: RegExpExecArray | null;
      while ((match = regex.exec(source)) !== null) {
        issues.push({
          severity: 'warning',
          rule: 'no-console-log',
          message: `Unexpected console.${match[1]} statement`,
          line: source.slice(0, match.index).split('\n').length,
          column: match.index - source.lastIndexOf('\n', match.index) - 1,
          suggestion: 'Use a proper logging framework instead',
        });
      }
      return issues;
    },
  },
  {
    name: 'no-unused-vars',
    severity: 'warning',
    check: (source: string) => {
      const issues: AnalysisIssue[] = [];
      const declared = new Set<string>();
      const used = new Set<string>();
      const varRegex = /(?:let|const|var)\s+(\w+)/g;
      let m: RegExpExecArray | null;
      while ((m = varRegex.exec(source)) !== null) {
        declared.add(m[1]);
      }
      const useRegex = /\b(\w+)\b/g;
      while ((m = useRegex.exec(source)) !== null) {
        if (declared.has(m[1])) used.add(m[1]);
      }
      for (const v of declared) {
        if (!used.has(v)) {
          issues.push({
            severity: 'warning',
            rule: 'no-unused-vars',
            message: `Variable '${v}' is declared but never used`,
            line: 0,
            column: 0,
            suggestion: `Remove '${v}' or use it`,
          });
        }
      }
      return issues;
    },
  },
  {
    name: 'max-line-length',
    severity: 'warning',
    check: (source: string) => {
      const issues: AnalysisIssue[] = [];
      const lines = source.split('\n');
      lines.forEach((line, index) => {
        if (line.length > 120) {
          issues.push({
            severity: 'warning',
            rule: 'max-line-length',
            message: `Line exceeds 120 characters (${line.length})`,
            line: index + 1,
            column: 120,
            suggestion: 'Break the line into multiple lines',
          });
        }
      });
      return issues;
    },
  },
];
