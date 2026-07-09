import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer.lexer import Lexer
from parser.parser import Parser
from compiler.codegen import CodeGenerator
from compiler.optimizer import Optimizer
from compiler.ir import IRProgram, Function, BasicBlock, Instruction, Opcode
from vm.vm import VirtualMachine, VMError
from vm.memory import (
    MemoryManager, Value, make_int, make_float, make_bool, make_string,
    make_nil, make_list, make_struct, make_function,
)


def run(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    codegen = CodeGenerator()
    ir = codegen.compile(program)
    opt = Optimizer()
    ir = opt.optimize(ir)
    vm = VirtualMachine()
    output = vm.run(ir)
    return vm, output


def run_ir(ir):
    vm = VirtualMachine()
    output = vm.run(ir)
    return vm, output


def test_empty():
    vm, output = run("")
    assert output == []


def test_print_literal():
    vm, output = run('println(42)')
    assert output == ["42"]


def test_print_string():
    vm, output = run('println("hello")')
    assert output == ["hello"]


def test_var_declaration():
    vm, output = run('let x = 42; println(x)')
    assert output == ["42"]


def test_var_reassignment():
    vm, output = run('let mut x = 10; x = 20; println(x)')
    assert output == ["20"]


def test_binary_add():
    vm, output = run('println(2 + 3)')
    assert output == ["5"]


def test_binary_mul():
    vm, output = run('println(10 * 3)')
    assert output == ["30"]


def test_binary_sub():
    vm, output = run('println(10 - 3)')
    assert output == ["7"]


def test_binary_div():
    vm, output = run('println(10 / 2)')
    assert output == ["5"]


def test_binary_mod():
    vm, output = run('println(10 % 3)')
    assert output == ["1"]


def test_comparison_gt():
    vm, output = run('println(10 > 5)')
    assert output == ["True"]


def test_comparison_lt():
    vm, output = run('println(5 < 10)')
    assert output == ["True"]


def test_comparison_eq():
    vm, output = run('println(5 == 5)')
    assert output == ["True"]


def test_comparison_ne():
    vm, output = run('println(5 != 10)')
    assert output == ["True"]


def test_comparison_le():
    vm, output = run('println(5 <= 5)')
    assert output == ["True"]


def test_comparison_ge():
    vm, output = run('println(10 >= 5)')
    assert output == ["True"]


def test_logical_and():
    vm, output = run('println(true and false)')
    assert output == ["False"]


def test_logical_or():
    vm, output = run('println(true or false)')
    assert output == ["True"]


def test_logical_not():
    vm, output = run('println(!true)')
    assert output == ["False"]


def test_string_concat():
    vm, output = run('println("hello" ++ " world")')
    assert output == ["hello world"]


def test_if_true():
    vm, output = run('println(if true { 42 } else { 0 })')
    assert output == ["42"]


def test_if_false():
    vm, output = run('println(if false { 42 } else { 99 })')
    assert output == ["99"]


def test_while_loop():
    vm, output = run('''
let mut x = 0
while x < 5 {
    x = x + 1
}
println(x)
''')
    assert output == ["5"]


def test_for_loop():
    vm, output = run('''
let mut sum = 0
for i in [1, 2, 3] {
    sum = sum + i
}
println(sum)
''')
    assert output == ["6"]


def test_function_call():
    vm, output = run('''
fn add(a, b) {
    a + b
}
println(add(3, 4))
''')
    assert output == ["7"]


def test_function_return():
    vm, output = run('''
fn double(x) {
    return x * 2
}
println(double(5))
''')
    assert output == ["10"]


def test_recursive_function():
    vm, output = run('''
fn factorial(n) {
    if n <= 1 {
        1
    } else {
        n * factorial(n - 1)
    }
}
println(factorial(5))
''')
    assert output == ["120"]


def test_list_literal():
    vm, output = run('println([1, 2, 3])')
    assert output == ["[1, 2, 3]"]


def test_list_index():
    vm, output = run('''
let items = [10, 20, 30]
println(items[1])
''')
    assert output == ["20"]


def test_builtin_int():
    vm, output = run('println(int(3.14))')
    assert output == ["3"]


def test_builtin_str():
    vm, output = run('println(str(42))')
    assert output == ["42"]


def test_multiple_statements():
    vm, output = run('''
let x = 10
let y = 20
println(x + y)
''')
    assert output == ["30"]


def test_struct_declaration():
    vm, output = run('''
struct Point {
    x: i32
    y: i32
}
println("ok")
''')
    assert output == ["ok"]


def test_agent_declaration():
    vm, output = run('''
agent Assistant {
    role: "Helpful assistant"
    model: "arcanis-default"
    fn respond(query: String) -> String {
        "hello"
    }
}
println("ok")
''')
    assert output == ["ok"]


def test_embed_expression():
    vm, output = run('''
let emb = embed("hello")
println("ok")
''')
    assert output == ["ok"]


def test_ai_expression():
    vm, output = run('''
let resp = ai prompt("hello") system("be helpful")
println(resp)
''')
    assert "<AI response" in output[0]


def test_operator_precedence():
    vm, output = run('println(2 + 3 * 4)')
    assert output == ["14"]


def test_optimizer_constant_folding():
    source = 'println(2 + 3)'
    ir = compile(source) if False else None
    from lexer.lexer import Lexer
    from parser.parser import Parser
    from compiler.codegen import CodeGenerator
    from compiler.optimizer import Optimizer

    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    codegen = CodeGenerator()
    ir = codegen.compile(program)
    opt = Optimizer()
    ir = opt.optimize(ir)
    assert opt.stats["constant_folded"] >= 1


def test_vm_memory_stats():
    vm, output = run('println(42)')
    stats = vm.memory.stats()
    assert stats["total_allocated"] >= 0
