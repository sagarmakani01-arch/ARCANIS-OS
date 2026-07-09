"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TypeChecker = void 0;
const ast_1 = require("../parser/ast");
const types_1 = require("../types");
function lookupVariable(name, env) {
    let current = env;
    while (current) {
        if (current.variables.has(name))
            return current.variables.get(name);
        current = current.parent;
    }
    return undefined;
}
class TypeChecker {
    constructor(sourceId, errors) {
        this.sourceId = sourceId;
        this.errors = errors;
    }
    check(program) {
        const builtins = new Map();
        builtins.set('print', { paramTypes: [types_1.Type.string()], returnType: types_1.Type.unit() });
        builtins.set('println', { paramTypes: [types_1.Type.string()], returnType: types_1.Type.unit() });
        builtins.set('printlnInt', { paramTypes: [types_1.Type.int()], returnType: types_1.Type.unit() });
        builtins.set('readInt', { paramTypes: [], returnType: types_1.Type.int() });
        builtins.set('readString', { paramTypes: [], returnType: types_1.Type.string() });
        builtins.set('intToString', { paramTypes: [types_1.Type.int()], returnType: types_1.Type.string() });
        builtins.set('floatToString', { paramTypes: [types_1.Type.float()], returnType: types_1.Type.string() });
        // Collect function declarations
        for (const fn of program.functions) {
            const paramTypes = fn.params.map((p) => p.paramType);
            builtins.set(fn.name, { paramTypes, returnType: fn.returnType });
        }
        // Check each function
        for (const fn of program.functions) {
            const env = {
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
    checkStmt(stmt, env) {
        if (stmt instanceof ast_1.VarDecl) {
            this.checkVarDecl(stmt, env);
        }
        else if (stmt instanceof ast_1.BlockStmt) {
            this.checkBlockStmt(stmt, env);
        }
        else if (stmt instanceof ast_1.ExprStmt) {
            this.checkExpr(stmt.expression, env);
        }
        else if (stmt instanceof ast_1.IfStmt) {
            this.checkIfStmt(stmt, env);
        }
        else if (stmt instanceof ast_1.WhileStmt) {
            this.checkWhileStmt(stmt, env);
        }
        else if (stmt instanceof ast_1.ReturnStmt) {
            this.checkReturnStmt(stmt, env);
        }
    }
    checkVarDecl(stmt, env) {
        let declaredType = stmt.varType;
        if (stmt.initializer) {
            const initType = this.checkExpr(stmt.initializer, env);
            if (declaredType.kind === types_1.TypeKind.Infer) {
                declaredType = initType;
            }
            else if (!declaredType.equals(initType)) {
                this.errors.error(types_1.CompilerStage.TypeChecking, `Type mismatch: variable '${stmt.name}' declared as ${declaredType} but initializer has type ${initType}`, stmt.range, [`Change the type to ${initType} or change the initializer to match ${declaredType}`]);
            }
        }
        if (env.variables.has(stmt.name)) {
            this.errors.error(types_1.CompilerStage.TypeChecking, `Variable '${stmt.name}' is already defined in this scope`, stmt.range, ['Rename the variable to avoid shadowing']);
        }
        env.variables.set(stmt.name, declaredType);
    }
    checkBlockStmt(stmt, env) {
        const scopedEnv = {
            variables: new Map(),
            functions: env.functions,
            returnType: env.returnType,
            parent: env,
        };
        for (const s of stmt.statements) {
            this.checkStmt(s, scopedEnv);
        }
    }
    checkIfStmt(stmt, env) {
        const condType = this.checkExpr(stmt.condition, env);
        if (!condType.equals(types_1.Type.bool())) {
            this.errors.error(types_1.CompilerStage.TypeChecking, `If condition must be Bool, got ${condType}`, stmt.condition.range);
        }
        this.checkStmt(stmt.thenBranch, env);
        if (stmt.elseBranch) {
            this.checkStmt(stmt.elseBranch, env);
        }
    }
    checkWhileStmt(stmt, env) {
        const condType = this.checkExpr(stmt.condition, env);
        if (!condType.equals(types_1.Type.bool())) {
            this.errors.error(types_1.CompilerStage.TypeChecking, `While condition must be Bool, got ${condType}`, stmt.condition.range);
        }
        this.checkStmt(stmt.body, env);
    }
    checkReturnStmt(stmt, env) {
        if (stmt.value) {
            const valueType = this.checkExpr(stmt.value, env);
            if (!valueType.equals(env.returnType)) {
                this.errors.error(types_1.CompilerStage.TypeChecking, `Return type mismatch: expected ${env.returnType}, got ${valueType}`, stmt.value.range);
            }
        }
        else if (!env.returnType.equals(types_1.Type.unit())) {
            this.errors.error(types_1.CompilerStage.TypeChecking, `Expected return value of type ${env.returnType}`, stmt.range);
        }
    }
    checkExpr(expr, env) {
        if (expr instanceof ast_1.IntLiteral) {
            return types_1.Type.int();
        }
        if (expr instanceof ast_1.FloatLiteral) {
            return types_1.Type.float();
        }
        if (expr instanceof ast_1.StringLiteral) {
            return types_1.Type.string();
        }
        if (expr instanceof ast_1.BoolLiteral) {
            return types_1.Type.bool();
        }
        if (expr instanceof ast_1.UnitLiteral) {
            return types_1.Type.unit();
        }
        if (expr instanceof ast_1.Identifier) {
            return this.checkIdentifier(expr, env);
        }
        if (expr instanceof ast_1.GroupExpr) {
            return this.checkExpr(expr.expression, env);
        }
        if (expr instanceof ast_1.UnaryExpr) {
            return this.checkUnary(expr, env);
        }
        if (expr instanceof ast_1.BinaryExpr) {
            return this.checkBinary(expr, env);
        }
        if (expr instanceof ast_1.CallExpr) {
            return this.checkCall(expr, env);
        }
        return types_1.Type.unit();
    }
    checkIdentifier(expr, env) {
        const type = lookupVariable(expr.name, env);
        if (!type) {
            this.errors.error(types_1.CompilerStage.TypeChecking, `Undefined variable '${expr.name}'`, expr.range, [`Check that '${expr.name}' has been declared in this scope`]);
            return types_1.Type.unit();
        }
        expr.resolvedType = type;
        return type;
    }
    checkUnary(expr, env) {
        const operandType = this.checkExpr(expr.operand, env);
        switch (expr.op) {
            case types_1.UnaryOp.Negate:
                if (!operandType.equals(types_1.Type.int()) && !operandType.equals(types_1.Type.float())) {
                    this.errors.error(types_1.CompilerStage.TypeChecking, `Cannot negate ${operandType}, expected Int or Float`, expr.range);
                }
                expr.resolvedType = operandType;
                return operandType;
            case types_1.UnaryOp.Not:
                if (!operandType.equals(types_1.Type.bool())) {
                    this.errors.error(types_1.CompilerStage.TypeChecking, `Cannot apply logical not to ${operandType}, expected Bool`, expr.range);
                }
                expr.resolvedType = types_1.Type.bool();
                return types_1.Type.bool();
        }
    }
    checkBinary(expr, env) {
        const leftType = this.checkExpr(expr.left, env);
        const rightType = this.checkExpr(expr.right, env);
        switch (expr.op) {
            case types_1.BinaryOp.Add:
            case types_1.BinaryOp.Subtract:
            case types_1.BinaryOp.Multiply:
            case types_1.BinaryOp.Divide:
            case types_1.BinaryOp.Modulo: {
                if (leftType.equals(types_1.Type.int()) && rightType.equals(types_1.Type.int())) {
                    expr.resolvedType = types_1.Type.int();
                    return types_1.Type.int();
                }
                if (leftType.equals(types_1.Type.float()) && rightType.equals(types_1.Type.float())) {
                    expr.resolvedType = types_1.Type.float();
                    return types_1.Type.float();
                }
                if (leftType.equals(types_1.Type.string()) && expr.op === types_1.BinaryOp.Add) {
                    expr.resolvedType = types_1.Type.string();
                    return types_1.Type.string();
                }
                this.errors.error(types_1.CompilerStage.TypeChecking, `Cannot apply '${expr.op}' to ${leftType} and ${rightType}`, expr.range);
                expr.resolvedType = types_1.Type.int();
                return types_1.Type.int();
            }
            case types_1.BinaryOp.Equal:
            case types_1.BinaryOp.NotEqual: {
                if (!leftType.equals(rightType)) {
                    this.errors.error(types_1.CompilerStage.TypeChecking, `Cannot compare ${leftType} with ${rightType}`, expr.range);
                }
                expr.resolvedType = types_1.Type.bool();
                return types_1.Type.bool();
            }
            case types_1.BinaryOp.LessThan:
            case types_1.BinaryOp.GreaterThan:
            case types_1.BinaryOp.LessEqual:
            case types_1.BinaryOp.GreaterEqual: {
                if (!leftType.equals(rightType) ||
                    !(leftType.equals(types_1.Type.int()) || leftType.equals(types_1.Type.float()))) {
                    this.errors.error(types_1.CompilerStage.TypeChecking, `Cannot apply '${expr.op}' to ${leftType} and ${rightType}`, expr.range);
                }
                expr.resolvedType = types_1.Type.bool();
                return types_1.Type.bool();
            }
            case types_1.BinaryOp.And:
            case types_1.BinaryOp.Or: {
                if (!leftType.equals(types_1.Type.bool()) || !rightType.equals(types_1.Type.bool())) {
                    this.errors.error(types_1.CompilerStage.TypeChecking, `Cannot apply '${expr.op}' to ${leftType} and ${rightType}, expected Bool`, expr.range);
                }
                expr.resolvedType = types_1.Type.bool();
                return types_1.Type.bool();
            }
            case types_1.BinaryOp.Assign: {
                if (!leftType.equals(rightType)) {
                    this.errors.error(types_1.CompilerStage.TypeChecking, `Cannot assign ${rightType} to variable of type ${leftType}`, expr.range);
                }
                expr.resolvedType = types_1.Type.unit();
                return types_1.Type.unit();
            }
        }
    }
    checkCall(expr, env) {
        let calleeType;
        if (expr.callee instanceof ast_1.Identifier) {
            const fnName = expr.callee.name;
            const sig = env.functions.get(fnName);
            if (!sig) {
                this.errors.error(types_1.CompilerStage.TypeChecking, `Undefined function '${fnName}'`, expr.callee.range, [`Check that '${fnName}' is defined or spelled correctly`]);
                expr.resolvedType = types_1.Type.unit();
                return types_1.Type.unit();
            }
            calleeType = types_1.Type.function(sig.paramTypes, sig.returnType);
            // Check argument count
            if (expr.args.length !== sig.paramTypes.length) {
                this.errors.error(types_1.CompilerStage.TypeChecking, `Function '${fnName}' expects ${sig.paramTypes.length} arguments but got ${expr.args.length}`, expr.range);
                expr.resolvedType = sig.returnType;
                return sig.returnType;
            }
            // Check argument types
            for (let i = 0; i < expr.args.length; i++) {
                const argType = this.checkExpr(expr.args[i], env);
                if (!argType.equals(sig.paramTypes[i])) {
                    this.errors.error(types_1.CompilerStage.TypeChecking, `Argument ${i + 1} of '${fnName}' expects ${sig.paramTypes[i]} but got ${argType}`, expr.args[i].range);
                }
            }
            expr.resolvedType = sig.returnType;
            return sig.returnType;
        }
        // If callee is not a simple identifier, check it as an expression
        calleeType = this.checkExpr(expr.callee, env);
        expr.resolvedType = types_1.Type.unit();
        return types_1.Type.unit();
    }
}
exports.TypeChecker = TypeChecker;
//# sourceMappingURL=checker.js.map