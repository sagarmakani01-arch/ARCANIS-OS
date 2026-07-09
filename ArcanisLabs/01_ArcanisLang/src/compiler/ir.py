from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple
from enum import Enum, auto


class Opcode(Enum):
    NOP = auto()
    HALT = auto()

    LOAD_CONST = auto()
    LOAD_VAR = auto()
    STORE_VAR = auto()

    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NEG = auto()
    NOT = auto()

    EQ = auto()
    NE = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    AND = auto()
    OR = auto()

    CONCAT = auto()

    JUMP = auto()
    JUMP_IF = auto()
    JUMP_IF_NOT = auto()

    CALL = auto()
    CALL_NATIVE = auto()
    RETURN = auto()

    BUILD_LIST = auto()
    BUILD_MAP = auto()
    BUILD_STRUCT = auto()
    INDEX = auto()
    STORE_INDEX = auto()
    GET_ATTR = auto()
    SET_ATTR = auto()

    MOV = auto()

    MAKE_CLOSURE = auto()

    PHI = auto()

    PRINT = auto()
    PRINTLN = auto()

    AI_PROMPT = auto()
    AI_MODEL = auto()
    EMBED = auto()


@dataclass
class Instruction:
    opcode: Opcode
    dest: Optional[str] = None
    args: List[str] = field(default_factory=list)
    const_val: Any = None
    source_pos: Optional[Any] = None

    def __repr__(self):
        parts = [self.opcode.name]
        if self.dest:
            parts.append(self.dest)
        if self.args:
            parts.extend(str(a) for a in self.args)
        if self.const_val is not None:
            parts.append(repr(self.const_val))
        return " ".join(parts)


@dataclass
class BasicBlock:
    label: str
    instructions: List[Instruction] = field(default_factory=list)
    successor: Optional[str] = None
    fallthrough: Optional[str] = None

    def add(self, opcode: Opcode, dest=None, args=None, const_val=None, source_pos=None):
        instr = Instruction(opcode, dest, args or [], const_val, source_pos)
        self.instructions.append(instr)
        return instr

    def __repr__(self):
        lines = [f"  {self.label}:"]
        for instr in self.instructions:
            lines.append(f"    {instr}")
        if self.successor:
            lines.append(f"    jump {self.successor}")
        elif self.fallthrough:
            lines.append(f"    fallthrough {self.fallthrough}")
        return "\n".join(lines)


@dataclass
class Function:
    name: str
    params: List[str]
    blocks: List[BasicBlock] = field(default_factory=list)
    entry_label: str = "entry"
    is_native: bool = False
    arity: int = 0

    def __repr__(self):
        header = f"fn {self.name}({', '.join(self.params)}):"
        body = "\n".join(str(b) for b in self.blocks)
        return f"{header}\n{body}"


@dataclass
class IRProgram:
    functions: List[Function] = field(default_factory=list)
    globals_: List[str] = field(default_factory=list)

    def add_function(self, func: Function):
        self.functions.append(func)

    def __repr__(self):
        return "\n".join(str(f) for f in self.functions)

    def to_text(self):
        lines = []
        for func in self.functions:
            lines.append(f"fn {func.name}({', '.join(func.params)}):")
            for block in func.blocks:
                lines.append(f"  {block.label}:")
                for instr in block.instructions:
                    lines.append(f"    {instr}")
                if block.successor:
                    lines.append(f"    jump {block.successor}")
                elif block.fallthrough:
                    lines.append(f"    fallthrough {block.fallthrough}")
            lines.append("")
        return "\n".join(lines)
