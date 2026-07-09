"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GroupExpr = exports.UnitLiteral = exports.BoolLiteral = exports.StringLiteral = exports.FloatLiteral = exports.IntLiteral = exports.Identifier = exports.CallExpr = exports.UnaryExpr = exports.BinaryExpr = exports.ReturnStmt = exports.WhileStmt = exports.IfStmt = exports.ExprStmt = exports.BlockStmt = exports.VarDecl = exports.ParamDecl = exports.FunctionDecl = exports.Program = exports.Node = void 0;
class Node {
    constructor(kind, range) {
        this.kind = kind;
        this.range = range;
    }
}
exports.Node = Node;
class Program extends Node {
    constructor(range, functions, statements) {
        super('Program', range);
        this.functions = functions;
        this.statements = statements;
    }
}
exports.Program = Program;
class FunctionDecl extends Node {
    constructor(range, name, params, returnType, body, resolvedType) {
        super('FunctionDecl', range);
        this.name = name;
        this.params = params;
        this.returnType = returnType;
        this.body = body;
        this.resolvedType = resolvedType;
    }
}
exports.FunctionDecl = FunctionDecl;
class ParamDecl extends Node {
    constructor(range, name, paramType) {
        super('ParamDecl', range);
        this.name = name;
        this.paramType = paramType;
    }
}
exports.ParamDecl = ParamDecl;
class VarDecl extends Node {
    constructor(range, name, varType, initializer) {
        super('VarDecl', range);
        this.name = name;
        this.varType = varType;
        this.initializer = initializer;
    }
}
exports.VarDecl = VarDecl;
class BlockStmt extends Node {
    constructor(range, statements) {
        super('BlockStmt', range);
        this.statements = statements;
    }
}
exports.BlockStmt = BlockStmt;
class ExprStmt extends Node {
    constructor(range, expression) {
        super('ExprStmt', range);
        this.expression = expression;
    }
}
exports.ExprStmt = ExprStmt;
class IfStmt extends Node {
    constructor(range, condition, thenBranch, elseBranch) {
        super('IfStmt', range);
        this.condition = condition;
        this.thenBranch = thenBranch;
        this.elseBranch = elseBranch;
    }
}
exports.IfStmt = IfStmt;
class WhileStmt extends Node {
    constructor(range, condition, body) {
        super('WhileStmt', range);
        this.condition = condition;
        this.body = body;
    }
}
exports.WhileStmt = WhileStmt;
class ReturnStmt extends Node {
    constructor(range, value) {
        super('ReturnStmt', range);
        this.value = value;
    }
}
exports.ReturnStmt = ReturnStmt;
class BinaryExpr extends Node {
    constructor(range, left, op, right, resolvedType) {
        super('BinaryExpr', range);
        this.left = left;
        this.op = op;
        this.right = right;
        this.resolvedType = resolvedType;
    }
}
exports.BinaryExpr = BinaryExpr;
class UnaryExpr extends Node {
    constructor(range, op, operand, resolvedType) {
        super('UnaryExpr', range);
        this.op = op;
        this.operand = operand;
        this.resolvedType = resolvedType;
    }
}
exports.UnaryExpr = UnaryExpr;
class CallExpr extends Node {
    constructor(range, callee, args, resolvedType) {
        super('CallExpr', range);
        this.callee = callee;
        this.args = args;
        this.resolvedType = resolvedType;
    }
}
exports.CallExpr = CallExpr;
class Identifier extends Node {
    constructor(range, name, resolvedType) {
        super('Identifier', range);
        this.name = name;
        this.resolvedType = resolvedType;
    }
}
exports.Identifier = Identifier;
class IntLiteral extends Node {
    constructor(range, value) {
        super('IntLiteral', range);
        this.value = value;
    }
}
exports.IntLiteral = IntLiteral;
class FloatLiteral extends Node {
    constructor(range, value) {
        super('FloatLiteral', range);
        this.value = value;
    }
}
exports.FloatLiteral = FloatLiteral;
class StringLiteral extends Node {
    constructor(range, value) {
        super('StringLiteral', range);
        this.value = value;
    }
}
exports.StringLiteral = StringLiteral;
class BoolLiteral extends Node {
    constructor(range, value) {
        super('BoolLiteral', range);
        this.value = value;
    }
}
exports.BoolLiteral = BoolLiteral;
class UnitLiteral extends Node {
    constructor(range) {
        super('UnitLiteral', range);
    }
}
exports.UnitLiteral = UnitLiteral;
class GroupExpr extends Node {
    constructor(range, expression) {
        super('GroupExpr', range);
        this.expression = expression;
    }
}
exports.GroupExpr = GroupExpr;
//# sourceMappingURL=ast.js.map