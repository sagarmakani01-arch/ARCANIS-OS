import { Lexer } from '../lexer/lexer';
import { Parser } from './parser';
import { ErrorReporter } from '../error';
import { Program, FunctionDecl, VarDecl, BinaryExpr, IntLiteral, Identifier, BlockStmt, ReturnStmt } from './ast';

function parse(source: string, sourceId = 'test.arc'): Program {
  const errors = new ErrorReporter();
  const lexer = new Lexer(source, sourceId, errors);
  const tokens = lexer.tokenize();
  const parser = new Parser(tokens, sourceId, errors);
  const program = parser.parse();
  if (errors.hasErrors()) {
    throw new Error(errors.formatAll());
  }
  return program;
}

describe('Parser', () => {
  it('parses an empty program', () => {
    const program = parse('');
    expect(program.functions).toHaveLength(0);
    expect(program.statements).toHaveLength(0);
  });

  it('parses a function declaration', () => {
    const program = parse('fun main(): Int { return 0; }');
    expect(program.functions).toHaveLength(1);
    const fn = program.functions[0];
    expect(fn.name).toBe('main');
    expect(fn.returnType.toString()).toBe('Int');
    expect(fn.body).toBeInstanceOf(BlockStmt);
  });

  it('parses function with parameters', () => {
    const program = parse('fun add(a: Int, b: Int): Int { return a + b; }');
    expect(program.functions).toHaveLength(1);
    const fn = program.functions[0];
    expect(fn.params).toHaveLength(2);
    expect(fn.params[0].name).toBe('a');
    expect(fn.params[1].name).toBe('b');
  });

  it('parses variable declaration', () => {
    const program = parse('fun main(): Unit { let x: Int = 5; }');
    const stmts = program.functions[0].body.statements;
    const varDecl = stmts[0] as VarDecl;
    expect(varDecl).toBeInstanceOf(VarDecl);
    expect(varDecl.name).toBe('x');
    expect(varDecl.varType.toString()).toBe('Int');
  });

  it('parses variable declaration with type inference', () => {
    const program = parse('fun main(): Unit { let x = 5; }');
    const stmts = program.functions[0].body.statements;
    const varDecl = stmts[0] as VarDecl;
    expect(varDecl.name).toBe('x');
    expect(varDecl.varType.kind).toBe('Infer');
  });

  it('parses binary expressions', () => {
    const program = parse('fun main(): Int { return 2 + 3 * 4; }');
    const stmts = program.functions[0].body.statements;
    const ret = stmts[0] as ReturnStmt;
    const expr = ret.value as BinaryExpr;
    expect(expr).toBeInstanceOf(BinaryExpr);
    expect(expr.op).toBe('+');
  });

  it('parses if statements', () => {
    const program = parse('fun main(): Int { if (true) { return 1; } else { return 2; } }');
    expect(program.functions[0].body.statements[0]).toBeDefined();
  });

  it('parses while statements', () => {
    const program = parse('fun main(): Int { while (x > 0) { x = x - 1; } }');
    expect(program.functions[0].body.statements[0]).toBeDefined();
  });

  it('parses function calls', () => {
    const program = parse('fun main(): Unit { print("hello"); }');
    expect(program.functions[0].body.statements[0]).toBeDefined();
  });

  it('parses standalone expressions at top level', () => {
    const program = parse('print("hello");');
    expect(program.statements).toHaveLength(1);
  });

  it('handles error recovery on unexpected tokens', () => {
    const errors = new ErrorReporter();
    const lexer = new Lexer('fun main() { @ }', 'test.arc', errors);
    const tokens = lexer.tokenize();
    const parser = new Parser(tokens, 'test.arc', errors);
    parser.parse();
    expect(errors.hasErrors()).toBe(true);
  });

  it('parses unit literal as ()', () => {
    const program = parse('fun main(): Unit { return (); }');
    const stmts = program.functions[0].body.statements;
    const ret = stmts[0] as ReturnStmt;
    expect(ret.value).toBeDefined();
  });

  it('parses comparison chains', () => {
    const program = parse('fun main(): Bool { return a < b && c > d; }');
    const stmts = program.functions[0].body.statements;
    const ret = stmts[0] as ReturnStmt;
    expect(ret.value).toBeDefined();
  });
});
