import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lexer import Lexer
from src.tokens import TokenType
from src.errors import LexerError

class TestLexer(unittest.TestCase):
    def _token_types(self, source):
        lexer = Lexer(source)
        return [t.type for t in lexer.tokens if t.type not in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT, TokenType.EOF)]

    def test_empty(self):
        types = self._token_types("")
        self.assertEqual(types, [])

    def test_integer(self):
        types = self._token_types("42")
        self.assertEqual(types, [TokenType.INTEGER])

    def test_float(self):
        lexer = Lexer("3.14")
        types = [t.type for t in lexer.tokens if t.type not in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT, TokenType.EOF)]
        self.assertEqual(types, [TokenType.FLOAT])
        tokens = [t for t in lexer.tokens if t.type == TokenType.FLOAT]
        self.assertAlmostEqual(tokens[0].value, 3.14)

    def test_string(self):
        lexer = Lexer('"hello"')
        tokens = [t for t in lexer.tokens if t.type not in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT, TokenType.EOF)]
        self.assertEqual(tokens[0].value, "hello")

    def test_string_single_quotes(self):
        lexer = Lexer("'hello'")
        tokens = [t for t in lexer.tokens if t.type not in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT, TokenType.EOF)]
        self.assertEqual(tokens[0].value, "hello")

    def test_boolean(self):
        types = self._token_types("true false")
        self.assertEqual(types, [TokenType.BOOLEAN, TokenType.BOOLEAN])

    def test_none(self):
        types = self._token_types("none")
        self.assertEqual(types, [TokenType.NONE])

    def test_identifier(self):
        types = self._token_types("my_variable")
        self.assertEqual(types, [TokenType.IDENTIFIER])

    def test_keywords(self):
        types = self._token_types("if elif else for while fun return class import from try catch raise break continue async await pass in and or not")
        self.assertEqual(types, [
            TokenType.IF, TokenType.ELIF, TokenType.ELSE,
            TokenType.FOR, TokenType.WHILE, TokenType.FUN,
            TokenType.RETURN, TokenType.CLASS, TokenType.IMPORT,
            TokenType.FROM, TokenType.TRY, TokenType.CATCH,
            TokenType.RAISE, TokenType.BREAK, TokenType.CONTINUE,
            TokenType.ASYNC, TokenType.AWAIT, TokenType.PASS,
            TokenType.IN, TokenType.AND, TokenType.OR, TokenType.NOT
        ])

    def test_operators(self):
        types = self._token_types("+ - * / % ** == != < > <= >= = += -=")
        self.assertEqual(types, [
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
            TokenType.PERCENT, TokenType.POW,
            TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT,
            TokenType.LTE, TokenType.GTE,
            TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN
        ])

    def test_delimiters(self):
        types = self._token_types("( ) [ ] { } , . : ->")
        self.assertEqual(types, [
            TokenType.LPAREN, TokenType.RPAREN,
            TokenType.LBRACKET, TokenType.RBRACKET,
            TokenType.LBRACE, TokenType.RBRACE,
            TokenType.COMMA, TokenType.DOT, TokenType.COLON, TokenType.ARROW
        ])

    def test_comment(self):
        types = self._token_types("# this is a comment\n42")
        types = [t for t in types if t != TokenType.NEWLINE]
        self.assertEqual(types, [TokenType.INTEGER])

    def test_indentation(self):
        source = "if true:\n    x = 1\n    y = 2\nz = 3"
        lexer = Lexer(source)
        types = [t.type for t in lexer.tokens]
        self.assertIn(TokenType.INDENT, types)
        self.assertIn(TokenType.DEDENT, types)

    def test_string_escape(self):
        lexer = Lexer('"hello\\nworld"')
        tokens = [t for t in lexer.tokens if t.type not in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT, TokenType.EOF)]
        self.assertEqual(tokens[0].value, "hello\nworld")

    def test_line_numbers(self):
        lexer = Lexer("1\n2\n3")
        ints = [t for t in lexer.tokens if t.type == TokenType.INTEGER]
        self.assertEqual(ints[0].line, 1)
        self.assertEqual(ints[1].line, 2)
        self.assertEqual(ints[2].line, 3)

if __name__ == "__main__":
    unittest.main()
