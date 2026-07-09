from typing import List, Dict, Any, Optional
from compiler.ir import IRProgram, Function, BasicBlock, Instruction, Opcode
from .memory import (
    MemoryManager, Value, make_int, make_float, make_bool, make_string,
    make_nil, make_list, make_tuple, make_function, make_native_function,
)


class VMError(Exception):
    def __init__(self, message: str, instruction: Instruction = None):
        self.instruction = instruction
        super().__init__(message)


class CallFrame:
    __slots__ = ('function', 'return_block', 'return_pc', 'regs')

    def __init__(self, function: Function, return_block: str = None, return_pc: int = 0):
        self.function = function
        self.return_block = return_block
        self.return_pc = return_pc
        self.regs: Dict[str, Value] = {}


class VirtualMachine:
    def __init__(self):
        self.memory = MemoryManager()
        self.globals: Dict[str, Value] = {}
        self.call_stack: List[CallFrame] = []
        self.current_frame: Optional[CallFrame] = None
        self.block_map: Dict[str, BasicBlock] = {}
        self.block_names: List[str] = []
        self.pc = 0
        self.halted = False
        self.output: List[str] = []
        self._jump_target: Optional[str] = None
        self._init_native_builtins()

    def _init_native_builtins(self):
        self.globals["print"] = make_native_function("print", self._native_print)
        self.globals["println"] = make_native_function("println", self._native_println)
        self.globals["int"] = make_native_function("int", self._native_int)
        self.globals["float"] = make_native_function("float", self._native_float)
        self.globals["str"] = make_native_function("str", self._native_str)
        self.globals["pi"] = make_float(3.141592653589793)
        self.globals["e"] = make_float(2.718281828459045)
        self.globals["sin"] = make_native_function("sin", self._native_sin)
        self.globals["cos"] = make_native_function("cos", self._native_cos)
        self.globals["sqrt"] = make_native_function("sqrt", self._native_sqrt)
        self.globals["abs"] = make_native_function("abs", self._native_abs)
        self.globals["floor"] = make_native_function("floor", self._native_floor)
        self.globals["ceil"] = make_native_function("ceil", self._native_ceil)
        self.globals["round"] = make_native_function("round", self._native_round)
        self.globals["random"] = make_native_function("random", self._native_random)
        self.globals["len"] = make_native_function("len", self._native_len)

    def _native_print(self, args):
        val = args[0] if args else make_nil()
        self.output.append(str(val.data))
        return make_nil()

    def _native_println(self, args):
        val = args[0] if args else make_nil()
        self.output.append(str(val.data))
        return make_nil()

    def _native_int(self, args):
        val = args[0] if args else make_nil()
        return make_int(int(val.data) if val.data is not None else 0)

    def _native_float(self, args):
        val = args[0] if args else make_nil()
        return make_float(float(val.data) if val.data is not None else 0.0)

    def _native_str(self, args):
        val = args[0] if args else make_nil()
        return make_string(str(val.data) if val.data is not None else "nil")

    def _native_sin(self, args):
        import math
        val = args[0] if args else make_float(0.0)
        return make_float(math.sin(float(val.data)))

    def _native_cos(self, args):
        import math
        val = args[0] if args else make_float(0.0)
        return make_float(math.cos(float(val.data)))

    def _native_sqrt(self, args):
        import math
        val = args[0] if args else make_float(0.0)
        return make_float(math.sqrt(float(val.data)))

    def _native_abs(self, args):
        val = args[0] if args else make_int(0)
        return make_int(abs(int(val.data)) if isinstance(val.data, int) else abs(float(val.data)))

    def _native_floor(self, args):
        import math
        val = args[0] if args else make_float(0.0)
        return make_float(math.floor(float(val.data)))

    def _native_ceil(self, args):
        import math
        val = args[0] if args else make_float(0.0)
        return make_float(math.ceil(float(val.data)))

    def _native_round(self, args):
        val = args[0] if args else make_int(0)
        return make_int(round(float(val.data)))

    def _native_random(self, args):
        import random
        return make_float(random.random())

    def _native_len(self, args):
        val = args[0] if args else make_nil()
        if val.vtype == "list":
            return make_int(len(val.data))
        if val.vtype == "string":
            return make_int(len(val.data))
        return make_int(0)

    def run(self, program: IRProgram) -> List[str]:
        self.output = []
        self.halted = False
        self.program = program

        for func in program.functions:
            if func.name != "__main__":
                self.globals[func.name] = make_function(
                    func.name, func.params, func, None
                )

        for func in program.functions:
            if func.name == "__main__":
                self._run_function(func)
                break

        return self.output

    def _run_function(self, func: Function, frame: CallFrame = None):
        if not func.blocks:
            return

        self.block_map = {}
        self.block_names = []
        for block in func.blocks:
            self.block_map[block.label] = block
            self.block_names.append(block.label)

        if frame is None:
            self.current_frame = CallFrame(func)
        else:
            self.current_frame = frame
        self.pc = 0
        self.halted = False

        if not self.block_names:
            return

        current_block = self.block_map[self.block_names[0]]

        while not self.halted:
            self._jump_target = None

            if self.pc >= len(current_block.instructions):
                if current_block.successor and current_block.successor in self.block_map:
                    current_block = self.block_map[current_block.successor]
                    self.pc = 0
                elif current_block.fallthrough and current_block.fallthrough in self.block_map:
                    current_block = self.block_map[current_block.fallthrough]
                    self.pc = 0
                else:
                    break

            instr = current_block.instructions[self.pc]
            self._execute_instruction(instr)

            if self._jump_target and self._jump_target in self.block_map:
                current_block = self.block_map[self._jump_target]
                self.pc = 0
            else:
                self.pc += 1

    def _execute_instruction(self, instr: Instruction) -> bool:
        opcode = instr.opcode
        jumped = False

        if opcode == Opcode.NOP:
            pass
        elif opcode == Opcode.HALT:
            self.halted = True
        elif opcode == Opcode.MOV:
            val = self._get_reg(instr.args[0]) if instr.args else make_nil()
            self._set_reg(instr.dest, val)
        elif opcode == Opcode.LOAD_CONST:
            self._set_reg(instr.dest, self._make_value(instr.const_val))
        elif opcode == Opcode.LOAD_VAR:
            name = instr.args[0] if instr.args else ""
            val = self._get_var(name)
            if instr.dest:
                self._set_reg(instr.dest, val)
        elif opcode == Opcode.STORE_VAR:
            name = instr.args[0] if instr.args else ""
            val = self._get_reg(instr.args[1]) if len(instr.args) > 1 else make_nil()
            self._set_var(name, val)
        elif opcode == Opcode.ADD:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            result = self._add(left, right)
            self._set_reg(instr.dest, result)
        elif opcode == Opcode.SUB:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            result = self._sub(left, right)
            self._set_reg(instr.dest, result)
        elif opcode == Opcode.MUL:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            result = self._mul(left, right)
            self._set_reg(instr.dest, result)
        elif opcode == Opcode.DIV:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            result = self._div(left, right)
            self._set_reg(instr.dest, result)
        elif opcode == Opcode.MOD:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            result = self._mod(left, right)
            self._set_reg(instr.dest, result)
        elif opcode == Opcode.NEG:
            val = self._get_reg(instr.args[0])
            result = make_int(-val.data) if val.vtype == "int" else make_float(-float(val.data))
            self._set_reg(instr.dest, result)
        elif opcode == Opcode.NOT:
            val = self._get_reg(instr.args[0])
            result = make_bool(not self._is_truthy(val))
            self._set_reg(instr.dest, result)
        elif opcode == Opcode.EQ:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            self._set_reg(instr.dest, make_bool(left.data == right.data))
        elif opcode == Opcode.NE:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            self._set_reg(instr.dest, make_bool(left.data != right.data))
        elif opcode == Opcode.LT:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            self._set_reg(instr.dest, make_bool(left.data < right.data))
        elif opcode == Opcode.GT:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            self._set_reg(instr.dest, make_bool(left.data > right.data))
        elif opcode == Opcode.LE:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            self._set_reg(instr.dest, make_bool(left.data <= right.data))
        elif opcode == Opcode.GE:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            self._set_reg(instr.dest, make_bool(left.data >= right.data))
        elif opcode == Opcode.AND:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            self._set_reg(instr.dest, make_bool(self._is_truthy(left) and self._is_truthy(right)))
        elif opcode == Opcode.OR:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            self._set_reg(instr.dest, make_bool(self._is_truthy(left) or self._is_truthy(right)))
        elif opcode == Opcode.CONCAT:
            left = self._get_reg(instr.args[0])
            right = self._get_reg(instr.args[1])
            result = make_string(str(left.data) + str(right.data))
            self._set_reg(instr.dest, result)
        elif opcode == Opcode.PRINT:
            args = [self._get_reg(a) for a in instr.args]
            val = args[0] if args else make_nil()
            self.output.append(str(val))
        elif opcode == Opcode.PRINTLN:
            args = [self._get_reg(a) for a in instr.args]
            val = args[0] if args else make_nil()
            self.output.append(str(val))
        elif opcode == Opcode.CALL:
            self._execute_call(instr)
        elif opcode == Opcode.CALL_NATIVE:
            self._execute_native_call(instr)
        elif opcode == Opcode.RETURN:
            self._execute_return(instr)
        elif opcode == Opcode.BUILD_LIST:
            elements = [self._get_reg(a) for a in instr.args]
            self._set_reg(instr.dest, make_list(elements))
        elif opcode == Opcode.BUILD_STRUCT:
            name = instr.args[0] if instr.args else "Struct"
            fields = {}
            i = 1
            while i + 1 < len(instr.args):
                field_name = instr.args[i]
                field_val = self._get_reg(instr.args[i + 1])
                fields[field_name] = field_val
                i += 2
            self._set_reg(instr.dest, make_struct(name, fields))
        elif opcode == Opcode.INDEX:
            target = self._get_reg(instr.args[0])
            index = self._get_reg(instr.args[1])
            result = self._index(target, index)
            self._set_reg(instr.dest, result)
        elif opcode == Opcode.GET_ATTR:
            target = self._get_reg(instr.args[0])
            attr = instr.args[1]
            result = self._get_attr(target, attr)
            self._set_reg(instr.dest, result)
        elif opcode == Opcode.SET_ATTR:
            target = self._get_reg(instr.args[0])
            attr = instr.args[1]
            val = self._get_reg(instr.args[2])
            if target.vtype == "struct" and attr in target.data["fields"]:
                target.data["fields"][attr] = val
        elif opcode == Opcode.JUMP:
            target = instr.args[0] if instr.args else ""
            if target in self.block_map:
                self._jump_target = target
                jumped = True
        elif opcode == Opcode.JUMP_IF:
            cond = self._get_reg(instr.args[0])
            target = instr.args[1] if len(instr.args) > 1 else ""
            if self._is_truthy(cond) and target in self.block_map:
                self._jump_target = target
                jumped = True
        elif opcode == Opcode.JUMP_IF_NOT:
            cond = self._get_reg(instr.args[0])
            target = instr.args[1] if len(instr.args) > 1 else ""
            if not self._is_truthy(cond) and target in self.block_map:
                self._jump_target = target
                jumped = True
        elif opcode == Opcode.AI_PROMPT:
            args = [self._get_reg(a) for a in instr.args]
            prompt = str(args[0].data) if args else ""
            self._set_reg(instr.dest, make_string(f"<AI response to: {prompt[:50]}>"))
        elif opcode == Opcode.EMBED:
            args = [self._get_reg(a) for a in instr.args]
            text = str(args[0].data) if args else ""
            import random
            random.seed(hash(text) % (2**31))
            data = [random.random() for _ in range(4)]
            self._set_reg(instr.dest, make_list([make_float(x) for x in data]))

        return jumped

    def _execute_call(self, instr: Instruction):
        func_name = instr.args[0] if instr.args else ""
        arg_regs = instr.args[1:] if len(instr.args) > 1 else []

        func_val = self._get_var(func_name) if isinstance(func_name, str) else make_nil()

        if func_val.vtype == "native_function":
            args = [self._get_reg(a) for a in arg_regs]
            result = func_val.data["func"](args)
            if instr.dest:
                self._set_reg(instr.dest, result)
            return

        if func_val.vtype == "function":
            func_info = func_val.data
            args = [self._get_reg(a) for a in arg_regs]

            saved_block_map = self.block_map
            saved_block_names = self.block_names
            saved_pc = self.pc

            new_frame = CallFrame(
                Function(
                    name=func_info["name"],
                    params=func_info["params"],
                    blocks=func_info["body"].blocks if func_info["body"] else [],
                ),
                return_block=None,
                return_pc=0,
            )
            for param, arg in zip(func_info["params"], args):
                new_frame.regs[param] = arg

            self.call_stack.append(self.current_frame)
            self.current_frame = new_frame
            self._run_function(new_frame.function, frame=new_frame)

            return_val = make_nil()
            if "__return__" in new_frame.regs:
                return_val = new_frame.regs["__return__"]

            self.current_frame = self.call_stack.pop() if self.call_stack else None
            self.block_map = saved_block_map
            self.block_names = saved_block_names
            self.pc = saved_pc

            if instr.dest and self.current_frame:
                self._set_reg(instr.dest, return_val)

    def _execute_native_call(self, instr: Instruction):
        func_name = instr.args[0] if instr.args else ""
        arg_regs = instr.args[1:] if len(instr.args) > 1 else []

        func_val = self._get_var(func_name)
        if func_val.vtype == "native_function":
            args = [self._get_reg(a) for a in arg_regs]
            result = func_val.data["func"](args)
            if instr.dest:
                self._set_reg(instr.dest, result)
        else:
            if instr.dest:
                self._set_reg(instr.dest, make_nil())

    def _execute_return(self, instr: Instruction):
        val = self._get_reg(instr.args[0]) if instr.args else make_nil()
        if self.current_frame:
            self.current_frame.regs["__return__"] = val

    def _make_value(self, val) -> Value:
        if val is None:
            return make_nil()
        if isinstance(val, bool):
            return make_bool(val)
        if isinstance(val, int):
            return make_int(val)
        if isinstance(val, float):
            return make_float(val)
        if isinstance(val, str):
            return make_string(val)
        if isinstance(val, Value):
            return val
        return make_nil()

    def _get_reg(self, name: str) -> Value:
        if isinstance(name, str) and name.startswith("r"):
            if self.current_frame and name in self.current_frame.regs:
                return self.current_frame.regs[name]
        return self._get_var(name)

    def _set_reg(self, name: str, val: Value):
        if name and self.current_frame:
            self.current_frame.regs[name] = val

    def _get_var(self, name: str) -> Value:
        if self.current_frame and name in self.current_frame.regs:
            return self.current_frame.regs[name]
        if name in self.globals:
            return self.globals[name]
        return make_nil()

    def _set_var(self, name: str, val: Value):
        if self.current_frame:
            self.current_frame.regs[name] = val
        self.globals[name] = val

    def _is_truthy(self, val: Value) -> bool:
        if val.vtype == "bool":
            return val.data
        if val.vtype == "nil":
            return False
        if val.vtype == "int":
            return val.data != 0
        if val.vtype == "float":
            return val.data != 0.0
        if val.vtype == "string":
            return len(val.data) > 0
        return True

    def _add(self, left: Value, right: Value) -> Value:
        if left.vtype == "int" and right.vtype == "int":
            return make_int(left.data + right.data)
        if left.vtype in ("int", "float") and right.vtype in ("int", "float"):
            l = float(left.data) if left.vtype == "float" else float(left.data)
            r = float(right.data) if right.vtype == "float" else float(right.data)
            return make_float(l + r)
        if left.vtype == "string" or right.vtype == "string":
            return make_string(str(left.data) + str(right.data))
        return make_nil()

    def _sub(self, left: Value, right: Value) -> Value:
        if left.vtype == "int" and right.vtype == "int":
            return make_int(left.data - right.data)
        return make_float(float(left.data) - float(right.data))

    def _mul(self, left: Value, right: Value) -> Value:
        if left.vtype == "int" and right.vtype == "int":
            return make_int(left.data * right.data)
        return make_float(float(left.data) * float(right.data))

    def _div(self, left: Value, right: Value) -> Value:
        if left.vtype == "int" and right.vtype == "int":
            if right.data == 0:
                return make_nil()
            return make_int(left.data // right.data)
        r = float(right.data)
        if r == 0:
            return make_nil()
        return make_float(float(left.data) / r)

    def _mod(self, left: Value, right: Value) -> Value:
        if left.vtype == "int" and right.vtype == "int":
            if right.data == 0:
                return make_nil()
            return make_int(left.data % right.data)
        return make_nil()

    def _index(self, target: Value, index: Value) -> Value:
        if target.vtype == "list" and index.vtype == "int":
            i = index.data
            if 0 <= i < len(target.data):
                return target.data[i]
        if target.vtype == "string" and index.vtype == "int":
            i = index.data
            if 0 <= i < len(target.data):
                return make_string(target.data[i])
        return make_nil()

    def _get_attr(self, target: Value, attr: str) -> Value:
        if target.vtype == "struct" and attr in target.data["fields"]:
            return target.data["fields"][attr]
        if target.vtype == "string":
            if attr == "len":
                return make_int(len(target.data))
        return make_nil()
