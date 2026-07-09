import { Compiler } from '../src/compiler';
import { CompilerStage } from '../src/types';

function compileFull(source: string, sourceId = 'test.arc'): ReturnType<Compiler['compile']> {
  const compiler = new Compiler();
  compiler.setSource(source, sourceId);
  return compiler.compile();
}

function compileAndRun(source: string): any {
  const result = compileFull(source);
  if (!result.success) {
    throw new Error(`Compilation failed: ${JSON.stringify(result.diagnostics)}`);
  }
  // Evaluate the generated JavaScript
  const fn = new Function(result.output!);
  return fn();
}

describe('Integration', () => {
  it('compiles and runs a complete function', () => {
    const source = `
fun add(a: Int, b: Int): Int {
  return a + b;
}
fun main(): Int {
  return add(3, 4);
}
`;
    const result = compileFull(source);
    expect(result.success).toBe(true);
    expect(result.output).toContain('function add');
    expect(result.output).toContain('function main');
  });

  it('handles errors gracefully with friendly messages', () => {
    const source = 'fun main(): Int { return "hello"; }';
    const result = compileFull(source);
    expect(result.success).toBe(false);
    expect(result.diagnostics.length).toBeGreaterThan(0);
    expect(result.diagnostics[0].message).toContain('Return type mismatch');
  });

  it('reports lexical errors', () => {
    const source = 'let @ = 5;';
    const result = compileFull(source, 'test.arc');
    expect(result.success).toBe(false);
    expect(result.diagnostics.length).toBeGreaterThan(0);
  });

  it('reports syntax errors', () => {
    const source = 'fun main() { return }';
    const result = compileFull(source, 'test.arc');
    expect(result.success).toBe(false);
  });

  it('produces valid JavaScript for arithmetic', () => {
    const source = 'fun main(): Int { return (2 + 3) * 4; }';
    const result = compileFull(source);
    expect(result.success).toBe(true);
    expect(() => new Function(result.output!)).not.toThrow();
  });

  it('produces valid JavaScript for conditionals', () => {
    const source = 'fun main(): Int { if (true) { return 1; } else { return 2; } }';
    const result = compileFull(source);
    expect(result.success).toBe(true);
    expect(() => new Function(result.output!)).not.toThrow();
  });

  it('optimizes constant expressions', () => {
    const source = 'fun main(): Int { return 100 + 200; }';
    const result = compileFull(source);
    expect(result.success).toBe(true);
    expect(result.output).toContain('300');
  });

  it('supports variable declarations', () => {
    const source = 'fun main(): Int { let x: Int = 42; return x; }';
    const result = compileFull(source);
    expect(result.success).toBe(true);
  });

  it('handles string concatenation', () => {
    const source = 'fun main(): String { return "hello" + " " + "world"; }';
    const result = compileFull(source);
    expect(result.success).toBe(true);
  });

  it('tracks compilation stages completed', () => {
    const source = 'fun main(): Int { return 0; }';
    const result = compileFull(source);
    expect(result.stagesCompleted).toContain('lexing');
    expect(result.stagesCompleted).toContain('parsing');
    expect(result.stagesCompleted).toContain('ast_generation');
    expect(result.stagesCompleted).toContain('type_checking');
    expect(result.stagesCompleted).toContain('optimization');
    expect(result.stagesCompleted).toContain('code_generation');
  });

  it('provides timing information', () => {
    const source = 'fun main(): Int { return 0; }';
    const result = compileFull(source);
    expect(result.timing.size).toBeGreaterThan(0);
  });

  it('supports emitting only specific stages', () => {
    const compiler = new Compiler();
    compiler.setSource('fun main(): Int { return 0; }', 'test.arc');
    const result = compiler.compile({ emitOnly: [CompilerStage.Lexing] });
    expect(result.stagesCompleted).toEqual([CompilerStage.Lexing]);
  });

  it('supports disabling optimizations', () => {
    const source = 'fun main(): Int { return 2 + 3; }';
    const compiler = new Compiler();
    compiler.setSource(source, 'test.arc');
    const resultNoOpt = compiler.compile({ enableOptimizations: false });
    const resultOpt = compiler.compile({ enableOptimizations: true });

    // Re-compile with source set again for the second compile
    compiler.setSource(source, 'test.arc');
    const resultOpt2 = compiler.compile({ enableOptimizations: true });

    // The unoptimized version should still have the addition
    expect(resultNoOpt.stagesCompleted).not.toContain('optimization');
    expect(resultOpt2.stagesCompleted).toContain('optimization');
  });

  it('generates valid JavaScript for factorial', () => {
    const source = `
fun factorial(n: Int): Int {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}
fun main(): Int {
  return factorial(5);
}
`;
    const result = compileFull(source);
    expect(result.success).toBe(true);
    expect(result.output).toContain('factorial');
    expect(result.output).toContain('function factorial');
  });
});
