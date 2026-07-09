"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Severity = exports.CompilerStage = exports.BinaryOp = exports.UnaryOp = exports.Type = exports.TypeKind = exports.Keyword = void 0;
var Keyword;
(function (Keyword) {
    Keyword["Let"] = "let";
    Keyword["Fun"] = "fun";
    Keyword["If"] = "if";
    Keyword["Else"] = "else";
    Keyword["While"] = "while";
    Keyword["Return"] = "return";
    Keyword["True"] = "true";
    Keyword["False"] = "false";
})(Keyword || (exports.Keyword = Keyword = {}));
var TypeKind;
(function (TypeKind) {
    TypeKind["Int"] = "Int";
    TypeKind["Float"] = "Float";
    TypeKind["Bool"] = "Bool";
    TypeKind["String"] = "String";
    TypeKind["Unit"] = "Unit";
    TypeKind["Function"] = "Function";
    TypeKind["Infer"] = "Infer";
})(TypeKind || (exports.TypeKind = TypeKind = {}));
class Type {
    constructor(kind, paramTypes, returnType) {
        this.kind = kind;
        this.paramTypes = paramTypes;
        this.returnType = returnType;
    }
    static int() {
        return new Type(TypeKind.Int);
    }
    static float() {
        return new Type(TypeKind.Float);
    }
    static bool() {
        return new Type(TypeKind.Bool);
    }
    static string() {
        return new Type(TypeKind.String);
    }
    static unit() {
        return new Type(TypeKind.Unit);
    }
    static function(paramTypes, returnType) {
        return new Type(TypeKind.Function, paramTypes, returnType);
    }
    static infer() {
        return new Type(TypeKind.Infer);
    }
    equals(other) {
        if (this.kind !== other.kind)
            return false;
        if (this.kind === TypeKind.Function) {
            if ((this.paramTypes ?? []).length !== (other.paramTypes ?? []).length)
                return false;
            for (let i = 0; i < (this.paramTypes ?? []).length; i++) {
                if (!this.paramTypes[i].equals(other.paramTypes[i]))
                    return false;
            }
            return this.returnType.equals(other.returnType);
        }
        return true;
    }
    toString() {
        if (this.kind === TypeKind.Function) {
            const params = this.paramTypes.map((p) => p.toString()).join(', ');
            return `(${params}) -> ${this.returnType.toString()}`;
        }
        return this.kind;
    }
}
exports.Type = Type;
var UnaryOp;
(function (UnaryOp) {
    UnaryOp["Negate"] = "-";
    UnaryOp["Not"] = "!";
})(UnaryOp || (exports.UnaryOp = UnaryOp = {}));
var BinaryOp;
(function (BinaryOp) {
    BinaryOp["Add"] = "+";
    BinaryOp["Subtract"] = "-";
    BinaryOp["Multiply"] = "*";
    BinaryOp["Divide"] = "/";
    BinaryOp["Modulo"] = "%";
    BinaryOp["Equal"] = "==";
    BinaryOp["NotEqual"] = "!=";
    BinaryOp["LessThan"] = "<";
    BinaryOp["GreaterThan"] = ">";
    BinaryOp["LessEqual"] = "<=";
    BinaryOp["GreaterEqual"] = ">=";
    BinaryOp["And"] = "&&";
    BinaryOp["Or"] = "||";
    BinaryOp["Assign"] = "=";
})(BinaryOp || (exports.BinaryOp = BinaryOp = {}));
var CompilerStage;
(function (CompilerStage) {
    CompilerStage["Lexing"] = "lexing";
    CompilerStage["Parsing"] = "parsing";
    CompilerStage["AstGeneration"] = "ast_generation";
    CompilerStage["TypeChecking"] = "type_checking";
    CompilerStage["Optimization"] = "optimization";
    CompilerStage["CodeGeneration"] = "code_generation";
})(CompilerStage || (exports.CompilerStage = CompilerStage = {}));
var Severity;
(function (Severity) {
    Severity["Error"] = "error";
    Severity["Warning"] = "warning";
    Severity["Info"] = "info";
})(Severity || (exports.Severity = Severity = {}));
//# sourceMappingURL=types.js.map