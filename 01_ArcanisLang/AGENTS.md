# ArcanisLang Agent Guide

## Build/Test/Lint Commands
- Run all tests: `python -m tests.run_tests`
- Run single test: `python -m tests.test_lexer`
- Run file: `python -m src.cli <file.arc>`
- Start REPL: `python -m src.cli`

## Code Style
- Keep syntax simple and human-readable
- Indentation-based blocks (4 spaces)
- Dynamic typing
- Use `fun` keyword for function definitions
- Use `class` keyword for classes
- Error messages should be clear and helpful

## Architecture
- `src/lexer.py` - Tokenizes source code
- `src/parser.py` - Recursive descent parser producing AST
- `src/semantic.py` - Semantic analysis (scope, type checking)
- `src/interpreter.py` - Tree-walking interpreter
- `src/builtins.py` - Built-in functions and standard environment
- `src/cli.py` - Command-line interface and REPL
