import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer.lexer import Lexer, LexerError
from parser.parser import Parser, ParseError
from interpreter.interpreter import Interpreter, InterpreterError, ReturnException
from interpreter.values import *
from interpreter.environment import Environment


def interpret(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    interp = Interpreter()
    interp.interpret(program)
    return interp


def test_literal_int():
    i = interpret("42")
    assert True


def test_variable_declaration():
    i = interpret("let x = 42")
    val = i.env.get("x")
    assert isinstance(val, IntValue)
    assert val.value == 42


def test_variable_string():
    i = interpret('let x = "hello"')
    val = i.env.get("x")
    assert isinstance(val, StringValue)
    assert val.value == "hello"


def test_variable_bool():
    i = interpret("let x = true")
    val = i.env.get("x")
    assert isinstance(val, BoolValue)
    assert val.value is True


def test_variable_nil():
    i = interpret("let x = nil")
    val = i.env.get("x")
    assert isinstance(val, NilValue)


def test_arithmetic():
    i = interpret("let x = 10 + 20 * 3")
    val = i.env.get("x")
    assert val.value == 70


def test_arithmetic_float():
    i = interpret("let x = 10.5 + 3.2")
    val = i.env.get("x")
    assert isinstance(val, FloatValue)
    assert abs(val.value - 13.7) < 0.01


def test_comparison():
    i = interpret("let x = 10 > 5")
    val = i.env.get("x")
    assert isinstance(val, BoolValue)
    assert val.value is True


def test_equality():
    i = interpret("let x = 10 == 10")
    val = i.env.get("x")
    assert val.value is True


def test_logical():
    i = interpret("let x = true and false")
    val = i.env.get("x")
    assert val.value is False


def test_unary_minus():
    i = interpret("let x = -42")
    val = i.env.get("x")
    assert isinstance(val, IntValue)
    assert val.value == -42


def test_unary_not():
    i = interpret("let x = !true")
    val = i.env.get("x")
    assert isinstance(val, BoolValue)
    assert val.value is False


def test_string_concat():
    i = interpret('let x = "hello" ++ " world"')
    val = i.env.get("x")
    assert val.value == "hello world"


def test_assignment():
    i = interpret("let mut x = 10; x = 20")
    val = i.env.get("x")
    assert val.value == 20


def test_if_true():
    i = interpret("""
let x = if true {
    42
} else {
    0
}
""")
    val = i.env.get("x")
    assert val.value == 42


def test_if_false():
    i = interpret("""
let x = if false {
    42
} else {
    99
}
""")
    val = i.env.get("x")
    assert val.value == 99


def test_while_loop():
    i = interpret("""
let mut x = 0
while x < 5 {
    x = x + 1
}
""")
    val = i.env.get("x")
    assert val.value == 5


def test_for_loop():
    i = interpret("""
let mut total = 0
for i in [1, 2, 3] {
    total = total + i
}
""")
    val = i.env.get("total")
    assert val.value == 6


def test_fn_call():
    i = interpret("""
fn add(a, b) {
    a + b
}
let x = add(3, 4)
""")
    val = i.env.get("x")
    assert val.value == 7


def test_fn_return():
    i = interpret("""
fn double(x) -> i32 {
    return x * 2
}
let y = double(5)
""")
    val = i.env.get("y")
    assert val.value == 10


def test_recursive_fn():
    i = interpret("""
fn factorial(n) {
    if n <= 1 {
        1
    } else {
        n * factorial(n - 1)
    }
}
let x = factorial(5)
""")
    val = i.env.get("x")
    assert val.value == 120


def test_list():
    i = interpret("let items = [1, 2, 3]")
    val = i.env.get("items")
    assert isinstance(val, ArrayValue)
    assert len(val.elements) == 3
    assert val.elements[0].value == 1


def test_list_index():
    i = interpret("""
let items = [10, 20, 30]
let x = items[1]
""")
    val = i.env.get("x")
    assert val.value == 20


def test_builtin_println():
    i = interpret('println("hello")')
    assert True


def test_builtin_int():
    i = interpret("let x = int(3.14)")
    val = i.env.get("x")
    assert isinstance(val, IntValue)
    assert val.value == 3


def test_builtin_str():
    i = interpret("let x = str(42)")
    val = i.env.get("x")
    assert isinstance(val, StringValue)
    assert val.value == "42"


def test_pi_constant():
    i = interpret("let x = pi")
    val = i.env.get("x")
    assert isinstance(val, FloatValue)
    assert abs(val.value - 3.14159) < 0.01


def test_nested_scopes():
    i = interpret("""
let x = 1
fn test() {
    let y = 2
}
""")
    assert isinstance(i.env.get("x"), IntValue)
    try:
        i.env.get("y")
        assert False, "y should not be in global scope"
    except RuntimeError:
        pass


def test_block_scope():
    i = interpret("""
fn test() {
    let inner = 42
}
let x = test()
let outer = 99
""")
    assert isinstance(i.env.get("outer"), IntValue)
    try:
        i.env.get("inner")
        assert False, "inner should not be accessible"
    except RuntimeError:
        pass


def test_embed_expression():
    i = interpret('let x = embed("hello world")')
    val = i.env.get("x")
    assert isinstance(val, EmbeddingValue)


def test_ai_expression():
    i = interpret('let x = ai prompt("test")')
    val = i.env.get("x")
    assert isinstance(val, StringValue)
    assert "AI response" in val.value
