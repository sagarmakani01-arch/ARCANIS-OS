import {
  Program, FunctionDecl, ParamDecl, VarDecl, BlockStmt, ExprStmt,
  IfStmt, WhileStmt, ReturnStmt, BinaryExpr, UnaryExpr, CallExpr,
  Identifier, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
  UnitLiteral, GroupExpr, Stmt, Expr,
} from '../parser/ast';
import { ErrorReporter } from '../error';
import {
  Type, TypeKind, BinaryOp, UnaryOp, CompilerStage,
} from '../types';

interface TypeEnv {
  variables: Map<string, Type>;
  functions: Map<string, FunctionSignature>;
  returnType: Type;
  parent?: TypeEnv;
}

function lookupVariable(name: string, env: TypeEnv): Type | undefined {
  let current: TypeEnv | undefined = env;
  while (current) {
    if (current.variables.has(name)) return current.variables.get(name);
    current = current.parent;
  }
  return undefined;
}

interface FunctionSignature {
  paramTypes: Type[];
  returnType: Type;
}

export class TypeChecker {
  private errors: ErrorReporter;
  private sourceId: string;

  constructor(sourceId: string, errors: ErrorReporter) {
    this.sourceId = sourceId;
    this.errors = errors;
  }

  check(program: Program): void {
    const builtins: Map<string, FunctionSignature> = new Map();

    builtins.set('print', { paramTypes: [Type.string()], returnType: Type.unit() });
    builtins.set('println', { paramTypes: [Type.string()], returnType: Type.unit() });
    builtins.set('printlnInt', { paramTypes: [Type.int()], returnType: Type.unit() });
    builtins.set('readInt', { paramTypes: [], returnType: Type.int() });
    builtins.set('readString', { paramTypes: [], returnType: Type.string() });
    builtins.set('intToString', { paramTypes: [Type.int()], returnType: Type.string() });
    builtins.set('floatToString', { paramTypes: [Type.float()], returnType: Type.string() });

    // Collect function declarations
    for (const fn of program.functions) {
      const paramTypes = fn.params.map((p) => p.paramType);
      builtins.set(fn.name, { paramTypes, returnType: fn.returnType });
    }

    // Check each function
    for (const fn of program.functions) {
      const env: TypeEnv = {
        variables: new Map(),
        functions: builtins,
        returnType: fn.returnType,
      };

      for (const param of fn.params) {
        env.variables.set(param.name, param.paramType);
      }

      this.checkStmt(fn.body, env);
    }
  }

  private checkStmt(stmt: Stmt, env: TypeEnv): void {
    if (stmt instanceof VarDecl) {
      this.checkVarDecl(stmt, env);
    } else if (stmt instanceof BlockStmt) {
      this.checkBlockStmt(stmt, env);
    } else if (stmt instanceof ExprStmt) {
      this.checkExpr(stmt.expression, env);
    } else if (stmt instanceof IfStmt) {
      this.checkIfStmt(stmt, env);
    } else if (stmt instanceof WhileStmt) {
      this.checkWhileStmt(stmt, env);
    } else if (stmt instanceof ReturnStmt) {
      this.checkReturnStmt(stmt, env);
    }
  }

  private checkVarDecl(stmt: VarDecl, env: TypeEnv): void {
    let declaredType = stmt.varType;

    if (stmt.initializer) {
      const initType = this.checkExpr(stmt.initializer, env);

      if (declaredType.kind === TypeKind.Infer) {
        declaredType = initType;
      } else if (!declaredType.equals(initType)) {
        this.errors.error(
          CompilerStage.TypeChecking,
          `Type mismatch: variable '${stmt.name}' declared as ${declaredType} but initializer has type ${initType}`,
          stmt.range,
          [`Change the type to ${initType} or change the initializer to match ${declaredType}`],
        );
      }
    }

    if (env.variables.has(stmt.name)) {
      this.errors.error(
        CompilerStage.TypeChecking,
        `Variable '${stmt.name}' is already defined in this scope`,
        stmt.range,
        ['Rename the variable to avoid shadowing'],
      );
    }

    env.variables.set(stmt.name, declaredType);
  }

  private checkBlockStmt(stmt: BlockStmt, env: TypeEnv): void {
    const scopedEnv: TypeEnv = {
      variables: new Map(),
      functions: env.functions,
      returnType: env.returnType,
      parent: env,
    };
    for (const s of stmt.statements) {
      this.checkStmt(s, scopedEnv);
    }
  }

  private checkIfStmt(stmt: IfStmt, env: TypeEnv): void {
    const condType = this.checkExpr(stmt.condition, env);
    if (!condType.equals(Type.bool())) {
      this.errors.error(
        CompilerStage.TypeChecking,
        `If condition must be Bool, got ${condType}`,
        stmt.condition.range,
      );
    }
    this.checkStmt(stmt.thenBranch, env);
    if (stmt.elseBranch) {
      this.checkStmt(stmt.elseBranch, env);
    }
  }

  private checkWhileStmt(stmt: WhileStmt, env: TypeEnv): void {
    const condType = this.checkExpr(stmt.condition, env);
    if (!condType.equals(Type.bool())) {
      this.errors.error(
        CompilerStage.TypeChecking,
        `While condition must be Bool, got ${condType}`,
        stmt.condition.range,
      );
    }
    this.checkStmt(stmt.body, env);
  }

  private checkReturnStmt(stmt: ReturnStmt, env: TypeEnv): void {
    if (stmt.value) {
      const valueType = this.checkExpr(stmt.value, env);
      if (!valueType.equals(env.returnType)) {
        this.errors.error(
          CompilerStage.TypeChecking,
          `Return type mismatch: expected ${env.returnType}, got ${valueType}`,
          stmt.value.range,
        );
      }
    } else if (!env.returnType.equals(Type.unit())) {
      this.errors.error(
        CompilerStage.TypeChecking,
        `Expected return value of type ${env.returnType}`,
        stmt.range,
      );
    }
  }

  private checkExpr(expr: Expr, env: TypeEnv): Type {
    if (expr instanceof IntLiteral) {
      return Type.int();
    }
    if (expr instanceof FloatLiteral) {
      return Type.float();
    }
    if (expr instanceof StringLiteral) {
      return Type.string();
    }
    if (expr instanceof BoolLiteral) {
      return Type.bool();
    }
    if (expr instanceof UnitLiteral) {
      return Type.unit();
    }
    if (expr instanceof Identifier) {
      return this.checkIdentifier(expr, env);
    }
    if (expr instanceof GroupExpr) {
      return this.checkExpr(expr.expression, env);
    }
    if (expr instanceof UnaryExpr) {
      return this.checkUnary(expr, env);
    }
    if (expr instanceof BinaryExpr) {
      return this.checkBinary(expr, env);
    }
    if (expr instanceof CallExpr) {
      return this.checkCall(expr, env);
    }
    return Type.unit();
  }

  private checkIdentifier(expr: Identifier, env: TypeEnv): Type {
    const type = lookupVariable(expr.name, env);
    if (!type) {
      this.errors.error(
        CompilerStage.TypeChecking,
        `Undefined variable '${expr.name}'`,
        expr.range,
        [`Check that '${expr.name}' has been declared in this scope`],
      );
      return Type.unit();
    }
    expr.resolvedType = type;
    return type;
  }

  private checkUnary(expr: UnaryExpr, env: TypeEnv): Type {
    const operandType = this.checkExpr(expr.operand, env);

    switch (expr.op) {
      case UnaryOp.Negate:
        if (!operandType.equals(Type.int()) && !operandType.equals(Type.float())) {
          this.errors.error(
            CompilerStage.TypeChecking,
            `Cannot negate ${operandType}, expected Int or Float`,
            expr.range,
          );
        }
        expr.resolvedType = operandType;
        return operandType;

      case UnaryOp.Not:
        if (!operandType.equals(Type.bool())) {
          this.errors.error(
            CompilerStage.TypeChecking,
            `Cannot apply logical not to ${operandType}, expected Bool`,
            expr.range,
          );
        }
        expr.resolvedType = Type.bool();
        return Type.bool();
    }
  }

  private checkBinary(expr: BinaryExpr, env: TypeEnv): Type {
    const leftType = this.checkExpr(expr.left, env);
    const rightType = this.checkExpr(expr.right, env);

    switch (expr.op) {
      case BinaryOp.Add:
      case BinaryOp.Subtract:
      case BinaryOp.Multiply:
      case BinaryOp.Divide:
      case BinaryOp.Modulo: {
        if (leftType.equals(Type.int()) && rightType.equals(Type.int())) {
          expr.resolvedType = Type.int();
          return Type.int();
        }
        if (leftType.equals(Type.float()) && rightType.equals(Type.float())) {
          expr.resolvedType = Type.float();
          return Type.float();
        }
        if (leftType.equals(Type.string()) && expr.op === BinaryOp.Add) {
          expr.resolvedType = Type.string();
          return Type.string();
        }
        this.errors.error(
          CompilerStage.TypeChecking,
          `Cannot apply '${expr.op}' to ${leftType} and ${rightType}`,
          expr.range,
        );
        expr.resolvedType = Type.int();
        return Type.int();
      }

      case BinaryOp.Equal:
      case BinaryOp.NotEqual: {
        if (!leftType.equals(rightType)) {
          this.errors.error(
            CompilerStage.TypeChecking,
            `Cannot compare ${leftType} with ${rightType}`,
            expr.range,
          );
        }
        expr.resolvedType = Type.bool();
        return Type.bool();
      }

      case BinaryOp.LessThan:
      case BinaryOp.GreaterThan:
      case BinaryOp.LessEqual:
      case BinaryOp.GreaterEqual: {
        if (!leftType.equals(rightType) ||
            !(leftType.equals(Type.int()) || leftType.equals(Type.float()))) {
          this.errors.error(
            CompilerStage.TypeChecking,
            `Cannot apply '${expr.op}' to ${leftType} and ${rightType}`,
            expr.range,
          );
        }
        expr.resolvedType = Type.bool();
        return Type.bool();
      }

      case BinaryOp.And:
      case BinaryOp.Or: {
        if (!leftType.equals(Type.bool()) || !rightType.equals(Type.bool())) {
          this.errors.error(
            CompilerStage.TypeChecking,
            `Cannot apply '${expr.op}' to ${leftType} and ${rightType}, expected Bool`,
            expr.range,
          );
        }
        expr.resolvedType = Type.bool();
        return Type.bool();
      }

      case BinaryOp.Assign: {
        if (!leftType.equals(rightType)) {
          this.errors.error(
            CompilerStage.TypeChecking,
            `Cannot assign ${rightType} to variable of type ${leftType}`,
            expr.range,
          );
        }
        expr.resolvedType = Type.unit();
        return Type.unit();
      }
    }
  }

  private checkCall(expr: CallExpr, env: TypeEnv): Type {
    let calleeType: Type;

    if (expr.callee instanceof Identifier) {
      const fnName = expr.callee.name;
      const sig = env.functions.get(fnName);

      if (!sig) {
        this.errors.error(
          CompilerStage.TypeChecking,
          `Undefined function '${fnName}'`,
          expr.callee.range,
          [`Check that '${fnName}' is defined or spelled correctly`],
        );
        expr.resolvedType = Type.unit();
        return Type.unit();
      }

      calleeType = Type.function(sig.paramTypes, sig.returnType);

      // Check argument count
      if (expr.args.length !== sig.paramTypes.length) {
        this.errors.error(
          CompilerStage.TypeChecking,
          `Function '${fnName}' expects ${sig.paramTypes.length} arguments but got ${expr.args.length}`,
          expr.range,
        );
        expr.resolvedType = sig.returnType;
        return sig.returnType;
      }

      // Check argument types
      for (let i = 0; i < expr.args.length; i++) {
        const argType = this.checkExpr(expr.args[i], env);
        if (!argType.equals(sig.paramTypes[i])) {
          this.errors.error(
            CompilerStage.TypeChecking,
            `Argument ${i + 1} of '${fnName}' expects ${sig.paramTypes[i]} but got ${argType}`,
            expr.args[i].range,
          );
        }
      }

      expr.resolvedType = sig.returnType;
      return sig.returnType;
    }

    // If callee is not a simple identifier, check it as an expression
    calleeType = this.checkExpr(expr.callee, env);
    expr.resolvedType = Type.unit();
    return Type.unit();
  }
}
