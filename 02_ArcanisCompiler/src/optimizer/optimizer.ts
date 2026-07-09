import {
  Program, FunctionDecl, ParamDecl, VarDecl, BlockStmt, ExprStmt,
  IfStmt, WhileStmt, ReturnStmt, BinaryExpr, UnaryExpr, CallExpr,
  Identifier, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
  UnitLiteral, GroupExpr, Stmt, Expr,
} from '../parser/ast';
import { Type, BinaryOp, UnaryOp } from '../types';

export class Optimizer {
  private changes = 0;

  optimize(program: Program): Program {
    this.changes = 0;

    const optimizedFunctions = program.functions.map((fn) => this.optimizeFunction(fn));
    const optimizedStmts = program.statements.map((stmt) => this.optimizeStmt(stmt));

    return new Program(program.range, optimizedFunctions, optimizedStmts);
  }

  getChangeCount(): number {
    return this.changes;
  }

  private optimizeFunction(fn: FunctionDecl): FunctionDecl {
    const body = this.optimizeBlock(fn.body);
    return new FunctionDecl(fn.range, fn.name, fn.params, fn.returnType, body, fn.resolvedType);
  }

  private optimizeStmt(stmt: Stmt): Stmt {
    if (stmt instanceof VarDecl) {
      return this.optimizeVarDecl(stmt);
    }
    if (stmt instanceof BlockStmt) {
      const block = this.optimizeBlock(stmt);
      // Flatten single-statement blocks if beneficial
      return block;
    }
    if (stmt instanceof ExprStmt) {
      const expr = this.optimizeExpr(stmt.expression);
      return new ExprStmt(stmt.range, expr);
    }
    if (stmt instanceof IfStmt) {
      return this.optimizeIfStmt(stmt);
    }
    if (stmt instanceof WhileStmt) {
      return this.optimizeWhileStmt(stmt);
    }
    if (stmt instanceof ReturnStmt) {
      const value = stmt.value ? this.optimizeExpr(stmt.value) : undefined;
      return new ReturnStmt(stmt.range, value);
    }
    return stmt;
  }

  private optimizeVarDecl(stmt: VarDecl): VarDecl {
    const init = stmt.initializer ? this.optimizeExpr(stmt.initializer) : undefined;
    return new VarDecl(stmt.range, stmt.name, stmt.varType, init);
  }

  private optimizeBlock(block: BlockStmt): BlockStmt {
    const stmts = block.statements.map((s) => this.optimizeStmt(s));
    return new BlockStmt(block.range, stmts);
  }

  private optimizeIfStmt(stmt: IfStmt): Stmt {
    const cond = this.optimizeExpr(stmt.condition);
    const thenBranch = this.optimizeStmt(stmt.thenBranch);

    // Constant folding: if condition is a boolean literal
    if (cond instanceof BoolLiteral) {
      this.changes++;
      if (cond.value) {
        return thenBranch;
      } else if (stmt.elseBranch) {
        return this.optimizeStmt(stmt.elseBranch);
      } else {
        // Empty statement - return a minimal block
        return new BlockStmt(stmt.range, []);
      }
    }

    const elseBranch = stmt.elseBranch ? this.optimizeStmt(stmt.elseBranch) : undefined;
    return new IfStmt(stmt.range, cond, thenBranch, elseBranch);
  }

  private optimizeWhileStmt(stmt: WhileStmt): Stmt {
    const cond = this.optimizeExpr(stmt.condition);

    // Remove while(false) loops
    if (cond instanceof BoolLiteral && !cond.value) {
      this.changes++;
      return new BlockStmt(stmt.range, []);
    }

    const body = this.optimizeStmt(stmt.body);
    return new WhileStmt(stmt.range, cond, body);
  }

  private optimizeExpr(expr: Expr): Expr {
    if (expr instanceof BinaryExpr) {
      return this.optimizeBinary(expr);
    }
    if (expr instanceof UnaryExpr) {
      return this.optimizeUnary(expr);
    }
    if (expr instanceof GroupExpr) {
      const inner = this.optimizeExpr(expr.expression);
      // Remove redundant grouping
      return inner;
    }
    if (expr instanceof CallExpr) {
      const callee = this.optimizeExpr(expr.callee);
      const args = expr.args.map((a) => this.optimizeExpr(a));
      return new CallExpr(expr.range, callee, args, expr.resolvedType);
    }
    // Literals and identifiers are already optimal
    return expr;
  }

  private optimizeBinary(expr: BinaryExpr): Expr {
    const left = this.optimizeExpr(expr.left);
    const right = this.optimizeExpr(expr.right);

    // Constant folding for integer operations
    if (left instanceof IntLiteral && right instanceof IntLiteral) {
      const lv = left.value;
      const rv = right.value;
      this.changes++;
      switch (expr.op) {
        case BinaryOp.Add: return new IntLiteral(expr.range, lv + rv);
        case BinaryOp.Subtract: return new IntLiteral(expr.range, lv - rv);
        case BinaryOp.Multiply: return new IntLiteral(expr.range, lv * rv);
        case BinaryOp.Divide:
          if (rv !== 0) return new IntLiteral(expr.range, Math.floor(lv / rv));
          break;
        case BinaryOp.Modulo:
          if (rv !== 0) return new IntLiteral(expr.range, lv % rv);
          break;
        case BinaryOp.Equal: return new BoolLiteral(expr.range, lv === rv);
        case BinaryOp.NotEqual: return new BoolLiteral(expr.range, lv !== rv);
        case BinaryOp.LessThan: return new BoolLiteral(expr.range, lv < rv);
        case BinaryOp.GreaterThan: return new BoolLiteral(expr.range, lv > rv);
        case BinaryOp.LessEqual: return new BoolLiteral(expr.range, lv <= rv);
        case BinaryOp.GreaterEqual: return new BoolLiteral(expr.range, lv >= rv);
      }
    }

    // Constant folding for float operations
    if (left instanceof FloatLiteral && right instanceof FloatLiteral) {
      const lv = left.value;
      const rv = right.value;
      this.changes++;
      switch (expr.op) {
        case BinaryOp.Add: return new FloatLiteral(expr.range, lv + rv);
        case BinaryOp.Subtract: return new FloatLiteral(expr.range, lv - rv);
        case BinaryOp.Multiply: return new FloatLiteral(expr.range, lv * rv);
        case BinaryOp.Divide:
          if (rv !== 0) return new FloatLiteral(expr.range, lv / rv);
          break;
        case BinaryOp.Equal: return new BoolLiteral(expr.range, lv === rv);
        case BinaryOp.NotEqual: return new BoolLiteral(expr.range, lv !== rv);
        case BinaryOp.LessThan: return new BoolLiteral(expr.range, lv < rv);
        case BinaryOp.GreaterThan: return new BoolLiteral(expr.range, lv > rv);
        case BinaryOp.LessEqual: return new BoolLiteral(expr.range, lv <= rv);
        case BinaryOp.GreaterEqual: return new BoolLiteral(expr.range, lv >= rv);
      }
    }

    // Constant folding for boolean operations
    if (left instanceof BoolLiteral && right instanceof BoolLiteral) {
      const lv = left.value;
      const rv = right.value;
      this.changes++;
      switch (expr.op) {
        case BinaryOp.Equal: return new BoolLiteral(expr.range, lv === rv);
        case BinaryOp.NotEqual: return new BoolLiteral(expr.range, lv !== rv);
        case BinaryOp.And: return new BoolLiteral(expr.range, lv && rv);
        case BinaryOp.Or: return new BoolLiteral(expr.range, lv || rv);
      }
    }

    // Remove division by 1 and multiplication by 1
    if (right instanceof IntLiteral && right.value === 1) {
      if (expr.op === BinaryOp.Multiply || expr.op === BinaryOp.Divide) {
        this.changes++;
        return left;
      }
    }

    return new BinaryExpr(expr.range, left, expr.op, right, expr.resolvedType);
  }

  private optimizeUnary(expr: UnaryExpr): Expr {
    const operand = this.optimizeExpr(expr.operand);

    // Double negation elimination
    if (operand instanceof UnaryExpr && operand.op === expr.op) {
      if (expr.op === UnaryOp.Not) {
        this.changes++;
        return operand.operand;
      }
    }

    // Constant folding for unary negation
    if (expr.op === UnaryOp.Negate) {
      if (operand instanceof IntLiteral) {
        this.changes++;
        return new IntLiteral(expr.range, -operand.value);
      }
      if (operand instanceof FloatLiteral) {
        this.changes++;
        return new FloatLiteral(expr.range, -operand.value);
      }
    }

    // Constant folding for logical not
    if (expr.op === UnaryOp.Not) {
      if (operand instanceof BoolLiteral) {
        this.changes++;
        return new BoolLiteral(expr.range, !operand.value);
      }
    }

    return new UnaryExpr(expr.range, expr.op, operand, expr.resolvedType);
  }
}
