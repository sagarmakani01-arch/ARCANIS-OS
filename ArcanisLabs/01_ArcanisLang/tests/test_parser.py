import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer.token import Token, TokenType
from lexer.lexer import Lexer
from parser.ast import *
from parser.parser import Parser, ParseError


def parse(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def test_empty():
    prog = parse("")
    assert len(prog.statements) == 0


def test_literal_integer():
    prog = parse("42")
    assert isinstance(prog.statements[0], ExpressionStmt)
    assert isinstance(prog.statements[0].expression, LiteralExpr)
    assert prog.statements[0].expression.value == 42


def test_literal_float():
    prog = parse("3.14")
    assert prog.statements[0].expression.value == 3.14


def test_literal_string():
    prog = parse('"hello"')
    assert prog.statements[0].expression.value == "hello"


def test_literal_bool():
    prog = parse("true")
    assert prog.statements[0].expression.value is True
    prog = parse("false")
    assert prog.statements[0].expression.value is False


def test_literal_nil():
    prog = parse("nil")
    assert prog.statements[0].expression.value is None


def test_identifier():
    prog = parse("my_var")
    assert isinstance(prog.statements[0].expression, IdentifierExpr)
    assert prog.statements[0].expression.name == "my_var"


def test_binary_op():
    prog = parse("1 + 2")
    expr = prog.statements[0].expression
    assert isinstance(expr, BinaryExpr)
    assert expr.op == "+"
    assert expr.left.value == 1
    assert expr.right.value == 2


def test_precedence():
    prog = parse("1 + 2 * 3")
    expr = prog.statements[0].expression
    assert isinstance(expr, BinaryExpr)
    assert expr.op == "+"
    assert expr.right.op == "*"


def test_parentheses():
    prog = parse("(1 + 2) * 3")
    expr = prog.statements[0].expression
    assert isinstance(expr, BinaryExpr)
    assert expr.op == "*"
    assert isinstance(expr.left, BinaryExpr)


def test_unary_minus():
    prog = parse("-42")
    expr = prog.statements[0].expression
    assert isinstance(expr, UnaryExpr)
    assert expr.op == "-"


def test_unary_not():
    prog = parse("!true")
    expr = prog.statements[0].expression
    assert isinstance(expr, UnaryExpr)
    assert expr.op == "!"


def test_comparison():
    prog = parse("1 == 2")
    assert prog.statements[0].expression.op == "=="
    prog = parse("1 != 2")
    assert prog.statements[0].expression.op == "!="
    prog = parse("1 < 2")
    assert prog.statements[0].expression.op == "<"
    prog = parse("1 > 2")
    assert prog.statements[0].expression.op == ">"


def test_logical():
    prog = parse("true and false")
    assert prog.statements[0].expression.op == "and"
    prog = parse("true or false")
    assert prog.statements[0].expression.op == "or"


def test_function_call():
    prog = parse("print(42)")
    expr = prog.statements[0].expression
    assert isinstance(expr, CallExpr)
    assert isinstance(expr.callee, IdentifierExpr)
    assert expr.callee.name == "print"
    assert len(expr.args) == 1


def test_function_call_multiple_args():
    prog = parse("add(1, 2, 3)")
    assert len(prog.statements[0].expression.args) == 3


def test_let_declaration():
    prog = parse("let x = 42")
    stmt = prog.statements[0]
    assert isinstance(stmt, LetStmt)
    assert stmt.name == "x"
    assert stmt.mutable is False
    assert stmt.value.value == 42


def test_let_mutable():
    prog = parse("let mut x = 42")
    assert prog.statements[0].mutable is True


def test_let_typed():
    prog = parse('let x: String = "hello"')
    stmt = prog.statements[0]
    assert stmt.type_annotation.name == "String"


def test_const():
    prog = parse("const MAX: i32 = 1024")
    stmt = prog.statements[0]
    assert isinstance(stmt, ConstStmt)
    assert stmt.name == "MAX"
    assert stmt.type_annotation.name == "i32"


def test_fn_declaration():
    source = """fn add(a: i32, b: i32) -> i32:
    a + b
"""
    prog = parse(source)
    stmt = prog.statements[0]
    assert isinstance(stmt, FnDecl)
    assert stmt.name == "add"
    assert len(stmt.params) == 2
    assert stmt.return_type.name == "i32"


def test_return_statement():
    source = """fn foo():
    return 42
"""
    prog = parse(source)
    fn_decl = prog.statements[0]
    ret = fn_decl.body.statements[0]
    assert isinstance(ret, ReturnStmt)
    assert ret.value.value == 42


def test_if_expression():
    source = """if true: 1 else: 2
"""
    prog = parse(source)
    expr = prog.statements[0].expression
    assert isinstance(expr, IfExpr)
    assert expr.condition.value is True
    assert expr.then_branch.statements[0].expression.value == 1
    assert expr.else_branch.statements[0].expression.value == 2


def test_match_expression():
    source = """match x:
    1 => "one"
    2 => "two"
    _ => "other"
"""
    prog = parse(source)
    expr = prog.statements[0].expression
    assert isinstance(expr, MatchExpr)
    assert len(expr.arms) == 3


def test_for_loop():
    source = """for i in 0..10:
    print(i)
"""
    prog = parse(source)
    stmt = prog.statements[0]
    assert isinstance(stmt, ForStmt)


def test_while_loop():
    source = """while x < 10:
    x += 1
"""
    prog = parse(source)
    stmt = prog.statements[0]
    assert isinstance(stmt, WhileStmt)


def test_struct_declaration():
    source = """struct Point:
    x: f64
    y: f64
"""
    prog = parse(source)
    stmt = prog.statements[0]
    assert isinstance(stmt, StructDecl)
    assert stmt.name == "Point"
    assert len(stmt.fields) == 2


def test_enum_declaration():
    source = """enum Status:
    Active
    Inactive
    Paused(String)
"""
    prog = parse(source)
    stmt = prog.statements[0]
    assert isinstance(stmt, EnumDecl)
    assert len(stmt.variants) == 3


def test_agent_declaration():
    source = """agent Assistant:
    role: "helper"
    model: "gpt-4"
"""
    prog = parse(source)
    stmt = prog.statements[0]
    assert isinstance(stmt, AgentDecl)
    assert stmt.name == "Assistant"
    assert stmt.role.value == "helper"


def test_ai_expression():
    source = 'ai prompt("hello")'
    prog = parse(source)
    expr = prog.statements[0].expression
    assert isinstance(expr, AIExpr)
    assert expr.prompt.expression.value == "hello"


def test_ai_with_model():
    source = 'ai prompt("hello") model("gpt-4")'
    prog = parse(source)
    expr = prog.statements[0].expression
    assert isinstance(expr, AIExpr)
    assert expr.model.expression.value == "gpt-4"


def test_embed():
    prog = parse('embed("text")')
    expr = prog.statements[0].expression
    assert isinstance(expr, EmbedExpr)
    assert expr.expression.value == "text"


def test_range_operator():
    prog = parse("1..10")
    expr = prog.statements[0].expression
    assert isinstance(expr, RangeExpr)
    assert expr.start.value == 1
    assert expr.end.value == 10


def test_import_stmt():
    prog = parse('import "std/io"')
    stmt = prog.statements[0]
    assert isinstance(stmt, ImportStmt)
    assert stmt.path == "std/io"


def test_async_await():
    source = """async fn fetch():
    await result
"""
    prog = parse(source)


def test_try_expr():
    prog = parse("try risky()")
    expr = prog.statements[0].expression
    assert isinstance(expr, TryExpr)


def test_nested_indentation():
    source = """if true:
    if false:
        let x = 1
    let y = 2
"""
    prog = parse(source)
    outer_if = prog.statements[0].expression
    assert isinstance(outer_if, IfExpr)
    inner_if = outer_if.then_branch.statements[0].expression
    assert isinstance(inner_if, IfExpr)
    assert len(outer_if.then_branch.statements) == 2


def test_attribute_access():
    prog = parse("obj.field")
    expr = prog.statements[0].expression
    assert isinstance(expr, AttributeExpr)
    assert expr.attr == "field"


def test_index_access():
    prog = parse("arr[0]")
    expr = prog.statements[0].expression
    assert isinstance(expr, IndexExpr)


def test_block_string():
    prog = parse('"""hello"""')
    assert prog.statements[0].expression.value == "hello"


def test_throw():
    source = 'throw "error"'
    prog = parse(source)
    assert isinstance(prog.statements[0], ThrowStmt)


def test_defer():
    source = "defer file.close()"
    prog = parse(source)
    assert isinstance(prog.statements[0], DeferStmt)


def test_import_with_names():
    source = 'import "std/collections" { List, Map }'
    prog = parse(source)
    stmt = prog.statements[0]
    assert stmt.names == ["List", "Map"]


def test_range_expr():
    prog = parse("0..=10")
    expr = prog.statements[0].expression
    assert isinstance(expr, RangeExpr)
    assert expr.inclusive is True


def test_attribute_chain():
    prog = parse("a.b.c")
    expr = prog.statements[0].expression
    assert isinstance(expr, AttributeExpr)
    assert isinstance(expr.target, AttributeExpr)
    assert expr.target.attr == "b"
    assert expr.attr == "c"


def test_pub_fn():
    source = """pub fn hello():
    print("hi")
"""
    prog = parse(source)
    assert prog.statements[0].pub is True


def test_trait():
    source = """trait Drawable:
    fn draw(self)
    fn area(self) -> f64
"""
    prog = parse(source)
    assert isinstance(prog.statements[0], TraitDecl)


def test_impl():
    source = """impl Drawable for Circle:
    fn draw(self):
        pass
"""
    prog = parse(source)
    assert isinstance(prog.statements[0], ImplDecl)


if __name__ == "__main__":
    test_empty()
    test_literal_integer()
    test_literal_float()
    test_literal_string()
    test_literal_bool()
    test_literal_nil()
    test_identifier()
    test_binary_op()
    test_precedence()
    test_parentheses()
    test_unary_minus()
    test_unary_not()
    test_comparison()
    test_logical()
    test_function_call()
    test_function_call_multiple_args()
    test_let_declaration()
    test_let_mutable()
    test_let_typed()
    test_const()
    test_fn_declaration()
    test_return_statement()
    test_if_expression()
    test_match_expression()
    test_for_loop()
    test_while_loop()
    test_struct_declaration()
    test_enum_declaration()
    test_agent_declaration()
    test_ai_expression()
    test_ai_with_model()
    test_embed()
    test_range_operator()
    test_import_stmt()
    test_async_await()
    test_try_expr()
    test_nested_indentation()
    test_attribute_access()
    test_index_access()
    test_block_string()
    test_throw()
    test_defer()
    test_import_with_names()
    test_range_expr()
    test_attribute_chain()
    test_pub_fn()
    test_trait()
    test_impl()
    print("All parser tests passed!")
