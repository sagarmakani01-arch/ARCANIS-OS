import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer.lexer import Lexer, LexerError
from parser.parser import Parser, ParseError
from semantic.analyzer import Analyzer, SemanticError
from interpreter.interpreter import Interpreter, InterpreterError
from compiler.codegen import CodeGenerator, CodeGenError
from compiler.optimizer import Optimizer
from vm.vm import VirtualMachine, VMError


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src <file.arc> [--tokens] [--no-check] [--run] [--compile] [--vm]")
        sys.exit(1)

    path = sys.argv[1]
    show_tokens = "--tokens" in sys.argv
    skip_check = "--no-check" in sys.argv
    run_mode = "--run" in sys.argv
    compile_mode = "--compile" in sys.argv
    vm_mode = "--vm" in sys.argv

    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {path}")
        sys.exit(1)

    try:
        lexer = Lexer(source, filename=path)
        tokens = lexer.tokenize()

        if show_tokens:
            for token in tokens:
                print(token)
            return

        parser = Parser(tokens)
        program = parser.parse()

        if compile_mode:
            codegen = CodeGenerator()
            ir = codegen.compile(program)
            optimizer = Optimizer()
            ir = optimizer.optimize(ir)
            print(f"Compiled {path} successfully.")
            print(f"  Functions: {len([f for f in ir.functions if not f.is_native])}")
            print(f"  Optimization stats: {optimizer.get_stats()}")
            print()
            print("Generated IR:")
            print(ir.to_text())
            return

        if vm_mode:
            codegen = CodeGenerator()
            ir = codegen.compile(program)
            optimizer = Optimizer()
            ir = optimizer.optimize(ir)
            vm = VirtualMachine()
            output = vm.run(ir)
            for line in output:
                print(line)
            return

        if run_mode:
            interpreter = Interpreter()
            interpreter.interpret(program)
            return

        print(f"Parsed {path} successfully.")
        print(f"  Statements: {len(program.statements)}")

        if not skip_check:
            analyzer = Analyzer()
            analyzer.analyze(program)
            print(f"Semantic check passed.")

        for stmt in program.statements:
            print(f"  - {type(stmt).__name__}: ", end="")
            if hasattr(stmt, "name"):
                print(stmt.name)
            elif hasattr(stmt, "expression"):
                print(repr(stmt.expression)[:60])
            else:
                print(type(stmt).__name__)

    except LexerError as e:
        print(f"Lexer error: {e}")
        sys.exit(1)
    except ParseError as e:
        print(f"Parser error: {e}")
        sys.exit(1)
    except SemanticError as e:
        print(f"Semantic error: {e}")
        sys.exit(1)
    except InterpreterError as e:
        print(f"Runtime error: {e}")
        sys.exit(1)
    except CodeGenError as e:
        print(f"Compilation error: {e}")
        sys.exit(1)
    except VMError as e:
        print(f"VM error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
