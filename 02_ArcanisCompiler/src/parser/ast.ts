import { SourceRange, Type, BinaryOp, UnaryOp } from '../types';

export type NodeKind =
  | 'Program'
  | 'FunctionDecl'
  | 'ParamDecl'
  | 'VarDecl'
  | 'BlockStmt'
  | 'ExprStmt'
  | 'IfStmt'
  | 'WhileStmt'
  | 'ReturnStmt'
  | 'BinaryExpr'
  | 'UnaryExpr'
  | 'CallExpr'
  | 'Identifier'
  | 'IntLiteral'
  | 'FloatLiteral'
  | 'StringLiteral'
  | 'BoolLiteral'
  | 'UnitLiteral'
  | 'GroupExpr';

export class Node {
  constructor(
    public readonly kind: NodeKind,
    public readonly range: SourceRange,
  ) {}
}

export class Program extends Node {
  constructor(
    range: SourceRange,
    public readonly functions: FunctionDecl[],
    public readonly statements: Stmt[],
  ) {
    super('Program', range);
  }
}

export class FunctionDecl extends Node {
  constructor(
    range: SourceRange,
    public readonly name: string,
    public readonly params: ParamDecl[],
    public readonly returnType: Type,
    public readonly body: BlockStmt,
    public resolvedType?: Type,
  ) {
    super('FunctionDecl', range);
  }
}

export class ParamDecl extends Node {
  constructor(
    range: SourceRange,
    public readonly name: string,
    public readonly paramType: Type,
  ) {
    super('ParamDecl', range);
  }
}

export class VarDecl extends Node {
  constructor(
    range: SourceRange,
    public readonly name: string,
    public readonly varType: Type,
    public readonly initializer: Expr | undefined,
  ) {
    super('VarDecl', range);
  }
}

export class BlockStmt extends Node {
  constructor(
    range: SourceRange,
    public readonly statements: Stmt[],
  ) {
    super('BlockStmt', range);
  }
}

export class ExprStmt extends Node {
  constructor(
    range: SourceRange,
    public readonly expression: Expr,
  ) {
    super('ExprStmt', range);
  }
}

export class IfStmt extends Node {
  constructor(
    range: SourceRange,
    public readonly condition: Expr,
    public readonly thenBranch: Stmt,
    public readonly elseBranch: Stmt | undefined,
  ) {
    super('IfStmt', range);
  }
}

export class WhileStmt extends Node {
  constructor(
    range: SourceRange,
    public readonly condition: Expr,
    public readonly body: Stmt,
  ) {
    super('WhileStmt', range);
  }
}

export class ReturnStmt extends Node {
  constructor(
    range: SourceRange,
    public readonly value: Expr | undefined,
  ) {
    super('ReturnStmt', range);
  }
}

export type Stmt = VarDecl | BlockStmt | ExprStmt | IfStmt | WhileStmt | ReturnStmt;

export class BinaryExpr extends Node {
  constructor(
    range: SourceRange,
    public readonly left: Expr,
    public readonly op: BinaryOp,
    public readonly right: Expr,
    public resolvedType?: Type,
  ) {
    super('BinaryExpr', range);
  }
}

export class UnaryExpr extends Node {
  constructor(
    range: SourceRange,
    public readonly op: UnaryOp,
    public readonly operand: Expr,
    public resolvedType?: Type,
  ) {
    super('UnaryExpr', range);
  }
}

export class CallExpr extends Node {
  constructor(
    range: SourceRange,
    public readonly callee: Expr,
    public readonly args: Expr[],
    public resolvedType?: Type,
  ) {
    super('CallExpr', range);
  }
}

export class Identifier extends Node {
  constructor(
    range: SourceRange,
    public readonly name: string,
    public resolvedType?: Type,
  ) {
    super('Identifier', range);
  }
}

export class IntLiteral extends Node {
  constructor(
    range: SourceRange,
    public readonly value: number,
  ) {
    super('IntLiteral', range);
  }
}

export class FloatLiteral extends Node {
  constructor(
    range: SourceRange,
    public readonly value: number,
  ) {
    super('FloatLiteral', range);
  }
}

export class StringLiteral extends Node {
  constructor(
    range: SourceRange,
    public readonly value: string,
  ) {
    super('StringLiteral', range);
  }
}

export class BoolLiteral extends Node {
  constructor(
    range: SourceRange,
    public readonly value: boolean,
  ) {
    super('BoolLiteral', range);
  }
}

export class UnitLiteral extends Node {
  constructor(range: SourceRange) {
    super('UnitLiteral', range);
  }
}

export class GroupExpr extends Node {
  constructor(
    range: SourceRange,
    public readonly expression: Expr,
  ) {
    super('GroupExpr', range);
  }
}

export type Expr =
  | BinaryExpr
  | UnaryExpr
  | CallExpr
  | Identifier
  | IntLiteral
  | FloatLiteral
  | StringLiteral
  | BoolLiteral
  | UnitLiteral
  | GroupExpr;
