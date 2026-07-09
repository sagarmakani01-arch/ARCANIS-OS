from .lexer import Lexer
from .parser import Parser
from .ast import Program
from .semantic import SemanticAnalyzer
from .interpreter import Interpreter
from .builtins import STANDARD_ENV
from .errors import LexerError, ParserError, SemanticError, RuntimeError_

def run_source(source, filename="<stdin>"):
    lexer = Lexer(source, filename)
    parser = Parser(lexer.tokens, filename)
    ast = parser.parse()
    analyzer = SemanticAnalyzer()
    analyzer.visit(ast)
    interpreter = Interpreter(STANDARD_ENV)
    return interpreter.visit(ast)

def run_file(path):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return run_source(source, path)
