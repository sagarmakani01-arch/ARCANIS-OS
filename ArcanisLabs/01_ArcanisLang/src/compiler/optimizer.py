from typing import Dict, Set, Optional
from .ir import IRProgram, Function, BasicBlock, Instruction, Opcode


class Optimizer:
    def __init__(self):
        self.stats = {
            "constant_folded": 0,
            "dead_code_eliminated": 0,
            "simplified": 0,
        }

    def optimize(self, program: IRProgram) -> IRProgram:
        for func in program.functions:
            if func.is_native:
                continue
            self._optimize_function(func)
        return program

    def _optimize_function(self, func: Function):
        for block in func.blocks:
            self._constant_fold(block)
            self._peephole(block)
        self._dead_code_elimination(func)
        self._remove_empty_blocks(func)

    def _constant_fold(self, block: BasicBlock):
        changed = True
        while changed:
            changed = False
            for i, instr in enumerate(block.instructions):
                if self._try_fold_arithmetic(block, i, instr):
                    changed = True
                elif self._try_fold_comparison(block, i, instr):
                    changed = True
                elif self._try_fold_not(block, i, instr):
                    changed = True

    def _try_fold_arithmetic(self, block: BasicBlock, idx: int, instr: Instruction) -> bool:
        if instr.opcode not in (Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD, Opcode.CONCAT):
            return False
        if len(instr.args) != 2:
            return False

        left = self._find_const(block, instr.args[0])
        right = self._find_const(block, instr.args[1])
        if left is None or right is None:
            return False

        result = None
        if instr.opcode in (Opcode.ADD, Opcode.CONCAT) and type(left) == type(right):
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                result = left + right
            elif isinstance(left, str) and isinstance(right, str):
                result = left + right
        elif instr.opcode == Opcode.SUB and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            result = left - right
        elif instr.opcode == Opcode.MUL:
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                result = left * right
            elif isinstance(left, str) and isinstance(right, int):
                result = left * right
        elif instr.opcode == Opcode.DIV and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            if right != 0:
                result = left // right if isinstance(left, int) and isinstance(right, int) else left / right
        elif instr.opcode == Opcode.MOD and isinstance(left, int) and isinstance(right, int):
            if right != 0:
                result = left % right

        if result is not None:
            block.instructions[idx] = Instruction(
                Opcode.LOAD_CONST,
                dest=instr.dest,
                const_val=result,
                source_pos=instr.source_pos,
            )
            self.stats["constant_folded"] += 1
            return True
        return False

    def _try_fold_comparison(self, block: BasicBlock, idx: int, instr: Instruction) -> bool:
        if instr.opcode not in (Opcode.EQ, Opcode.NE, Opcode.LT, Opcode.GT, Opcode.LE, Opcode.GE):
            return False
        if len(instr.args) != 2:
            return False

        left = self._find_const(block, instr.args[0])
        right = self._find_const(block, instr.args[1])
        if left is None or right is None:
            return False

        result = None
        if instr.opcode == Opcode.EQ:
            result = left == right
        elif instr.opcode == Opcode.NE:
            result = left != right
        elif instr.opcode == Opcode.LT:
            result = left < right
        elif instr.opcode == Opcode.GT:
            result = left > right
        elif instr.opcode == Opcode.LE:
            result = left <= right
        elif instr.opcode == Opcode.GE:
            result = left >= right

        if result is not None:
            block.instructions[idx] = Instruction(
                Opcode.LOAD_CONST,
                dest=instr.dest,
                const_val=result,
                source_pos=instr.source_pos,
            )
            self.stats["constant_folded"] += 1
            return True
        return False

    def _try_fold_not(self, block: BasicBlock, idx: int, instr: Instruction) -> bool:
        if instr.opcode != Opcode.NOT or len(instr.args) != 1:
            return False

        val = self._find_const(block, instr.args[0])
        if val is None:
            return False

        result = not val
        block.instructions[idx] = Instruction(
            Opcode.LOAD_CONST,
            dest=instr.dest,
            const_val=result,
            source_pos=instr.source_pos,
        )
        self.stats["constant_folded"] += 1
        return True

    def _find_const(self, block: BasicBlock, reg: str):
        for instr in block.instructions:
            if instr.dest == reg and instr.opcode == Opcode.LOAD_CONST:
                return instr.const_val
        return None

    def _peephole(self, block: BasicBlock):
        i = 0
        while i < len(block.instructions):
            instr = block.instructions[i]

            if instr.opcode == Opcode.LOAD_CONST and i + 1 < len(block.instructions):
                next_instr = block.instructions[i + 1]
                if (next_instr.opcode in (Opcode.ADD, Opcode.SUB, Opcode.MUL) and
                    len(next_instr.args) == 2 and
                    next_instr.args[0] == instr.dest):
                    pass

            if instr.opcode == Opcode.NOP:
                block.instructions.pop(i)
                self.stats["simplified"] += 1
                continue

            i += 1

    def _dead_code_elimination(self, func: Function):
        for block in func.blocks:
            used_regs = self._find_used_regs(block)
            new_instructions = []
            for instr in block.instructions:
                if (instr.dest and
                    instr.dest not in used_regs and
                    instr.opcode not in (Opcode.STORE_VAR, Opcode.JUMP, Opcode.JUMP_IF,
                                         Opcode.JUMP_IF_NOT, Opcode.RETURN, Opcode.PRINT,
                                         Opcode.PRINTLN, Opcode.NOP, Opcode.MOV)):
                    self.stats["dead_code_eliminated"] += 1
                    continue
                new_instructions.append(instr)
            block.instructions = new_instructions

    def _find_used_regs(self, block: BasicBlock) -> Set[str]:
        used = set()
        for instr in block.instructions:
            for arg in instr.args:
                if isinstance(arg, str) and arg.startswith("r"):
                    used.add(arg)
            if instr.opcode == Opcode.STORE_VAR and len(instr.args) >= 2:
                if isinstance(instr.args[1], str):
                    used.add(instr.args[1])
        return used

    def _remove_empty_blocks(self, func: Function):
        to_remove = []
        for block in func.blocks:
            if not block.instructions and block.successor:
                to_remove.append(block.label)
        for label in to_remove:
            func.blocks = [b for b in func.blocks if b.label != label]

    def get_stats(self) -> dict:
        return dict(self.stats)
