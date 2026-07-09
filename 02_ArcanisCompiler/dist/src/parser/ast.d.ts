import { SourceRange, Type, BinaryOp, UnaryOp } from '../types';
export type NodeKind = 'Program' | 'FunctionDecl' | 'ParamDecl' | 'VarDecl' | 'BlockStmt' | 'ExprStmt' | 'IfStmt' | 'WhileStmt' | 'ReturnStmt' | 'BinaryExpr' | 'UnaryExpr' | 'CallExpr' | 'Identifier' | 'IntLiteral' | 'FloatLiteral' | 'StringLiteral' | 'BoolLiteral' | 'UnitLiteral' | 'GroupExpr';
export declare class Node {
    readonly kind: NodeKind;
    readonly range: SourceRange;
    constructor(kind: NodeKind, range: SourceRange);
}
export declare class Program extends Node {
    readonly functions: FunctionDecl[];
    readonly statements: Stmt[];
    constructor(range: SourceRange, functions: FunctionDecl[], statements: Stmt[]);
}
export declare class FunctionDecl extends Node {
    readonly name: string;
    readonly params: ParamDecl[];
    readonly returnType: Type;
    readonly body: BlockStmt;
    resolvedType?: Type | undefined;
    constructor(range: SourceRange, name: string, params: ParamDecl[], returnType: Type, body: BlockStmt, resolvedType?: Type | undefined);
}
export declare class ParamDecl extends Node {
    readonly name: string;
    readonly paramType: Type;
    constructor(range: SourceRange, name: string, paramType: Type);
}
export declare class VarDecl extends Node {
    readonly name: string;
    readonly varType: Type;
    readonly initializer: Expr | undefined;
    constructor(range: SourceRange, name: string, varType: Type, initializer: Expr | undefined);
}
export declare class BlockStmt extends Node {
    readonly statements: Stmt[];
    constructor(range: SourceRange, statements: Stmt[]);
}
export declare class ExprStmt extends Node {
    readonly expression: Expr;
    constructor(range: SourceRange, expression: Expr);
}
export declare class IfStmt extends Node {
    readonly condition: Expr;
    readonly thenBranch: Stmt;
    readonly elseBranch: Stmt | undefined;
    constructor(range: SourceRange, condition: Expr, thenBranch: Stmt, elseBranch: Stmt | undefined);
}
export declare class WhileStmt extends Node {
    readonly condition: Expr;
    readonly body: Stmt;
    constructor(range: SourceRange, condition: Expr, body: Stmt);
}
export declare class ReturnStmt extends Node {
    readonly value: Expr | undefined;
    constructor(range: SourceRange, value: Expr | undefined);
}
export type Stmt = VarDecl | BlockStmt | ExprStmt | IfStmt | WhileStmt | ReturnStmt;
export declare class BinaryExpr extends Node {
    readonly left: Expr;
    readonly op: BinaryOp;
    readonly right: Expr;
    resolvedType?: Type | undefined;
    constructor(range: SourceRange, left: Expr, op: BinaryOp, right: Expr, resolvedType?: Type | undefined);
}
export declare class UnaryExpr extends Node {
    readonly op: UnaryOp;
    readonly operand: Expr;
    resolvedType?: Type | undefined;
    constructor(range: SourceRange, op: UnaryOp, operand: Expr, resolvedType?: Type | undefined);
}
export declare class CallExpr extends Node {
    readonly callee: Expr;
    readonly args: Expr[];
    resolvedType?: Type | undefined;
    constructor(range: SourceRange, callee: Expr, args: Expr[], resolvedType?: Type | undefined);
}
export declare class Identifier extends Node {
    readonly name: string;
    resolvedType?: Type | undefined;
    constructor(range: SourceRange, name: string, resolvedType?: Type | undefined);
}
export declare class IntLiteral extends Node {
    readonly value: number;
    constructor(range: SourceRange, value: number);
}
export declare class FloatLiteral extends Node {
    readonly value: number;
    constructor(range: SourceRange, value: number);
}
export declare class StringLiteral extends Node {
    readonly value: string;
    constructor(range: SourceRange, value: string);
}
export declare class BoolLiteral extends Node {
    readonly value: boolean;
    constructor(range: SourceRange, value: boolean);
}
export declare class UnitLiteral extends Node {
    constructor(range: SourceRange);
}
export declare class GroupExpr extends Node {
    readonly expression: Expr;
    constructor(range: SourceRange, expression: Expr);
}
export type Expr = BinaryExpr | UnaryExpr | CallExpr | Identifier | IntLiteral | FloatLiteral | StringLiteral | BoolLiteral | UnitLiteral | GroupExpr;
//# sourceMappingURL=ast.d.ts.map