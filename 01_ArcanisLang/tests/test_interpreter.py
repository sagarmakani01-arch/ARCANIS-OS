import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.interpreter import Interpreter
from src.builtins import STANDARD_ENV
from src.errors import RuntimeError_

class TestInterpreter(unittest.TestCase):
    def _run(self, source):
        lexer = Lexer(source)
        parser = Parser(lexer.tokens)
        ast = parser.parse()
        analyzer = SemanticAnalyzer()
        analyzer.visit(ast)
        interp = Interpreter(dict(STANDARD_ENV))
        return interp.visit(ast)

    def test_literal_int(self):
        result = self._run("42")
        self.assertEqual(result, 42)

    def test_literal_float(self):
        result = self._run("3.14")
        self.assertAlmostEqual(result, 3.14)

    def test_literal_string(self):
        result = self._run('"hello"')
        self.assertEqual(result, "hello")

    def test_literal_bool(self):
        result = self._run("true")
        self.assertTrue(result)
        result = self._run("false")
        self.assertFalse(result)

    def test_literal_none(self):
        result = self._run("none")
        self.assertIsNone(result)

    def test_assignment(self):
        result = self._run("x = 42\nx")
        self.assertEqual(result, 42)

    def test_addition(self):
        result = self._run("1 + 2")
        self.assertEqual(result, 3)

    def test_subtraction(self):
        result = self._run("5 - 3")
        self.assertEqual(result, 2)

    def test_multiplication(self):
        result = self._run("4 * 3")
        self.assertEqual(result, 12)

    def test_division(self):
        result = self._run("10 / 2")
        self.assertEqual(result, 5.0)

    def test_modulo(self):
        result = self._run("10 % 3")
        self.assertEqual(result, 1)

    def test_power(self):
        result = self._run("2 ** 3")
        self.assertEqual(result, 8)

    def test_comparison_eq(self):
        self.assertTrue(self._run("1 == 1"))
        self.assertFalse(self._run("1 == 2"))

    def test_comparison_neq(self):
        self.assertTrue(self._run("1 != 2"))
        self.assertFalse(self._run("1 != 1"))

    def test_comparison_lt(self):
        self.assertTrue(self._run("1 < 2"))
        self.assertFalse(self._run("2 < 1"))

    def test_comparison_gt(self):
        self.assertTrue(self._run("2 > 1"))
        self.assertFalse(self._run("1 > 2"))

    def test_and_or_not(self):
        self.assertTrue(self._run("true and true"))
        self.assertFalse(self._run("true and false"))
        self.assertTrue(self._run("true or false"))
        self.assertFalse(self._run("false or false"))
        self.assertFalse(self._run("not true"))
        self.assertTrue(self._run("not false"))

    def test_if_true(self):
        result = self._run("if true:\n    x = 1\nelse:\n    x = 2\nx")
        self.assertEqual(result, 1)

    def test_if_false(self):
        result = self._run("if false:\n    x = 1\nelse:\n    x = 2\nx")
        self.assertEqual(result, 2)

    def test_if_elif(self):
        source = """x = 2
if x == 1:
    result = "one"
elif x == 2:
    result = "two"
else:
    result = "other"
result"""
        self.assertEqual(self._run(source), "two")

    def test_while(self):
        result = self._run("""x = 0
while x < 3:
    x = x + 1
x""")
        self.assertEqual(result, 3)

    def test_for(self):
        result = self._run("""s = 0
for i in range(4):
    s = s + i
s""")
        self.assertEqual(result, 6)

    def test_function_def_and_call(self):
        source = """fun add(a, b):
    return a + b
add(3, 4)"""
        self.assertEqual(self._run(source), 7)

    def test_function_recursive(self):
        source = """fun fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
fact(5)"""
        self.assertEqual(self._run(source), 120)

    def test_function_no_return(self):
        source = """fun f():
    x = 1
result = f()
result"""
        self.assertIsNone(self._run(source))

    def test_class_and_instance(self):
        source = """class Dog:
    fun init(self, name):
        self.name = name
    fun bark(self):
        return self.name + " says woof"

d = Dog("Rex")
d.bark()"""
        self.assertEqual(self._run(source), "Rex says woof")

    def test_list_literal(self):
        result = self._run("[1, 2, 3]")
        self.assertEqual(result, [1, 2, 3])

    def test_list_index(self):
        result = self._run('[1, 2, 3][1]')
        self.assertEqual(result, 2)

    def test_map_literal(self):
        result = self._run('{"a": 1, "b": 2}')
        self.assertEqual(result, {"a": 1, "b": 2})

    def test_map_access(self):
        result = self._run('{"a": 1}["a"]')
        self.assertEqual(result, 1)

    def test_nested_expressions(self):
        result = self._run("(1 + 2) * (3 + 4)")
        self.assertEqual(result, 21)

    def test_string_concat(self):
        result = self._run('"Hello, " + "World!"')
        self.assertEqual(result, "Hello, World!")

    def test_print_builtin(self):
        result = self._run('print("test")')
        self.assertIsNone(result)

    def test_len_builtin(self):
        result = self._run('len([1, 2, 3])')
        self.assertEqual(result, 3)

    def test_range_builtin(self):
        result = self._run('range(5)')
        self.assertEqual(result, [0, 1, 2, 3, 4])

    def test_str_builtin(self):
        result = self._run('str(42)')
        self.assertEqual(result, "42")

    def test_int_builtin(self):
        result = self._run('int("42")')
        self.assertEqual(result, 42)

    def test_float_builtin(self):
        result = self._run('float("3.14")')
        self.assertAlmostEqual(result, 3.14)

    def test_type_builtin(self):
        result = self._run('type(42)')
        self.assertEqual(result, "int")

    def test_break(self):
        result = self._run("""x = 0
while true:
    x = x + 1
    if x == 3:
        break
x""")
        self.assertEqual(result, 3)

    def test_continue(self):
        result = self._run("""evens = 0
for i in range(5):
    if i % 2 == 0:
        evens = evens + 1
evens""")
        self.assertEqual(result, 3)

    def test_try_catch_no_error(self):
        result = self._run("""try:
    x = 1 + 1
catch e:
    x = 0
x""")
        self.assertEqual(result, 2)

    def test_try_catch_error(self):
        result = self._run("""try:
    x = 1 / 0
catch e:
    x = -1
x""")
        self.assertEqual(result, -1)

    def test_raise_and_catch(self):
        result = self._run("""try:
    raise "error occurred"
catch e:
    result = "caught: " + e
result""")
        self.assertEqual(result, "caught: error occurred")

    def test_unary_minus(self):
        result = self._run("-5")
        self.assertEqual(result, -5)

    def test_unary_not(self):
        result = self._run("not true")
        self.assertFalse(result)

    def test_chained_assignment_increment(self):
        result = self._run("x = 5\nx += 3\nx")
        self.assertEqual(result, 8)

    def test_chained_assignment_decrement(self):
        result = self._run("x = 5\nx -= 2\nx")
        self.assertEqual(result, 3)

    def test_member_access(self):
        result = self._run('x = {"name": "test"}\nx.name')
        self.assertEqual(result, "test")

    def test_sum_builtin(self):
        result = self._run("sum([1, 2, 3, 4, 5])")
        self.assertEqual(result, 15)

    def test_max_builtin(self):
        result = self._run("max(3, 7, 1)")
        self.assertEqual(result, 7)

    def test_min_builtin(self):
        result = self._run("min(3, 7, 1)")
        self.assertEqual(result, 1)

    def test_abs_builtin(self):
        result = self._run("abs(-5)")
        self.assertEqual(result, 5)

    def test_modulo_negative(self):
        result = self._run("7 % 3")
        self.assertEqual(result, 1)

    def test_float_operations(self):
        result = self._run("2.5 * 2")
        self.assertEqual(result, 5.0)

if __name__ == "__main__":
    unittest.main()
