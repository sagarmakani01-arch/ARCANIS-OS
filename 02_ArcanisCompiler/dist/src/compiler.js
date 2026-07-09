"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Compiler = void 0;
const lexer_1 = require("./lexer/lexer");
const parser_1 = require("./parser/parser");
const checker_1 = require("./checker/checker");
const optimizer_1 = require("./optimizer/optimizer");
const codegen_1 = require("./codegen/codegen");
const target_1 = require("./targets/target");
const error_1 = require("./error");
const plugin_1 = require("./plugin");
const incremental_1 = require("./incremental");
const debug_1 = require("./debug");
const types_1 = require("./types");
class Compiler {
    constructor() {
        this.source = '';
        this.sourceId = '<stdin>';
        this.tokens = [];
        this.ast = null;
        this.errors = new error_1.ErrorReporter();
        this.pluginManager = new plugin_1.PluginManager();
        this.incrementalCompiler = new incremental_1.IncrementalCompiler();
        this.debugInfoBuilder = new debug_1.DebugInfoBuilder();
    }
    setSource(source, sourceId) {
        this.source = source;
        this.sourceId = sourceId || '<stdin>';
        this.errors.setSource(this.sourceId, source);
    }
    getPluginManager() {
        return this.pluginManager;
    }
    getErrorReporter() {
        return this.errors;
    }
    getIncrementalCompiler() {
        return this.incrementalCompiler;
    }
    getDebugInfoBuilder() {
        return this.debugInfoBuilder;
    }
    compile(options = {}) {
        const target = options.sourceId || this.sourceId;
        const sourceId = options.sourceId || this.sourceId;
        const targetName = options.target || 'js';
        const enableOptimizations = options.enableOptimizations ?? true;
        const enableDebugInfo = options.enableDebugInfo ?? false;
        const enableIncremental = options.enableIncremental ?? false;
        const emitOnly = options.emitOnly;
        const stagesCompleted = [];
        const timing = new Map();
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
                    stagesCompleted: [types_1.CompilerStage.CodeGeneration],
                    timing,
                };
            }
        }
        try {
            // --- STAGE 1: Lexical Analysis ---
            if (!emitOnly || emitOnly.includes(types_1.CompilerStage.Lexing)) {
                const startTime = Date.now();
                this.pluginManager.runStageHooks(types_1.CompilerStage.Lexing, this);
                let modifiedSource = this.pluginManager.runHook('beforeLexing', this.source) ?? this.source;
                const lexer = new lexer_1.Lexer(modifiedSource, sourceId, this.errors);
                this.tokens = lexer.tokenize();
                this.tokens = this.pluginManager.runHook('afterLexing', this.tokens) ?? this.tokens;
                timing.set(types_1.CompilerStage.Lexing, Date.now() - startTime);
                stagesCompleted.push(types_1.CompilerStage.Lexing);
                if (this.errors.hasErrors() && !emitOnly) {
                    return this.result(undefined, stagesCompleted, timing);
                }
            }
            // --- STAGE 2 & 3: Parsing & AST Generation ---
            if (!emitOnly || emitOnly.includes(types_1.CompilerStage.Parsing) || emitOnly.includes(types_1.CompilerStage.AstGeneration)) {
                const startTime = Date.now();
                this.pluginManager.runStageHooks(types_1.CompilerStage.Parsing, this);
                let modifiedTokens = this.pluginManager.runHook('beforeParsing', this.tokens) ?? this.tokens;
                const parser = new parser_1.Parser(modifiedTokens, sourceId, this.errors);
                let program = parser.parse();
                program = this.pluginManager.runHook('afterParsing', program) ?? program;
                this.ast = program;
                timing.set(types_1.CompilerStage.Parsing, Date.now() - startTime);
                stagesCompleted.push(types_1.CompilerStage.Parsing);
                stagesCompleted.push(types_1.CompilerStage.AstGeneration);
                if (this.errors.hasErrors() && !emitOnly) {
                    return this.result(undefined, stagesCompleted, timing);
                }
            }
            // --- STAGE 4: Type Checking ---
            if (!emitOnly || emitOnly.includes(types_1.CompilerStage.TypeChecking)) {
                const startTime = Date.now();
                this.pluginManager.runStageHooks(types_1.CompilerStage.TypeChecking, this);
                let checkedAst = this.pluginManager.runHook('beforeTypeChecking', this.ast) ?? this.ast;
                const checker = new checker_1.TypeChecker(sourceId, this.errors);
                checker.check(checkedAst);
                checkedAst = this.pluginManager.runHook('afterTypeChecking', checkedAst) ?? checkedAst;
                this.ast = checkedAst;
                timing.set(types_1.CompilerStage.TypeChecking, Date.now() - startTime);
                stagesCompleted.push(types_1.CompilerStage.TypeChecking);
                if (this.errors.hasErrors() && !emitOnly) {
                    return this.result(undefined, stagesCompleted, timing);
                }
            }
            // --- STAGE 5: Optimization ---
            if (enableOptimizations && (!emitOnly || emitOnly.includes(types_1.CompilerStage.Optimization))) {
                const startTime = Date.now();
                this.pluginManager.runStageHooks(types_1.CompilerStage.Optimization, this);
                let optimizedAst = this.pluginManager.runHook('beforeOptimization', this.ast) ?? this.ast;
                const optimizer = new optimizer_1.Optimizer();
                optimizedAst = optimizer.optimize(optimizedAst);
                optimizedAst = this.pluginManager.runHook('afterOptimization', optimizedAst) ?? optimizedAst;
                this.ast = optimizedAst;
                timing.set(types_1.CompilerStage.Optimization, Date.now() - startTime);
                stagesCompleted.push(types_1.CompilerStage.Optimization);
            }
            // --- STAGE 6: Code Generation ---
            if (!emitOnly || emitOnly.includes(types_1.CompilerStage.CodeGeneration)) {
                const startTime = Date.now();
                this.pluginManager.runStageHooks(types_1.CompilerStage.CodeGeneration, this);
                let output;
                if (targetName === 'js' || !targetName) {
                    const codegen = new codegen_1.JavaScriptCodeGen(sourceId);
                    const debugInfo = enableDebugInfo ? this.debugInfoBuilder : undefined;
                    output = this.pluginManager.runHook('beforeCodeGeneration', this.ast) ?? codegen.generate(this.ast, debugInfo);
                }
                else {
                    const target = (0, target_1.getTarget)(targetName);
                    if (!target) {
                        this.errors.error(types_1.CompilerStage.CodeGeneration, `Unknown target '${targetName}'`);
                        return this.result(undefined, stagesCompleted, timing);
                    }
                    const debugInfo = enableDebugInfo ? this.debugInfoBuilder : undefined;
                    output = target.generate(this.ast, debugInfo);
                }
                output = this.pluginManager.runHook('afterCodeGeneration', output) ?? output;
                timing.set(types_1.CompilerStage.CodeGeneration, Date.now() - startTime);
                stagesCompleted.push(types_1.CompilerStage.CodeGeneration);
                if (enableIncremental) {
                    this.incrementalCompiler.updateCache(sourceId, this.source, [], 'codegen');
                }
                return this.result(output, stagesCompleted, timing);
            }
            return this.result(undefined, stagesCompleted, timing);
        }
        catch (error) {
            const transformed = this.pluginManager.runHook('transformError', error) ?? error;
            this.errors.error(types_1.CompilerStage.CodeGeneration, transformed.message || 'Unknown error during compilation');
            return this.result(undefined, stagesCompleted, timing);
        }
    }
    result(output, stages, timing) {
        let debugInfo;
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
    clear() {
        this.errors.clear();
        this.source = '';
        this.sourceId = '<stdin>';
        this.tokens = [];
        this.ast = null;
        this.debugInfoBuilder.clear();
    }
}
exports.Compiler = Compiler;
//# sourceMappingURL=compiler.js.map