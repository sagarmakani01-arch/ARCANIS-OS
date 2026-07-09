import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer.lexer import Lexer, LexerError
from parser.parser import Parser, ParseError
from parser.ast import *
from semantic.analyzer import Analyzer, SemanticError
from semantic.types import *
from semantic.symbol_table import SymbolTable, SymbolKind


def analyze(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    analyzer = Analyzer()
    analyzer.analyze(program)
    return analyzer


def test_empty():
    a = analyze("")
    assert len(a.symbols.scopes) == 1
    assert len(a.errors) == 0


def test_let_integer():
    a = analyze("let x = 42")
    sym = a.symbols.resolve("x")
    assert sym is not None
    assert sym.kind == SymbolKind.VARIABLE
    assert sym.type == I32


def test_let_string():
    a = analyze('let name = "hello"')
    sym = a.symbols.resolve("name")
    assert sym.type == STRING


def test_let_bool():
    a = analyze("let flag = true")
    sym = a.symbols.resolve("flag")
    assert sym.type == BOOL


def test_let_float():
    a = analyze("let pi = 3.14")
    sym = a.symbols.resolve("pi")
    assert sym.type == F64


def test_let_nil():
    a = analyze("let nothing = nil")
    sym = a.symbols.resolve("nothing")
    assert sym.type == NULL


def test_let_with_type_annotation():
    a = analyze("let x: i64 = 42")
    sym = a.symbols.resolve("x")
    assert sym.type == I64


def test_let_mutable():
    a = analyze("let mut x = 10; x = 20")
    sym = a.symbols.resolve("x")
    assert sym.mutable is True


def test_const():
    a = analyze("const PI: f64 = 3.14159")
    sym = a.symbols.resolve("PI")
    assert sym.type == F64


def test_variable_scope():
    a = analyze("""
let x = 10
fn test():
    let y = 20
""")
    assert a.symbols.resolve("x") is not None
    assert a.symbols.resolve("y") is None


def test_undefined_variable():
    caught = False
    try:
        analyze("let x = unknown_var")
    except SemanticError as e:
        caught = True
        assert "Undefined" in str(e)
    assert caught


def test_binary_arithmetic():
    a = analyze("let x = 10 + 20")
    sym = a.symbols.resolve("x")
    assert sym.type == I32


def test_binary_comparison():
    a = analyze("let x = 10 == 20")
    sym = a.symbols.resolve("x")
    assert sym.type == BOOL


def test_binary_string_concat():
    a = analyze('let x = "hello" ++ " world"')
    sym = a.symbols.resolve("x")
    assert sym.type == STRING


def test_unary_negation():
    a = analyze("let x = -42")
    sym = a.symbols.resolve("x")
    assert sym.type == I32


def test_unary_not():
    a = analyze("let x = !true")
    sym = a.symbols.resolve("x")
    assert sym.type == BOOL


def test_fn_declaration():
    a = analyze("""
fn add(a: i32, b: i32) -> i32:
    a + b
""")
    sym = a.symbols.resolve("add")
    assert sym is not None
    assert sym.kind == SymbolKind.FUNCTION
    assert isinstance(sym.type, FunctionType)
    assert len(sym.type.params) == 2
    assert sym.type.params[0] == I32
    assert sym.type.params[1] == I32
    assert sym.type.return_type == I32


def test_fn_no_params():
    a = analyze('fn greet() { println("hi") }')
    sym = a.symbols.resolve("greet")
    assert isinstance(sym.type, FunctionType)
    assert len(sym.type.params) == 0


def test_fn_return_type_inference():
    a = analyze("fn five() -> i32 { 5 }")
    sym = a.symbols.resolve("five")
    assert sym.type.return_type == I32


def test_list():
    a = analyze("let items = [1, 2, 3]")
    sym = a.symbols.resolve("items")
    assert isinstance(sym.type, ArrayType)
    assert sym.type.element_type == I32


def test_struct_declaration():
    a = analyze("""
struct Point:
    x: i32
    y: i32
""")
    sym = a.symbols.resolve("Point")
    assert sym is not None
    assert sym.kind == SymbolKind.TYPE


def test_builtin_print():
    a = analyze('println("hello")')
    assert len(a.errors) == 0


def test_builtin_int():
    a = analyze("let x = int(3.14)")
    sym = a.symbols.resolve("x")
    assert sym.type == I32


def test_nested_function_scopes():
    source = """
let a = 1
fn outer():
    let b = 2
    fn inner():
        let c = 3
"""
    a = analyze(source)
    assert a.symbols.resolve("a") is not None
    assert a.symbols.resolve("b") is None
    assert a.symbols.resolve("c") is None


def test_for_loop():
    source = """
for i in [1, 2, 3]:
    let x = i
"""
    a = analyze(source)
    assert len(a.errors) == 0


def test_while_loop():
    source = """
let mut x = 0
while x < 10:
    x = x + 1
"""
    a = analyze(source)
    assert a.symbols.resolve("x") is not None


def test_pi_constant():
    a = analyze("let x = pi")
    sym = a.symbols.resolve("x")
    assert sym.type == F64


def test_multiple_functions():
    source = """
fn foo() -> i32 { 10 }
fn bar() -> i32 { foo() }
"""
    a = analyze(source)
    assert a.symbols.resolve("bar") is not None


def test_all_builtins():
    source = """
print(1)
println("hello")
int(3.14)
float(42)
str(123)
cosine_similarity(nil, nil)
semantic_search("q", ["a"], 5)
token_count("hello")
read_line()
read_file("test.txt")
write_file("test.txt", "data")
"""
    a = analyze(source)
    assert len(a.errors) == 0


def test_assign_to_immutable():
    caught = False
    try:
        analyze("let x = 10; x = 20")
    except SemanticError as e:
        caught = True
        assert "assign" in str(e).lower() or "immutable" in str(e).lower()
    assert caught, "Should have raised SemanticError for assign to immutable"
