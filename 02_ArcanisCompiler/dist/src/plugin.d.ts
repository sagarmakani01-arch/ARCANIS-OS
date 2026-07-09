import { CompilerStage } from './types';
import { Program } from './parser/ast';
import type { Compiler } from './compiler';
export interface CompilerPlugin {
    name: string;
    version: string;
    hooks: Partial<PluginHooks>;
}
export interface PluginHooks {
    beforeStage(stage: CompilerStage, compiler: Compiler): void;
    afterStage(stage: CompilerStage, compiler: Compiler): void;
    beforeLexing(source: string): string;
    afterLexing(tokens: Token[]): Token[];
    beforeParsing(tokens: Token[]): Token[];
    afterParsing(ast: Program): Program;
    beforeTypeChecking(ast: Program): Program;
    afterTypeChecking(ast: Program): Program;
    beforeOptimization(ast: Program): Program;
    afterOptimization(ast: Program): Program;
    beforeCodeGeneration(ast: Program): string;
    afterCodeGeneration(output: string): string;
    transformError(error: any): any;
}
import { Token } from './lexer/token';
export declare class PluginManager {
    private plugins;
    register(plugin: CompilerPlugin): void;
    unregister(name: string): void;
    getPlugins(): CompilerPlugin[];
    runHook<K extends keyof PluginHooks>(hookName: K, ...args: Parameters<Exclude<PluginHooks[K], undefined>>): ReturnType<Exclude<PluginHooks[K], undefined>> | undefined;
    runStageHooks(stage: CompilerStage, compiler: Compiler): void;
    clear(): void;
}
//# sourceMappingURL=plugin.d.ts.map