import { Token } from '../lexer/token';
import {
  Program, FunctionDecl, ParamDecl, VarDecl, BlockStmt, ExprStmt,
  IfStmt, WhileStmt, ReturnStmt, BinaryExpr, UnaryExpr, CallExpr,
  Identifier, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
  UnitLiteral, GroupExpr, Stmt, Expr,
} from './ast';
import { ErrorReporter } from '../error';
import {
  SourceRange, Type, TypeKind, BinaryOp, UnaryOp,
  Keyword, CompilerStage,
} from '../types';

const BINARY_PRECEDENCE: Record<string, number> = {
  '||': 1,
  '&&': 2,
  '==': 3, '!=': 3,
  '<': 4, '>': 4, '<=': 4, '>=': 4,
  '+': 5, '-': 5,
  '*': 6, '/': 6, '%': 6,
};

const UNARY_OPS: Record<string, UnaryOp> = {
  '-': UnaryOp.Negate,
  '!': UnaryOp.Not,
};

const BINARY_OPS: Record<string, BinaryOp> = {
  '+': BinaryOp.Add,
  '-': BinaryOp.Subtract,
  '*': BinaryOp.Multiply,
  '/': BinaryOp.Divide,
  '%': BinaryOp.Modulo,
  '==': BinaryOp.Equal,
  '!=': BinaryOp.NotEqual,
  '<': BinaryOp.LessThan,
  '>': BinaryOp.GreaterThan,
  '<=': BinaryOp.LessEqual,
  '>=': BinaryOp.GreaterEqual,
  '&&': BinaryOp.And,
  '||': BinaryOp.Or,
  '=': BinaryOp.Assign,
};

export class Parser {
  private tokens: Token[];
  private current: number = 0;
  private errors: ErrorReporter;
  private sourceId: string;

  constructor(tokens: Token[], sourceId: string, errors: ErrorReporter) {
    this.tokens = tokens;
    this.sourceId = sourceId;
    this.errors = errors;
  }

  parse(): Program {
    const functions: FunctionDecl[] = [];
    const statements: Stmt[] = [];
    const start = this.peek();

    while (!this.isAtEnd()) {
      if (this.checkKeyword(Keyword.Fun)) {
        functions.push(this.parseFunctionDecl());
      } else {
        statements.push(this.parseStmt());
      }
    }

    const endToken = this.current > 0 ? this.previous() : this.peek();
    const range = this.mergeRange(start.range, endToken.range);
    return new Program(range, functions, statements);
  }

  private parseFunctionDecl(): FunctionDecl {
    const start = this.consumeKeyword(Keyword.Fun, "Expect 'fun' keyword");

    const nameToken = this.consume('IDENTIFIER', 'Expect function name');
    const name = nameToken.lexeme;

    this.consume('OPEN_PAREN', `Expect '(' after function name '${name}'`);

    const params: ParamDecl[] = [];
    if (!this.check('CLOSE_PAREN')) {
      do {
        params.push(this.parseParamDecl());
      } while (this.match('COMMA'));
    }

    this.consume('CLOSE_PAREN', `Expect ')' after parameters`);

    let returnType: Type = Type.unit();
    if (this.match('COLON')) {
      returnType = this.parseType();
    }

    this.consume('OPEN_BRACE', `Expect '{' before function body`);
    const body = this.parseBlockStmt();

    const end = this.previous();
    return new FunctionDecl(
      this.mergeRange(start.range, end.range),
      name,
      params,
      returnType,
      body,
    );
  }

  private parseParamDecl(): ParamDecl {
    const nameToken = this.consume('IDENTIFIER', 'Expect parameter name');
    this.consume('COLON', `Expect ':' after parameter name`);
    const paramType = this.parseType();
    return new ParamDecl(nameToken.range, nameToken.lexeme, paramType);
  }

  private parseStmt(): Stmt {
    if (this.checkKeyword(Keyword.Let)) return this.parseVarDecl();
    if (this.checkKeyword(Keyword.If)) return this.parseIfStmt();
    if (this.checkKeyword(Keyword.While)) return this.parseWhileStmt();
    if (this.checkKeyword(Keyword.Return)) return this.parseReturnStmt();
    if (this.match('OPEN_BRACE')) return this.parseBlockStmt();
    return this.parseExprStmt();
  }

  private parseVarDecl(): VarDecl {
    const start = this.consumeKeyword(Keyword.Let, "Expect 'let' keyword");
    const nameToken = this.consume('IDENTIFIER', 'Expect variable name');

    let varType: Type = Type.infer();
    if (this.match('COLON')) {
      varType = this.parseType();
    }

    let initializer: Expr | undefined;
    if (this.matchOperator('=')) {
      initializer = this.parseExpr();
    }

    this.consume('SEMICOLON', "Expect ';' after variable declaration");
    return new VarDecl(nameToken.range, nameToken.lexeme, varType, initializer);
  }

  private parseBlockStmt(): BlockStmt {
    const start = this.previous();
    const statements: Stmt[] = [];

    while (!this.check('CLOSE_BRACE') && !this.isAtEnd()) {
      statements.push(this.parseStmt());
    }

    this.consume('CLOSE_BRACE', "Expect '}' after block");
    const end = this.previous();
    return new BlockStmt(this.mergeRange(start.range, end.range), statements);
  }

  private parseIfStmt(): IfStmt {
    const start = this.consumeKeyword(Keyword.If, "Expect 'if' keyword");
    this.consume('OPEN_PAREN', "Expect '(' after 'if'");

    const condition = this.parseExpr();

    this.consume('CLOSE_PAREN', "Expect ')' after condition");

    const thenBranch = this.parseStmt();

    let elseBranch: Stmt | undefined;
    if (this.checkKeyword(Keyword.Else)) {
      this.advance();
      elseBranch = this.parseStmt();
    }

    const end = this.previous();
    return new IfStmt(this.mergeRange(start.range, end.range), condition, thenBranch, elseBranch);
  }

  private parseWhileStmt(): WhileStmt {
    const start = this.consumeKeyword(Keyword.While, "Expect 'while' keyword");
    this.consume('OPEN_PAREN', "Expect '(' after 'while'");

    const condition = this.parseExpr();

    this.consume('CLOSE_PAREN', "Expect ')' after condition");

    const body = this.parseStmt();
    const end = this.previous();
    return new WhileStmt(this.mergeRange(start.range, end.range), condition, body);
  }

  private parseReturnStmt(): ReturnStmt {
    const start = this.consumeKeyword(Keyword.Return, "Expect 'return' keyword");

    let value: Expr | undefined;
    if (!this.check('SEMICOLON')) {
      value = this.parseExpr();
    }

    this.consume('SEMICOLON', "Expect ';' after return value");
    const end = this.previous();
    return new ReturnStmt(this.mergeRange(start.range, end.range), value);
  }

  private parseExprStmt(): ExprStmt {
    const expr = this.parseExpr();
    this.consume('SEMICOLON', "Expect ';' after expression");
    return new ExprStmt(expr.range, expr);
  }

  private parseExpr(): Expr {
    return this.parseAssignment();
  }

  private parseAssignment(): Expr {
    const expr = this.parseLogicalOr();

    if (this.matchOperator('=')) {
      const value = this.parseAssignment();
      if (expr instanceof Identifier) {
        return new BinaryExpr(
          this.mergeRange(expr.range, value.range),
          expr,
          BinaryOp.Assign,
          value,
        );
      }
      this.errors.error(
        CompilerStage.Parsing,
        'Invalid assignment target',
        this.previous().range,
      );
    }

    return expr;
  }

  private parseLogicalOr(): Expr {
    let expr = this.parseLogicalAnd();

    while (this.matchOperator('||')) {
      const op = this.previous();
      const right = this.parseLogicalAnd();
      expr = new BinaryExpr(
        this.mergeRange(expr.range, right.range),
        expr,
        BinaryOp.Or,
        right,
      );
    }

    return expr;
  }

  private parseLogicalAnd(): Expr {
    let expr = this.parseEquality();

    while (this.matchOperator('&&')) {
      const op = this.previous();
      const right = this.parseEquality();
      expr = new BinaryExpr(
        this.mergeRange(expr.range, right.range),
        expr,
        BinaryOp.And,
        right,
      );
    }

    return expr;
  }

  private parseEquality(): Expr {
    let expr = this.parseComparison();

    while (this.matchOperator('==') || this.matchOperator('!=')) {
      const op = this.previous();
      const right = this.parseComparison();
      const binOp = BINARY_OPS[op.lexeme]!;
      expr = new BinaryExpr(
        this.mergeRange(expr.range, right.range),
        expr,
        binOp,
        right,
      );
    }

    return expr;
  }

  private parseComparison(): Expr {
    let expr = this.parseTerm();

    while (
      this.matchOperator('<') || this.matchOperator('>') ||
      this.matchOperator('<=') || this.matchOperator('>=')
    ) {
      const op = this.previous();
      const right = this.parseTerm();
      const binOp = BINARY_OPS[op.lexeme]!;
      expr = new BinaryExpr(
        this.mergeRange(expr.range, right.range),
        expr,
        binOp,
        right,
      );
    }

    return expr;
  }

  private parseTerm(): Expr {
    let expr = this.parseFactor();

    while (this.matchOperator('+') || this.matchOperator('-')) {
      const op = this.previous();
      const right = this.parseFactor();
      const binOp = BINARY_OPS[op.lexeme]!;
      expr = new BinaryExpr(
        this.mergeRange(expr.range, right.range),
        expr,
        binOp,
        right,
      );
    }

    return expr;
  }

  private parseFactor(): Expr {
    let expr = this.parseUnary();

    while (this.matchOperator('*') || this.matchOperator('/') || this.matchOperator('%')) {
      const op = this.previous();
      const right = this.parseUnary();
      const binOp = BINARY_OPS[op.lexeme]!;
      expr = new BinaryExpr(
        this.mergeRange(expr.range, right.range),
        expr,
        binOp,
        right,
      );
    }

    return expr;
  }

  private parseUnary(): Expr {
    if (this.matchOperator('-') || this.matchOperator('!')) {
      const opToken = this.previous();
      const op = UNARY_OPS[opToken.lexeme]!;
      const operand = this.parseUnary();
      return new UnaryExpr(
        this.mergeRange(opToken.range, operand.range),
        op,
        operand,
      );
    }

    return this.parseCall();
  }

  private parseCall(): Expr {
    let expr = this.parsePrimary();

    while (true) {
      if (this.match('OPEN_PAREN')) {
        expr = this.finishCall(expr);
      } else {
        break;
      }
    }

    return expr;
  }

  private finishCall(callee: Expr): CallExpr {
    const args: Expr[] = [];

    if (!this.check('CLOSE_PAREN')) {
      do {
        args.push(this.parseExpr());
      } while (this.match('COMMA'));
    }

    const paren = this.consume('CLOSE_PAREN', "Expect ')' after arguments");
    return new CallExpr(
      this.mergeRange(callee.range, paren.range),
      callee,
      args,
    );
  }

  private parsePrimary(): Expr {
    if (this.match('INT_LITERAL')) {
      const token = this.previous();
      return new IntLiteral(token.range, token.literal as number);
    }

    if (this.match('FLOAT_LITERAL')) {
      const token = this.previous();
      return new FloatLiteral(token.range, token.literal as number);
    }

    if (this.match('STRING_LITERAL')) {
      const token = this.previous();
      return new StringLiteral(token.range, token.literal as string);
    }

    if (this.matchKeyword(Keyword.True)) {
      const token = this.previous();
      return new BoolLiteral(token.range, true);
    }

    if (this.matchKeyword(Keyword.False)) {
      const token = this.previous();
      return new BoolLiteral(token.range, false);
    }

    if (this.match('IDENTIFIER')) {
      const token = this.previous();
      return new Identifier(token.range, token.lexeme);
    }

    if (this.match('OPEN_PAREN')) {
      if (this.check('CLOSE_PAREN')) {
        const closeToken = this.advance();
        return new UnitLiteral(this.mergeRange(this.previous().range, closeToken.range));
      }
      const expr = this.parseExpr();
      this.consume('CLOSE_PAREN', "Expect ')' after expression");
      return new GroupExpr(expr.range, expr);
    }

    const token = this.peek();
    this.errors.error(
      CompilerStage.Parsing,
      `Unexpected token '${token.lexeme}'`,
      token.range,
    );

    // Try to recover by advancing
    this.advance();
    return new UnitLiteral(token.range);
  }

  private parseType(): Type {
    const token = this.consume('IDENTIFIER', 'Expect type name');
    switch (token.lexeme) {
      case 'Int': return Type.int();
      case 'Float': return Type.float();
      case 'Bool': return Type.bool();
      case 'String': return Type.string();
      case 'Unit': return Type.unit();
      default:
        this.errors.error(
          CompilerStage.Parsing,
          `Unknown type '${token.lexeme}'`,
          token.range,
          ["Valid types: Int, Float, Bool, String, Unit"],
        );
        return Type.infer();
    }
  }

  // Helpers

  private match(kind: string): boolean {
    if (this.check(kind)) {
      this.advance();
      return true;
    }
    return false;
  }

  private matchOperator(lexeme: string): boolean {
    if (this.peek().kind === 'OPERATOR' && this.peek().lexeme === lexeme) {
      this.advance();
      return true;
    }
    return false;
  }

  private matchKeyword(keyword: Keyword): boolean {
    if (
      this.peek().kind === 'KEYWORD' &&
      this.peek().lexeme === keyword
    ) {
      this.advance();
      return true;
    }
    return false;
  }

  private check(kind: string): boolean {
    if (this.isAtEnd()) return false;
    return this.peek().kind === kind;
  }

  private checkKeyword(keyword: Keyword): boolean {
    if (this.isAtEnd()) return false;
    return this.peek().kind === 'KEYWORD' && this.peek().lexeme === keyword;
  }

  private advance(): Token {
    if (!this.isAtEnd()) this.current++;
    return this.previous();
  }

  private consume(kind: string, message: string): Token {
    if (this.check(kind)) return this.advance();

    const token = this.peek();
    this.errors.error(
      CompilerStage.Parsing,
      message,
      token.range,
    );
    return token;
  }

  private consumeKeyword(keyword: Keyword, message: string): Token {
    if (this.checkKeyword(keyword)) return this.advance();

    const token = this.peek();
    this.errors.error(
      CompilerStage.Parsing,
      message,
      token.range,
    );
    return token;
  }

  private isAtEnd(): boolean {
    return this.peek().kind === 'EOF';
  }

  private peek(): Token {
    return this.tokens[this.current];
  }

  private previous(): Token {
    return this.tokens[this.current - 1];
  }

  private mergeRange(startRange: SourceRange, endRange: SourceRange): SourceRange {
    return {
      start: { ...startRange.start },
      end: { ...endRange.end },
      sourceId: this.sourceId,
    };
  }
}
