import { Lexer } from './lexer/lexer';
import { Token } from './lexer/token';
import { Parser } from './parser/parser';
import { Program } from './parser/ast';
import { TypeChecker } from './checker/checker';
import { Optimizer } from './optimizer/optimizer';
import { JavaScriptCodeGen } from './codegen/codegen';
import { Target, getTarget } from './targets/target';
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

export class Compiler {
  private errors: ErrorReporter;
  private pluginManager: PluginManager;
  private incrementalCompiler: IncrementalCompiler;
  private debugInfoBuilder: DebugInfoBuilder;
  private source: string = '';
  private sourceId: string = '<stdin>';
  private tokens: Token[] = [];
  private ast: Program | null = null;

  constructor() {
    this.errors = new ErrorReporter();
    this.pluginManager = new PluginManager();
    this.incrementalCompiler = new IncrementalCompiler();
    this.debugInfoBuilder = new DebugInfoBuilder();
  }

  setSource(source: string, sourceId?: string): void {
    this.source = source;
    this.sourceId = sourceId || '<stdin>';
    this.errors.setSource(this.sourceId, source);
  }

  getPluginManager(): PluginManager {
    return this.pluginManager;
  }

  getErrorReporter(): ErrorReporter {
    return this.errors;
  }

  getIncrementalCompiler(): IncrementalCompiler {
    return this.incrementalCompiler;
  }

  getDebugInfoBuilder(): DebugInfoBuilder {
    return this.debugInfoBuilder;
  }

  compile(options: CompileOptions = {}): CompileResult {
    const target = options.sourceId || this.sourceId;
    const sourceId = options.sourceId || this.sourceId;
    const targetName = options.target || 'js';
    const enableOptimizations = options.enableOptimizations ?? true;
    const enableDebugInfo = options.enableDebugInfo ?? false;
    const enableIncremental = options.enableIncremental ?? false;
    const emitOnly = options.emitOnly;

    const stagesCompleted: CompilerStage[] = [];
    const timing = new Map<CompilerStage, number>();

    if (!this.source) {
      return {
        success: false,
        diagnostics: [],
        stagesCompleted: [],
        timing,
      };
    }

    // Check incremental cache
    if (enableIncremental && this.incrementalCompiler.isCached(sourceId, this.source, 'codegen')) {
      const cachedOutput = this.incrementalCompiler.getCachedOutput(sourceId);
      if (cachedOutput) {
        return {
          success: true,
          output: cachedOutput,
          diagnostics: [],
          stagesCompleted: [CompilerStage.CodeGeneration],
          timing,
        };
      }
    }

    try {
      // --- STAGE 1: Lexical Analysis ---
      if (!emitOnly || emitOnly.includes(CompilerStage.Lexing)) {
        const startTime = Date.now();
        this.pluginManager.runStageHooks(CompilerStage.Lexing, this);

        let modifiedSource = this.pluginManager.runHook('beforeLexing', this.source) ?? this.source;
        const lexer = new Lexer(modifiedSource, sourceId, this.errors);
        this.tokens = lexer.tokenize();
        this.tokens = this.pluginManager.runHook('afterLexing', this.tokens) ?? this.tokens;

        timing.set(CompilerStage.Lexing, Date.now() - startTime);
        stagesCompleted.push(CompilerStage.Lexing);

        if (this.errors.hasErrors() && !emitOnly) {
          return this.result(undefined, stagesCompleted, timing);
        }
      }

      // --- STAGE 2 & 3: Parsing & AST Generation ---
      if (!emitOnly || emitOnly.includes(CompilerStage.Parsing) || emitOnly.includes(CompilerStage.AstGeneration)) {
        const startTime = Date.now();
        this.pluginManager.runStageHooks(CompilerStage.Parsing, this);

        let modifiedTokens = this.pluginManager.runHook('beforeParsing', this.tokens) ?? this.tokens;
        const parser = new Parser(modifiedTokens, sourceId, this.errors);
        let program = parser.parse();
        program = this.pluginManager.runHook('afterParsing', program) ?? program;
        this.ast = program;

        timing.set(CompilerStage.Parsing, Date.now() - startTime);
        stagesCompleted.push(CompilerStage.Parsing);
        stagesCompleted.push(CompilerStage.AstGeneration);

        if (this.errors.hasErrors() && !emitOnly) {
          return this.result(undefined, stagesCompleted, timing);
        }
      }

      // --- STAGE 4: Type Checking ---
      if (!emitOnly || emitOnly.includes(CompilerStage.TypeChecking)) {
        const startTime = Date.now();
        this.pluginManager.runStageHooks(CompilerStage.TypeChecking, this);

        let checkedAst = this.pluginManager.runHook('beforeTypeChecking', this.ast!) ?? this.ast!;
        const checker = new TypeChecker(sourceId, this.errors);
        checker.check(checkedAst);
        checkedAst = this.pluginManager.runHook('afterTypeChecking', checkedAst) ?? checkedAst;
        this.ast = checkedAst;

        timing.set(CompilerStage.TypeChecking, Date.now() - startTime);
        stagesCompleted.push(CompilerStage.TypeChecking);

        if (this.errors.hasErrors() && !emitOnly) {
          return this.result(undefined, stagesCompleted, timing);
        }
      }

      // --- STAGE 5: Optimization ---
      if (enableOptimizations && (!emitOnly || emitOnly.includes(CompilerStage.Optimization))) {
        const startTime = Date.now();
        this.pluginManager.runStageHooks(CompilerStage.Optimization, this);

        let optimizedAst = this.pluginManager.runHook('beforeOptimization', this.ast!) ?? this.ast!;
        const optimizer = new Optimizer();
        optimizedAst = optimizer.optimize(optimizedAst);
        optimizedAst = this.pluginManager.runHook('afterOptimization', optimizedAst) ?? optimizedAst;
        this.ast = optimizedAst;

        timing.set(CompilerStage.Optimization, Date.now() - startTime);
        stagesCompleted.push(CompilerStage.Optimization);
      }

      // --- STAGE 6: Code Generation ---
      if (!emitOnly || emitOnly.includes(CompilerStage.CodeGeneration)) {
        const startTime = Date.now();
        this.pluginManager.runStageHooks(CompilerStage.CodeGeneration, this);

        let output: string;

        if (targetName === 'js' || !targetName) {
          const codegen = new JavaScriptCodeGen(sourceId);
          const debugInfo = enableDebugInfo ? this.debugInfoBuilder : undefined;
          output = this.pluginManager.runHook('beforeCodeGeneration', this.ast!) ?? codegen.generate(this.ast!, debugInfo);
        } else {
          const target = getTarget(targetName);
          if (!target) {
            this.errors.error(
              CompilerStage.CodeGeneration,
              `Unknown target '${targetName}'`,
            );
            return this.result(undefined, stagesCompleted, timing);
          }
          const debugInfo = enableDebugInfo ? this.debugInfoBuilder : undefined;
          output = target.generate(this.ast!, debugInfo);
        }

        output = this.pluginManager.runHook('afterCodeGeneration', output) ?? output;
        timing.set(CompilerStage.CodeGeneration, Date.now() - startTime);
        stagesCompleted.push(CompilerStage.CodeGeneration);

        if (enableIncremental) {
          this.incrementalCompiler.updateCache(sourceId, this.source, [], 'codegen');
        }

        return this.result(output, stagesCompleted, timing);
      }

      return this.result(undefined, stagesCompleted, timing);
    } catch (error: any) {
      const transformed = this.pluginManager.runHook('transformError', error) ?? error;
      this.errors.error(
        CompilerStage.CodeGeneration,
        transformed.message || 'Unknown error during compilation',
      );
      return this.result(undefined, stagesCompleted, timing);
    }
  }

  private result(output?: string, stages?: CompilerStage[], timing?: Map<CompilerStage, number>): CompileResult {
    let debugInfo: DebugInfo | undefined;
    if (this.debugInfoBuilder) {
      debugInfo = this.debugInfoBuilder.build(this.sourceId);
    }

    return {
      success: !this.errors.hasErrors(),
      output,
      diagnostics: this.errors.getDiagnostics(),
      debugInfo,
      stagesCompleted: stages || [],
      timing: timing || new Map(),
    };
  }

  clear(): void {
    this.errors.clear();
    this.source = '';
    this.sourceId = '<stdin>';
    this.tokens = [];
    this.ast = null;
    this.debugInfoBuilder.clear();
  }
}
