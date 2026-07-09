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

export type TokenKind =
  | 'EOF'
  | 'IDENTIFIER'
  | 'INT_LITERAL'
  | 'FLOAT_LITERAL'
  | 'STRING_LITERAL'
  | 'BOOL_LITERAL'
  | 'UNIT_LITERAL'
  | 'KEYWORD'
  | 'OPERATOR'
  | 'OPEN_PAREN'
  | 'CLOSE_PAREN'
  | 'OPEN_BRACE'
  | 'CLOSE_BRACE'
  | 'OPEN_BRACKET'
  | 'CLOSE_BRACKET'
  | 'SEMICOLON'
  | 'COLON'
  | 'COMMA'
  | 'DOT'
  | 'ARROW'
  | 'PIPE';

export enum Keyword {
  Let = 'let',
  Fun = 'fun',
  If = 'if',
  Else = 'else',
  While = 'while',
  Return = 'return',
  True = 'true',
  False = 'false',

}

export enum TypeKind {
  Int = 'Int',
  Float = 'Float',
  Bool = 'Bool',
  String = 'String',
  Unit = 'Unit',
  Function = 'Function',
  Infer = 'Infer',
}

export class Type {
  constructor(
    public readonly kind: TypeKind,
    public readonly paramTypes?: Type[],
    public readonly returnType?: Type,
  ) {}

  static int(): Type {
    return new Type(TypeKind.Int);
  }

  static float(): Type {
    return new Type(TypeKind.Float);
  }

  static bool(): Type {
    return new Type(TypeKind.Bool);
  }

  static string(): Type {
    return new Type(TypeKind.String);
  }

  static unit(): Type {
    return new Type(TypeKind.Unit);
  }

  static function(paramTypes: Type[], returnType: Type): Type {
    return new Type(TypeKind.Function, paramTypes, returnType);
  }

  static infer(): Type {
    return new Type(TypeKind.Infer);
  }

  equals(other: Type): boolean {
    if (this.kind !== other.kind) return false;
    if (this.kind === TypeKind.Function) {
      if ((this.paramTypes ?? []).length !== (other.paramTypes ?? []).length) return false;
      for (let i = 0; i < (this.paramTypes ?? []).length; i++) {
        if (!this.paramTypes![i].equals(other.paramTypes![i])) return false;
      }
      return this.returnType!.equals(other.returnType!);
    }
    return true;
  }

  toString(): string {
    if (this.kind === TypeKind.Function) {
      const params = this.paramTypes!.map((p) => p.toString()).join(', ');
      return `(${params}) -> ${this.returnType!.toString()}`;
    }
    return this.kind;
  }
}

export enum UnaryOp {
  Negate = '-',
  Not = '!',
}

export enum BinaryOp {
  Add = '+',
  Subtract = '-',
  Multiply = '*',
  Divide = '/',
  Modulo = '%',
  Equal = '==',
  NotEqual = '!=',
  LessThan = '<',
  GreaterThan = '>',
  LessEqual = '<=',
  GreaterEqual = '>=',
  And = '&&',
  Or = '||',
  Assign = '=',
}

export enum CompilerStage {
  Lexing = 'lexing',
  Parsing = 'parsing',
  AstGeneration = 'ast_generation',
  TypeChecking = 'type_checking',
  Optimization = 'optimization',
  CodeGeneration = 'code_generation',
}

export enum Severity {
  Error = 'error',
  Warning = 'warning',
  Info = 'info',
}

export interface CompilerDiagnostic {
  severity: Severity;
  message: string;
  range?: SourceRange;
  code?: string;
  hints?: string[];
}
