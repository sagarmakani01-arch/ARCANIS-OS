"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Optimizer = void 0;
const ast_1 = require("../parser/ast");
const types_1 = require("../types");
class Optimizer {
    constructor() {
        this.changes = 0;
    }
    optimize(program) {
        this.changes = 0;
        const optimizedFunctions = program.functions.map((fn) => this.optimizeFunction(fn));
        const optimizedStmts = program.statements.map((stmt) => this.optimizeStmt(stmt));
        return new ast_1.Program(program.range, optimizedFunctions, optimizedStmts);
    }
    getChangeCount() {
        return this.changes;
    }
    optimizeFunction(fn) {
        const body = this.optimizeBlock(fn.body);
        return new ast_1.FunctionDecl(fn.range, fn.name, fn.params, fn.returnType, body, fn.resolvedType);
    }
    optimizeStmt(stmt) {
        if (stmt instanceof ast_1.VarDecl) {
            return this.optimizeVarDecl(stmt);
        }
        if (stmt instanceof ast_1.BlockStmt) {
            const block = this.optimizeBlock(stmt);
            // Flatten single-statement blocks if beneficial
            return block;
        }
        if (stmt instanceof ast_1.ExprStmt) {
            const expr = this.optimizeExpr(stmt.expression);
            return new ast_1.ExprStmt(stmt.range, expr);
        }
        if (stmt instanceof ast_1.IfStmt) {
            return this.optimizeIfStmt(stmt);
        }
        if (stmt instanceof ast_1.WhileStmt) {
            return this.optimizeWhileStmt(stmt);
        }
        if (stmt instanceof ast_1.ReturnStmt) {
            const value = stmt.value ? this.optimizeExpr(stmt.value) : undefined;
            return new ast_1.ReturnStmt(stmt.range, value);
        }
        return stmt;
    }
    optimizeVarDecl(stmt) {
        const init = stmt.initializer ? this.optimizeExpr(stmt.initializer) : undefined;
        return new ast_1.VarDecl(stmt.range, stmt.name, stmt.varType, init);
    }
    optimizeBlock(block) {
        const stmts = block.statements.map((s) => this.optimizeStmt(s));
        return new ast_1.BlockStmt(block.range, stmts);
    }
    optimizeIfStmt(stmt) {
        const cond = this.optimizeExpr(stmt.condition);
        const thenBranch = this.optimizeStmt(stmt.thenBranch);
        // Constant folding: if condition is a boolean literal
        if (cond instanceof ast_1.BoolLiteral) {
            this.changes++;
            if (cond.value) {
                return thenBranch;
            }
            else if (stmt.elseBranch) {
                return this.optimizeStmt(stmt.elseBranch);
            }
            else {
                // Empty statement - return a minimal block
                return new ast_1.BlockStmt(stmt.range, []);
            }
        }
        const elseBranch = stmt.elseBranch ? this.optimizeStmt(stmt.elseBranch) : undefined;
        return new ast_1.IfStmt(stmt.range, cond, thenBranch, elseBranch);
    }
    optimizeWhileStmt(stmt) {
        const cond = this.optimizeExpr(stmt.condition);
        // Remove while(false) loops
        if (cond instanceof ast_1.BoolLiteral && !cond.value) {
            this.changes++;
            return new ast_1.BlockStmt(stmt.range, []);
        }
        const body = this.optimizeStmt(stmt.body);
        return new ast_1.WhileStmt(stmt.range, cond, body);
    }
    optimizeExpr(expr) {
        if (expr instanceof ast_1.BinaryExpr) {
            return this.optimizeBinary(expr);
        }
        if (expr instanceof ast_1.UnaryExpr) {
            return this.optimizeUnary(expr);
        }
        if (expr instanceof ast_1.GroupExpr) {
            const inner = this.optimizeExpr(expr.expression);
            // Remove redundant grouping
            return inner;
        }
        if (expr instanceof ast_1.CallExpr) {
            const callee = this.optimizeExpr(expr.callee);
            const args = expr.args.map((a) => this.optimizeExpr(a));
            return new ast_1.CallExpr(expr.range, callee, args, expr.resolvedType);
        }
        // Literals and identifiers are already optimal
        return expr;
    }
    optimizeBinary(expr) {
        const left = this.optimizeExpr(expr.left);
        const right = this.optimizeExpr(expr.right);
        // Constant folding for integer operations
        if (left instanceof ast_1.IntLiteral && right instanceof ast_1.IntLiteral) {
            const lv = left.value;
            const rv = right.value;
            this.changes++;
            switch (expr.op) {
                case types_1.BinaryOp.Add: return new ast_1.IntLiteral(expr.range, lv + rv);
                case types_1.BinaryOp.Subtract: return new ast_1.IntLiteral(expr.range, lv - rv);
                case types_1.BinaryOp.Multiply: return new ast_1.IntLiteral(expr.range, lv * rv);
                case types_1.BinaryOp.Divide:
                    if (rv !== 0)
                        return new ast_1.IntLiteral(expr.range, Math.floor(lv / rv));
                    break;
                case types_1.BinaryOp.Modulo:
                    if (rv !== 0)
                        return new ast_1.IntLiteral(expr.range, lv % rv);
                    break;
                case types_1.BinaryOp.Equal: return new ast_1.BoolLiteral(expr.range, lv === rv);
                case types_1.BinaryOp.NotEqual: return new ast_1.BoolLiteral(expr.range, lv !== rv);
                case types_1.BinaryOp.LessThan: return new ast_1.BoolLiteral(expr.range, lv < rv);
                case types_1.BinaryOp.GreaterThan: return new ast_1.BoolLiteral(expr.range, lv > rv);
                case types_1.BinaryOp.LessEqual: return new ast_1.BoolLiteral(expr.range, lv <= rv);
                case types_1.BinaryOp.GreaterEqual: return new ast_1.BoolLiteral(expr.range, lv >= rv);
            }
        }
        // Constant folding for float operations
        if (left instanceof ast_1.FloatLiteral && right instanceof ast_1.FloatLiteral) {
            const lv = left.value;
            const rv = right.value;
            this.changes++;
            switch (expr.op) {
                case types_1.BinaryOp.Add: return new ast_1.FloatLiteral(expr.range, lv + rv);
                case types_1.BinaryOp.Subtract: return new ast_1.FloatLiteral(expr.range, lv - rv);
                case types_1.BinaryOp.Multiply: return new ast_1.FloatLiteral(expr.range, lv * rv);
                case types_1.BinaryOp.Divide:
                    if (rv !== 0)
                        return new ast_1.FloatLiteral(expr.range, lv / rv);
                    break;
                case types_1.BinaryOp.Equal: return new ast_1.BoolLiteral(expr.range, lv === rv);
                case types_1.BinaryOp.NotEqual: return new ast_1.BoolLiteral(expr.range, lv !== rv);
                case types_1.BinaryOp.LessThan: return new ast_1.BoolLiteral(expr.range, lv < rv);
                case types_1.BinaryOp.GreaterThan: return new ast_1.BoolLiteral(expr.range, lv > rv);
                case types_1.BinaryOp.LessEqual: return new ast_1.BoolLiteral(expr.range, lv <= rv);
                case types_1.BinaryOp.GreaterEqual: return new ast_1.BoolLiteral(expr.range, lv >= rv);
            }
        }
        // Constant folding for boolean operations
        if (left instanceof ast_1.BoolLiteral && right instanceof ast_1.BoolLiteral) {
            const lv = left.value;
            const rv = right.value;
            this.changes++;
            switch (expr.op) {
                case types_1.BinaryOp.Equal: return new ast_1.BoolLiteral(expr.range, lv === rv);
                case types_1.BinaryOp.NotEqual: return new ast_1.BoolLiteral(expr.range, lv !== rv);
                case types_1.BinaryOp.And: return new ast_1.BoolLiteral(expr.range, lv && rv);
                case types_1.BinaryOp.Or: return new ast_1.BoolLiteral(expr.range, lv || rv);
            }
        }
        // Remove division by 1 and multiplication by 1
        if (right instanceof ast_1.IntLiteral && right.value === 1) {
            if (expr.op === types_1.BinaryOp.Multiply || expr.op === types_1.BinaryOp.Divide) {
                this.changes++;
                return left;
            }
        }
        return new ast_1.BinaryExpr(expr.range, left, expr.op, right, expr.resolvedType);
    }
    optimizeUnary(expr) {
        const operand = this.optimizeExpr(expr.operand);
        // Double negation elimination
        if (operand instanceof ast_1.UnaryExpr && operand.op === expr.op) {
            if (expr.op === types_1.UnaryOp.Not) {
                this.changes++;
                return operand.operand;
            }
        }
        // Constant folding for unary negation
        if (expr.op === types_1.UnaryOp.Negate) {
            if (operand instanceof ast_1.IntLiteral) {
                this.changes++;
                return new ast_1.IntLiteral(expr.range, -operand.value);
            }
            if (operand instanceof ast_1.FloatLiteral) {
                this.changes++;
                return new ast_1.FloatLiteral(expr.range, -operand.value);
            }
        }
        // Constant folding for logical not
        if (expr.op === types_1.UnaryOp.Not) {
            if (operand instanceof ast_1.BoolLiteral) {
                this.changes++;
                return new ast_1.BoolLiteral(expr.range, !operand.value);
            }
        }
        return new ast_1.UnaryExpr(expr.range, expr.op, operand, expr.resolvedType);
    }
}
exports.Optimizer = Optimizer;
//# sourceMappingURL=optimizer.js.map