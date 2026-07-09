export { Compiler, CompileOptions, CompileResult } from './compiler';
export { Lexer } from './lexer/lexer';
export { Token } from './lexer/token';
export { Parser } from './parser/parser';
export { Program, FunctionDecl, ParamDecl, VarDecl, BlockStmt, ExprStmt, IfStmt, WhileStmt, ReturnStmt, BinaryExpr, UnaryExpr, CallExpr, Identifier, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral, UnitLiteral, GroupExpr, } from './parser/ast';
export { TypeChecker } from './checker/checker';
export { Optimizer } from './optimizer/optimizer';
export { JavaScriptCodeGen, CodeGenTarget } from './codegen/codegen';
export { Target, listTargets, getTarget } from './targets/target';
export { ErrorReporter, CompilerError } from './error';
export { PluginManager, CompilerPlugin, PluginHooks } from './plugin';
export { IncrementalCompiler } from './incremental';
export { DebugInfoBuilder, DebugInfo, formatDebugInfo } from './debug';
export { Type, TypeKind, TokenKind, Keyword, BinaryOp, UnaryOp, SourceLocation, SourceRange, CompilerStage, Severity, CompilerDiagnostic, } from './types';
//# sourceMappingURL=index.d.ts.map