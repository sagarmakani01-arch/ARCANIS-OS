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

// Forward declaration to avoid circular import
import { Token } from './lexer/token';

export class PluginManager {
  private plugins: CompilerPlugin[] = [];

  register(plugin: CompilerPlugin): void {
    if (this.plugins.find((p) => p.name === plugin.name)) {
      throw new Error(`Plugin '${plugin.name}' is already registered`);
    }
    this.plugins.push(plugin);
  }

  unregister(name: string): void {
    this.plugins = this.plugins.filter((p) => p.name !== name);
  }

  getPlugins(): CompilerPlugin[] {
    return [...this.plugins];
  }

  runHook<K extends keyof PluginHooks>(
    hookName: K,
    ...args: Parameters<Exclude<PluginHooks[K], undefined>>
  ): ReturnType<Exclude<PluginHooks[K], undefined>> | undefined {
    let result: any = undefined;
    for (const plugin of this.plugins) {
      const hook = plugin.hooks[hookName];
      if (hook) {
        try {
          result = (hook as any)(...args);
          if (result !== undefined) {
            args = [result] as any;
          }
        } catch (e) {
          console.error(`Plugin '${plugin.name}' failed on hook '${hookName}':`, e);
        }
      }
    }
    return result;
  }

  runStageHooks(stage: CompilerStage, compiler: Compiler): void {
    for (const plugin of this.plugins) {
      plugin.hooks.beforeStage?.(stage, compiler);
    }
  }

  clear(): void {
    this.plugins = [];
  }
}
