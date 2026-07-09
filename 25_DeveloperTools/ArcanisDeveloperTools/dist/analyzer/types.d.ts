export interface AnalysisResult {
    file: string;
    issues: AnalysisIssue[];
    complexity: ComplexityMetrics;
    dependencies: string[];
}
export interface AnalysisIssue {
    severity: 'error' | 'warning' | 'info';
    rule: string;
    message: string;
    line: number;
    column: number;
    suggestion?: string;
}
export interface ComplexityMetrics {
    cyclomaticComplexity: number;
    cognitiveComplexity: number;
    linesOfCode: number;
    numberOfFunctions: number;
    numberOfClasses: number;
    maxDepth: number;
}
export interface LintRule {
    name: string;
    severity: 'error' | 'warning' | 'info';
    check: (source: string) => AnalysisIssue[];
}
export interface DependencyGraph {
    nodes: DependencyNode[];
    edges: DependencyEdge[];
}
export interface DependencyNode {
    name: string;
    type: 'module' | 'file' | 'package';
    path: string;
}
export interface DependencyEdge {
    from: string;
    to: string;
    type: 'import' | 'require' | 'dynamic';
}
