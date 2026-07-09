import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer.token import Token, TokenType
from lexer.lexer import Lexer, LexerError


def tokenize(source):
    lexer = Lexer(source)
    return lexer.tokenize()


def test_empty_source():
    tokens = tokenize("")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF


def test_simple_hello():
    tokens = tokenize('print("Hello")')
    types = [t.type for t in tokens]
    assert TokenType.IDENTIFIER in types
    assert TokenType.STRING in types
    assert TokenType.LPAREN in types
    assert TokenType.RPAREN in types
    assert TokenType.EOF in types


def test_keywords():
    tokens = tokenize("let x = 42")
    types = [t.type for t in tokens]
    assert TokenType.LET in types
    assert TokenType.IDENTIFIER in types
    assert TokenType.EQ in types
    assert TokenType.INTEGER in types


def test_integer_literal():
    tokens = tokenize("42")
    assert tokens[0].type == TokenType.INTEGER
    assert tokens[0].value == "42"


def test_float_literal():
    tokens = tokenize("3.14")
    assert tokens[0].type == TokenType.FLOAT
    assert tokens[0].value == "3.14"


def test_hex_literal():
    tokens = tokenize("0xFF")
    assert tokens[0].type == TokenType.INTEGER
    assert tokens[0].value == "0xFF"


def test_binary_literal():
    tokens = tokenize("0b1010")
    assert tokens[0].type == TokenType.INTEGER
    assert tokens[0].value == "0b1010"


def test_underscore_number():
    tokens = tokenize("1_000_000")
    assert tokens[0].type == TokenType.INTEGER
    assert tokens[0].value == "1_000_000"


def test_string_literal():
    tokens = tokenize('"hello"')
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello"


def test_block_string():
    tokens = tokenize('"""multi\nline"""')
    assert tokens[0].type == TokenType.STRING_BLOCK


def test_line_comment():
    tokens = tokenize("# this is a comment\n42")
    types = [t.type for t in tokens]
    assert TokenType.INTEGER in types
    assert TokenType.IDENTIFIER not in types


def test_operators():
    ops = [
        ("+", TokenType.PLUS), ("-", TokenType.MINUS),
        ("*", TokenType.STAR), ("/", TokenType.SLASH),
        ("%", TokenType.PERCENT), ("=", TokenType.EQ),
        ("==", TokenType.EQ_EQ), ("!=", TokenType.BANG_EQ),
        ("<", TokenType.LT), (">", TokenType.GT),
        ("<=", TokenType.LT_EQ), (">=", TokenType.GT_EQ),
        ("->", TokenType.ARROW), ("=>", TokenType.FAT_ARROW),
        ("..", TokenType.DOTDOT), ("..=", TokenType.DOTDOT_EQ),
        ("+=", TokenType.PLUS_EQ), ("-=", TokenType.MINUS_EQ),
        ("*=", TokenType.STAR_EQ), ("/=", TokenType.SLASH_EQ),
        ("??", TokenType.QUESTION_QUESTION), ("++", TokenType.PLUS_PLUS),
        ("!", TokenType.BANG), ("?", TokenType.QUESTION),
        ("|", TokenType.PIPE), ("&", TokenType.AMPERSAND),
    ]
    for op_str, expected in ops:
        tokens = tokenize(op_str)
        assert tokens[0].type == expected, f"Failed for {op_str!r}: got {tokens[0].type}"


def test_punctuation():
    punct = [
        ("(", TokenType.LPAREN), (")", TokenType.RPAREN),
        ("[", TokenType.LBRACKET), ("]", TokenType.RBRACKET),
        ("{", TokenType.LBRACE), ("}", TokenType.RBRACE),
        (",", TokenType.COMMA), (".", TokenType.DOT),
        (":", TokenType.COLON), (";", TokenType.SEMICOLON),
        ("_", TokenType.UNDERSCORE),
    ]
    for p_str, expected in punct:
        tokens = tokenize(p_str)
        assert tokens[0].type == expected, f"Failed for {p_str!r}: got {tokens[0].type}"


def test_all_keywords():
    tests = [
        ("let", TokenType.LET), ("const", TokenType.CONST),
        ("fn", TokenType.FN), ("if", TokenType.IF),
        ("else", TokenType.ELSE), ("for", TokenType.FOR),
        ("while", TokenType.WHILE), ("return", TokenType.RETURN),
        ("true", TokenType.TRUE), ("false", TokenType.FALSE),
        ("nil", TokenType.NIL), ("import", TokenType.IMPORT),
        ("struct", TokenType.STRUCT), ("enum", TokenType.ENUM),
        ("trait", TokenType.TRAIT), ("impl", TokenType.IMPL),
        ("match", TokenType.MATCH), ("pub", TokenType.PUB),
        ("mut", TokenType.MUT), ("async", TokenType.ASYNC),
        ("await", TokenType.AWAIT), ("try", TokenType.TRY),
        ("throw", TokenType.THROW), ("ai", TokenType.AI),
        ("prompt", TokenType.PROMPT), ("embed", TokenType.EMBED),
        ("model", TokenType.MODEL), ("agent", TokenType.AGENT),
        ("memory", TokenType.MEMORY), ("and", TokenType.AND),
        ("or", TokenType.OR), ("self", TokenType.SELF),
    ]
    for word, expected in tests:
        tokens = tokenize(word)
        assert tokens[0].type == expected, f"Failed for keyword {word!r}: got {tokens[0].type}"


def test_indentation():
    source = """fn foo():
    let x = 1
    let y = 2
"""
    tokens = tokenize(source)
    types = [t.type for t in tokens]
    assert TokenType.INDENT in types, "Should have INDENT"
    assert TokenType.DEDENT in types, "Should have DEDENT"


def test_nested_indentation():
    source = """if true:
    if false:
        let x = 1
    let y = 2
"""
    tokens = tokenize(source)
    types = [t.type for t in tokens]
    indent_count = types.count(TokenType.INDENT)
    dedent_count = types.count(TokenType.DEDENT)
    assert indent_count == 2, f"Should have 2 INDENTs, got {indent_count}"
    assert dedent_count == 2, f"Should have 2 DEDENTs, got {dedent_count}"


def test_function_declaration():
    source = """fn greet(name: String) -> String:
    return "Hello, {name}!"
"""
    tokens = tokenize(source)
    types = [t.type for t in tokens]
    assert TokenType.FN in types
    assert TokenType.COLON in types
    assert TokenType.ARROW in types
    assert TokenType.STRING in types


def test_ai_prompt():
    source = 'let answer = ai prompt("What is 2+2?")'
    tokens = tokenize(source)
    types = [t.type for t in tokens]
    assert TokenType.LET in types
    assert TokenType.AI in types
    assert TokenType.PROMPT in types
    assert TokenType.STRING in types


def test_agent_definition():
    source = """agent Assistant:
    role: "Helper"
    model: "gpt-4"
"""
    tokens = tokenize(source)
    types = [t.type for t in tokens]
    assert TokenType.AGENT in types
    assert TokenType.ROLE in types
    assert TokenType.MODEL in types


def test_scientific_notation():
    tokens = tokenize("1.5e10")
    assert tokens[0].type == TokenType.FLOAT


def test_identifier_with_underscore():
    tokens = tokenize("my_var_123")
    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].value == "my_var_123"


def test_invalid_character():
    try:
        tokenize("let x = `invalid`")
        assert False, "Should have raised error"
    except LexerError:
        pass


def test_unterminated_string():
    try:
        tokenize('"hello')
        assert False, "Should have raised error"
    except LexerError:
        pass


def test_multiple_statements():
    source = """let x = 10
let y = 20
let z = x + y
"""
    tokens = tokenize(source)
    types = [t.type for t in tokens]
    assert types.count(TokenType.LET) == 3


def test_match_expression():
    source = """match value:
    1 => "one"
    2 => "two"
    _ => "other"
"""
    tokens = tokenize(source)
    types = [t.type for t in tokens]
    assert TokenType.MATCH in types
    assert TokenType.FAT_ARROW in types
    assert TokenType.UNDERSCORE in types


if __name__ == "__main__":
    test_empty_source()
    test_simple_hello()
    test_keywords()
    test_integer_literal()
    test_float_literal()
    test_hex_literal()
    test_binary_literal()
    test_underscore_number()
    test_string_literal()
    test_block_string()
    test_line_comment()
    test_operators()
    test_punctuation()
    test_all_keywords()
    test_indentation()
    test_nested_indentation()
    test_function_declaration()
    test_ai_prompt()
    test_agent_definition()
    test_scientific_notation()
    test_identifier_with_underscore()
    test_invalid_character()
    test_unterminated_string()
    test_multiple_statements()
    test_match_expression()
    print("All lexer tests passed!")
