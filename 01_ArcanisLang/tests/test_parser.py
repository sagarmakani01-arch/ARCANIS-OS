import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lexer import Lexer
from src.parser import Parser
from src.ast import *
from src.errors import ParserError

class TestParser(unittest.TestCase):
    def _parse(self, source):
        lexer = Lexer(source)
        parser = Parser(lexer.tokens)
        return parser.parse()

    def test_empty(self):
        ast = self._parse("")
        self.assertIsInstance(ast, Program)
        self.assertEqual(len(ast.statements), 0)

    def test_integer_literal(self):
        ast = self._parse("42")
        self.assertIsInstance(ast.statements[0], Literal)
        self.assertEqual(ast.statements[0].value, 42)

    def test_float_literal(self):
        ast = self._parse("3.14")
        self.assertIsInstance(ast.statements[0], Literal)
        self.assertAlmostEqual(ast.statements[0].value, 3.14)

    def test_string_literal(self):
        ast = self._parse('"hello"')
        self.assertIsInstance(ast.statements[0], Literal)
        self.assertEqual(ast.statements[0].value, "hello")

    def test_boolean_literal(self):
        ast = self._parse("true")
        self.assertIsInstance(ast.statements[0], Literal)
        self.assertTrue(ast.statements[0].value)

    def test_none_literal(self):
        ast = self._parse("none")
        self.assertIsInstance(ast.statements[0], Literal)
        self.assertIsNone(ast.statements[0].value)

    def test_identifier(self):
        ast = self._parse("x")
        self.assertIsInstance(ast.statements[0], Identifier)
        self.assertEqual(ast.statements[0].name, "x")

    def test_assignment(self):
        ast = self._parse("x = 42")
        self.assertIsInstance(ast.statements[0], Assign)
        self.assertEqual(ast.statements[0].target.name, "x")
        self.assertEqual(ast.statements[0].value.value, 42)

    def test_binary_op(self):
        ast = self._parse("1 + 2")
        self.assertIsInstance(ast.statements[0], BinaryOp)
        self.assertEqual(ast.statements[0].op, "+")

    def test_precedence(self):
        ast = self._parse("1 + 2 * 3")
        op = ast.statements[0]
        self.assertIsInstance(op, BinaryOp)
        self.assertEqual(op.op, "+")
        self.assertIsInstance(op.right, BinaryOp)
        self.assertEqual(op.right.op, "*")

    def test_if_statement(self):
        ast = self._parse("if true:\n    x = 1")
        self.assertIsInstance(ast.statements[0], If)
        self.assertEqual(len(ast.statements[0].body), 1)

    def test_if_elif_else(self):
        source = """if x > 0:
    print("pos")
elif x < 0:
    print("neg")
else:
    print("zero")"""
        ast = self._parse(source)
        self.assertIsInstance(ast.statements[0], If)
        self.assertEqual(len(ast.statements[0].elifs), 1)
        self.assertIsNotNone(ast.statements[0].else_body)

    def test_while(self):
        ast = self._parse("while true:\n    x = 1")
        self.assertIsInstance(ast.statements[0], While)

    def test_for(self):
        ast = self._parse("for i in range(5):\n    print(i)")
        self.assertIsInstance(ast.statements[0], For)
        self.assertEqual(ast.statements[0].target.name, "i")

    def test_fun_def(self):
        ast = self._parse("fun add(a, b):\n    return a + b")
        self.assertIsInstance(ast.statements[0], FunctionDef)
        self.assertEqual(ast.statements[0].name, "add")
        self.assertEqual(len(ast.statements[0].params), 2)

    def test_class_def(self):
        source = """class Animal:
    fun init(self, name):
        self.name = name"""
        ast = self._parse(source)
        self.assertIsInstance(ast.statements[0], ClassDef)
        self.assertEqual(ast.statements[0].name, "Animal")

    def test_class_with_inheritance(self):
        source = """class Dog(Animal):
    fun bark(self):
        print("woof")"""
        ast = self._parse(source)
        self.assertIsInstance(ast.statements[0], ClassDef)
        self.assertEqual(ast.statements[0].base_classes, ["Animal"])

    def test_call(self):
        ast = self._parse("f(1, 2)")
        self.assertIsInstance(ast.statements[0], Call)
        self.assertEqual(len(ast.statements[0].args), 2)

    def test_list_literal(self):
        ast = self._parse("[1, 2, 3]")
        self.assertIsInstance(ast.statements[0], ListLiteral)
        self.assertEqual(len(ast.statements[0].elements), 3)

    def test_map_literal(self):
        ast = self._parse('{"a": 1, "b": 2}')
        self.assertIsInstance(ast.statements[0], MapLiteral)
        self.assertEqual(len(ast.statements[0].pairs), 2)

    def test_try_catch(self):
        source = """try:
    x = 1 / 0
catch e:
    print(e)"""
        ast = self._parse(source)
        self.assertIsInstance(ast.statements[0], TryCatch)

    def test_import(self):
        ast = self._parse("import math")
        self.assertIsInstance(ast.statements[0], Import)
        self.assertEqual(ast.statements[0].module, "math")

    def test_from_import(self):
        ast = self._parse("from math import sqrt")
        self.assertIsInstance(ast.statements[0], FromImport)
        self.assertEqual(ast.statements[0].module, "math")

    def test_break_continue(self):
        source = """while true:
    break
    continue"""
        ast = self._parse(source)
        self.assertIsInstance(ast.statements[0].body[0], Break)
        self.assertIsInstance(ast.statements[0].body[1], Continue)

    def test_return(self):
        ast = self._parse("fun f():\n    return 42")
        ret = ast.statements[0].body[0]
        self.assertIsInstance(ret, Return)
        self.assertEqual(ret.value.value, 42)

    def test_raise(self):
        ast = self._parse("raise \"error\"")
        self.assertIsInstance(ast.statements[0], Raise)

    def test_await(self):
        ast = self._parse("await x")
        self.assertIsInstance(ast.statements[0], Await)

if __name__ == "__main__":
    unittest.main()
