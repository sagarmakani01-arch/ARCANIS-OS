import { Lexer } from '../lexer/lexer';
import { Parser } from '../parser/parser';
import { Optimizer } from './optimizer';
import { ErrorReporter } from '../error';
import { Program, IntLiteral, FloatLiteral, BoolLiteral, BinaryExpr } from '../parser/ast';

function optimize(source: string, sourceId = 'test.arc'): { program: Program; optimizer: Optimizer } {
  const errors = new ErrorReporter();
  const lexer = new Lexer(source, sourceId, errors);
  const tokens = lexer.tokenize();
  const parser = new Parser(tokens, sourceId, errors);
  const program = parser.parse();
  const optimizer = new Optimizer();
  const optimized = optimizer.optimize(program);
  return { program: optimized, optimizer };
}

describe('Optimizer', () => {
  it('folds constant integer addition', () => {
    const { program, optimizer } = optimize('fun main(): Int { return 2 + 3; }');
    expect(optimizer.getChangeCount()).toBeGreaterThan(0);
    const ret = program.functions[0].body.statements[0] as any;
    expect(ret.value).toBeInstanceOf(IntLiteral);
    expect((ret.value as IntLiteral).value).toBe(5);
  });

  it('folds constant boolean comparison', () => {
    const { program, optimizer } = optimize('fun main(): Bool { return 5 == 5; }');
    expect(optimizer.getChangeCount()).toBeGreaterThan(0);
    const ret = program.functions[0].body.statements[0] as any;
    expect(ret.value).toBeInstanceOf(BoolLiteral);
    expect((ret.value as BoolLiteral).value).toBe(true);
  });

  it('folds logical operations', () => {
    const { program, optimizer } = optimize('fun main(): Bool { return true && false; }');
    expect(optimizer.getChangeCount()).toBeGreaterThan(0);
    const ret = program.functions[0].body.statements[0] as any;
    expect(ret.value).toBeInstanceOf(BoolLiteral);
    expect((ret.value as BoolLiteral).value).toBe(false);
  });

  it('folds logical OR', () => {
    const { program, optimizer } = optimize('fun main(): Bool { return true || false; }');
    expect(optimizer.getChangeCount()).toBeGreaterThan(0);
    const ret = program.functions[0].body.statements[0] as any;
    expect((ret.value as BoolLiteral).value).toBe(true);
  });

  it('eliminates while(false)', () => {
    const { program, optimizer } = optimize('fun main(): Unit { while (false) { print("x"); } }');
    expect(optimizer.getChangeCount()).toBeGreaterThan(0);
  });

  it('folds comparison operators', () => {
    const { program, optimizer } = optimize('fun main(): Bool { return 10 > 5; }');
    expect(optimizer.getChangeCount()).toBeGreaterThan(0);
    const ret = program.functions[0].body.statements[0] as any;
    expect((ret.value as BoolLiteral).value).toBe(true);
  });

  it('folds negation', () => {
    const { program, optimizer } = optimize('fun main(): Int { return -(-5); }');
    expect(optimizer.getChangeCount()).toBeGreaterThan(0);
  });

  it('folds float operations', () => {
    const { program, optimizer } = optimize('fun main(): Float { return 1.5 + 2.5; }');
    expect(optimizer.getChangeCount()).toBeGreaterThan(0);
    const ret = program.functions[0].body.statements[0] as any;
    expect(ret.value).toBeInstanceOf(FloatLiteral);
  });

  it('does not change already optimal code', () => {
    const { optimizer } = optimize('fun main(): Int { let x = a + b; return x; }');
    expect(optimizer.getChangeCount()).toBe(0);
  });
});
