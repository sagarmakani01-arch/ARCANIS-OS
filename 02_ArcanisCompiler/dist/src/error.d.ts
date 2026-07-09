import { SourceRange, CompilerDiagnostic, CompilerStage } from './types';
export declare class CompilerError extends Error {
    readonly stage: CompilerStage;
    readonly range?: SourceRange | undefined;
    readonly hints: string[];
    constructor(stage: CompilerStage, message: string, range?: SourceRange | undefined, hints?: string[]);
    toDiagnostic(): CompilerDiagnostic;
}
export declare class ErrorReporter {
    private diagnostics;
    private sourceCache;
    setSource(sourceId: string, content: string): void;
    report(diagnostic: CompilerDiagnostic): void;
    error(stage: CompilerStage, message: string, range?: SourceRange, hints?: string[]): void;
    warning(stage: CompilerStage, message: string, range?: SourceRange, hints?: string[]): void;
    info(stage: CompilerStage, message: string, range?: SourceRange): void;
    getDiagnostics(): CompilerDiagnostic[];
    hasErrors(): boolean;
    formatDiagnostic(diagnostic: CompilerDiagnostic): string;
    formatAll(): string;
    clear(): void;
}
export declare function createCompilerError(stage: CompilerStage, message: string, range?: SourceRange, hints?: string[]): CompilerError;
//# sourceMappingURL=error.d.ts.map