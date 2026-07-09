from dataclasses import dataclass, field
from typing import List, Optional, Any, Callable


class RuntimeValue:
    pass


@dataclass
class IntValue(RuntimeValue):
    value: int

    def __str__(self):
        return str(self.value)


@dataclass
class FloatValue(RuntimeValue):
    value: float

    def __str__(self):
        return str(self.value)


@dataclass
class BoolValue(RuntimeValue):
    value: bool

    def __str__(self):
        return "true" if self.value else "false"


@dataclass
class StringValue(RuntimeValue):
    value: str

    def __str__(self):
        return self.value


@dataclass
class NilValue(RuntimeValue):
    def __str__(self):
        return "nil"


NIL = NilValue()


@dataclass
class ArrayValue(RuntimeValue):
    elements: List[RuntimeValue]

    def __str__(self):
        inner = ", ".join(str(e) for e in self.elements)
        return f"[{inner}]"


@dataclass
class TupleValue(RuntimeValue):
    elements: List[RuntimeValue]

    def __str__(self):
        inner = ", ".join(str(e) for e in self.elements)
        return f"({inner})"


@dataclass
class MapValue(RuntimeValue):
    entries: dict

    def __str__(self):
        inner = ", ".join(f"{k}: {v}" for k, v in self.entries.items())
        return f"{{{inner}}}"


@dataclass
class FunctionValue(RuntimeValue):
    name: str
    params: List["Param"]
    body: Any
    closure: Optional["Environment"] = None

    def __str__(self):
        return f"<fn {self.name}>"


@dataclass
class BuiltinFunction(RuntimeValue):
    name: str
    arity: int
    func: Callable

    def __str__(self):
        return f"<builtin {self.name}>"


@dataclass
class StructValue(RuntimeValue):
    name: str
    fields: dict

    def __str__(self):
        inner = ", ".join(f"{k}: {v}" for k, v in self.fields.items())
        return f"{self.name}({inner})"


@dataclass
class AgentValue(RuntimeValue):
    name: str
    role: Optional[str] = None
    model: Optional[str] = None
    methods: Optional[dict] = None

    def __str__(self):
        return f"<agent {self.name}>"


@dataclass
class EmbeddingValue(RuntimeValue):
    data: List[float] = field(default_factory=list)

    def __str__(self):
        return f"<embedding {len(self.data)}d>"


@dataclass
class MemoryValue(RuntimeValue):
    entries: List[dict] = field(default_factory=list)

    def __str__(self):
        return f"<memory {len(self.entries)} entries>"


@dataclass
class ResultValue(RuntimeValue):
    ok: bool
    value: RuntimeValue

    def __str__(self):
        if self.ok:
            return f"Ok({self.value})"
        return f"Err({self.value})"
