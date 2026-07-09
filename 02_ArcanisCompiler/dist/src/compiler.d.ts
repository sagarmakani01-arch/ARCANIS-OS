import { ErrorReporter } from './error';
import { PluginManager } from './plugin';
import { IncrementalCompiler } from './incremental';
import { DebugInfoBuilder, DebugInfo } from './debug';
import { CompilerStage, CompilerDiagnostic } from './types';
export interface CompileOptions {
    sourceId?: string;
    target?: string;
    enableOptimizations?: boolean;
    enableDebugInfo?: boolean;
    enableIncremental?: boolean;
    emitOnly?: CompilerStage[];
}
export interface CompileResult {
    success: boolean;
    output?: string;
    diagnostics: CompilerDiagnostic[];
    debugInfo?: DebugInfo;
    stagesCompleted: CompilerStage[];
    timing: Map<CompilerStage, number>;
}
export declare class Compiler {
    private errors;
    private pluginManager;
    private incrementalCompiler;
    private debugInfoBuilder;
    private source;
    private sourceId;
    private tokens;
    private ast;
    constructor();
    setSource(source: string, sourceId?: string): void;
    getPluginManager(): PluginManager;
    getErrorReporter(): ErrorReporter;
    getIncrementalCompiler(): IncrementalCompiler;
    getDebugInfoBuilder(): DebugInfoBuilder;
    compile(options?: CompileOptions): CompileResult;
    private result;
    clear(): void;
}
//# sourceMappingURL=compiler.d.ts.map