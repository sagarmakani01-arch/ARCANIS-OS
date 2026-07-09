export interface SourceLocation {
    line: number;
    column: number;
    offset: number;
}
export interface SourceRange {
    start: SourceLocation;
    end: SourceLocation;
    sourceId: string;
}
export type TokenKind = 'EOF' | 'IDENTIFIER' | 'INT_LITERAL' | 'FLOAT_LITERAL' | 'STRING_LITERAL' | 'BOOL_LITERAL' | 'UNIT_LITERAL' | 'KEYWORD' | 'OPERATOR' | 'OPEN_PAREN' | 'CLOSE_PAREN' | 'OPEN_BRACE' | 'CLOSE_BRACE' | 'OPEN_BRACKET' | 'CLOSE_BRACKET' | 'SEMICOLON' | 'COLON' | 'COMMA' | 'DOT' | 'ARROW' | 'PIPE';
export declare enum Keyword {
    Let = "let",
    Fun = "fun",
    If = "if",
    Else = "else",
    While = "while",
    Return = "return",
    True = "true",
    False = "false"
}
export declare enum TypeKind {
    Int = "Int",
    Float = "Float",
    Bool = "Bool",
    String = "String",
    Unit = "Unit",
    Function = "Function",
    Infer = "Infer"
}
export declare class Type {
    readonly kind: TypeKind;
    readonly paramTypes?: Type[] | undefined;
    readonly returnType?: Type | undefined;
    constructor(kind: TypeKind, paramTypes?: Type[] | undefined, returnType?: Type | undefined);
    static int(): Type;
    static float(): Type;
    static bool(): Type;
    static string(): Type;
    static unit(): Type;
    static function(paramTypes: Type[], returnType: Type): Type;
    static infer(): Type;
    equals(other: Type): boolean;
    toString(): string;
}
export declare enum UnaryOp {
    Negate = "-",
    Not = "!"
}
export declare enum BinaryOp {
    Add = "+",
    Subtract = "-",
    Multiply = "*",
    Divide = "/",
    Modulo = "%",
    Equal = "==",
    NotEqual = "!=",
    LessThan = "<",
    GreaterThan = ">",
    LessEqual = "<=",
    GreaterEqual = ">=",
    And = "&&",
    Or = "||",
    Assign = "="
}
export declare enum CompilerStage {
    Lexing = "lexing",
    Parsing = "parsing",
    AstGeneration = "ast_generation",
    TypeChecking = "type_checking",
    Optimization = "optimization",
    CodeGeneration = "code_generation"
}
export declare enum Severity {
    Error = "error",
    Warning = "warning",
    Info = "info"
}
export interface CompilerDiagnostic {
    severity: Severity;
    message: string;
    range?: SourceRange;
    code?: string;
    hints?: string[];
}
//# sourceMappingURL=types.d.ts.map