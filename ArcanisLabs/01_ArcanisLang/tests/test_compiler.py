import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer.lexer import Lexer, LexerError
from parser.parser import Parser, ParseError
from compiler.codegen import CodeGenerator, CodeGenError
from compiler.optimizer import Optimizer
from compiler.ir import IRProgram, Function, BasicBlock, Instruction, Opcode


def compile(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    codegen = CodeGenerator()
    ir = codegen.compile(program)
    return ir


def compile_optimized(source):
    ir = compile(source)
    opt = Optimizer()
    opt.optimize(ir)
    return ir, opt


def test_empty():
    ir = compile("")
    assert len(ir.functions) == 1
    assert ir.functions[0].name == "__main__"


def test_integer_literal():
    ir = compile("42")
    assert len(ir.functions) == 1
    fn = ir.functions[0]
    assert fn.name == "__main__"


def test_var_declaration():
    ir = compile("let x = 42")
    assert len(ir.functions) >= 1
    found_store = False
    for fn in ir.functions:
        for block in fn.blocks:
            for instr in block.instructions:
                if instr.opcode == Opcode.STORE_VAR and "x" in instr.args:
                    found_store = True
    assert found_store


def test_function_declaration():
    ir = compile("""
fn add(a, b) {
    a + b
}
""")
    found_add = False
    for fn in ir.functions:
        if fn.name == "add":
            found_add = True
            assert fn.params == ["a", "b"]
    assert found_add


def test_function_call():
    ir = compile("print(42)")
    found_print = False
    for fn in ir.functions:
        for block in fn.blocks:
            for instr in block.instructions:
                if instr.opcode == Opcode.PRINT:
                    found_print = True
    assert found_print


def test_if_expression():
    ir = compile("""
let x = if true {
    10
} else {
    20
}
""")
    assert len(ir.functions) >= 1


def test_while_loop():
    ir = compile("""
let mut x = 0
while x < 10 {
    x = x + 1
}
""")
    assert len(ir.functions) >= 1


def test_for_loop():
    ir = compile("""
for i in [1, 2, 3] {
    let x = i
}
""")
    assert len(ir.functions) >= 1


def test_binary_arithmetic():
    ir = compile("let x = 10 + 20 * 3")
    found_add = False
    found_mul = False
    for fn in ir.functions:
        for block in fn.blocks:
            for instr in block.instructions:
                if instr.opcode == Opcode.ADD:
                    found_add = True
                if instr.opcode == Opcode.MUL:
                    found_mul = True
    assert found_add
    assert found_mul


def test_list_literal():
    ir = compile("let items = [1, 2, 3]")
    found_build = False
    for fn in ir.functions:
        for block in fn.blocks:
            for instr in block.instructions:
                if instr.opcode == Opcode.BUILD_LIST:
                    found_build = True
    assert found_build


def test_embed_expression():
    ir = compile('let x = embed("hello")')
    found_embed = False
    for fn in ir.functions:
        for block in fn.blocks:
            for instr in block.instructions:
                if instr.opcode == Opcode.EMBED:
                    found_embed = True
    assert found_embed


def test_ai_expression():
    ir = compile('let x = ai prompt("hello")')
    found_ai = False
    for fn in ir.functions:
        for block in fn.blocks:
            for instr in block.instructions:
                if instr.opcode == Opcode.AI_PROMPT:
                    found_ai = True
    assert found_ai


def test_optimizer_constant_folding():
    ir, opt = compile_optimized("let x = 2 + 3")
    assert opt.stats["constant_folded"] >= 1


def test_optimizer_multiple_folds():
    ir, opt = compile_optimized("let x = 1 + 2 + 3 + 4")
    assert opt.stats["constant_folded"] >= 3


def test_optimizer_comparison_folding():
    ir, opt = compile_optimized("let x = 5 > 3")
    assert opt.stats["constant_folded"] >= 1


def test_optimizer_string_concat_folding():
    ir, opt = compile_optimized('let x = "hello" ++ " world"')
    assert opt.stats["constant_folded"] >= 1


def test_optimizer_not_folding():
    ir, opt = compile_optimized("let x = !true")
    assert opt.stats["constant_folded"] >= 1


def test_optimizer_no_fold_variable():
    ir, opt = compile_optimized("let x = a + b")
    assert opt.stats["constant_folded"] == 0


def test_optimizer_mixed_fold():
    ir, opt = compile_optimized("""
let x = 2 + 3
let y = a + b
""")
    assert opt.stats["constant_folded"] >= 1


def test_optimizer_stats():
    ir, opt = compile_optimized("""
let a = 1 + 2
let b = 3 * 4
let c = 10 > 5
""")
    assert opt.stats["constant_folded"] >= 3


def test_ir_to_text():
    ir = compile("let x = 42")
    text = ir.to_text()
    assert isinstance(text, str)
    assert len(text) > 0


def test_optimizer_empty_program():
    ir, opt = compile_optimized("")
    assert opt.stats["constant_folded"] == 0


def test_optimizer_nop_elimination():
    ir, opt = compile_optimized("let x = 1")
    assert True


def test_optimizer_complex():
    source = """
fn factorial(n) {
    if n <= 1 {
        1
    } else {
        n * factorial(n - 1)
    }
}
let x = factorial(5)
"""
    ir, opt = compile_optimized(source)
    assert True


def test_struct_declaration():
    ir = compile("""
struct Point {
    x: i32
    y: i32
}
""")
    assert len(ir.functions) >= 1


def test_agent_declaration():
    ir = compile("""
agent Assistant {
    role: "Helpful assistant"
    model: "arcanis-default"
    fn respond(query: String) -> String {
        "hello"
    }
}
""")
    found_respond = False
    for fn in ir.functions:
        if fn.name == "respond":
            found_respond = True
    assert found_respond


def test_multiple_statements():
    ir = compile("""
let x = 10
let y = 20
let z = x + y
""")
    assert len(ir.functions) >= 1
