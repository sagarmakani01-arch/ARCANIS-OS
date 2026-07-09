import { defaultRules } from './lint.js';
import { analyzeComplexity } from './complexity.js';
import { AnalysisResult, AnalysisIssue, ComplexityMetrics, LintRule } from './types.js';

export { defaultRules, analyzeComplexity };
export type { AnalysisResult, AnalysisIssue, ComplexityMetrics, LintRule } from './types.js';

export class CodeAnalyzer {
  private rules: LintRule[];

  constructor(rules?: LintRule[]) {
    this.rules = rules ?? defaultRules;
  }

  async analyzeFile(filePath: string, source: string): Promise<AnalysisResult> {
    const issues: AnalysisIssue[] = [];

    for (const rule of this.rules) {
      try {
        const ruleIssues = rule.check(source);
        issues.push(...ruleIssues);
      } catch (err) {
        console.error(`[Analyzer] Rule '${rule.name}' failed:`, err);
      }
    }

    const complexity = analyzeComplexity(source);
    const dependencies = this.extractDependencies(source);

    return { file: filePath, issues, complexity, dependencies };
  }

  private extractDependencies(source: string): string[] {
    const deps: string[] = [];
    const importRegex = /(?:import\s+(?:\w+\s*,?\s*)?(?:\{[^}]*\})?\s*from\s+['"]|require\s*\(\s*['"])([^'"]+)/g;
    let m: RegExpExecArray | null;
    while ((m = importRegex.exec(source)) !== null) {
      deps.push(m[1]);
    }
    return deps;
  }
}
