import { defaultRules } from './lint.js';
import { analyzeComplexity } from './complexity.js';
import { AnalysisResult, LintRule } from './types.js';
export { defaultRules, analyzeComplexity };
export type { AnalysisResult, AnalysisIssue, ComplexityMetrics, LintRule } from './types.js';
export declare class CodeAnalyzer {
    private rules;
    constructor(rules?: LintRule[]);
    analyzeFile(filePath: string, source: string): Promise<AnalysisResult>;
    private extractDependencies;
}
