from typing import Optional, Dict, Any
from .values import RuntimeValue, NilValue, NIL


class Environment:
    def __init__(self, parent: Optional["Environment"] = None):
        self.parent = parent
        self.values: Dict[str, RuntimeValue] = {}

    def define(self, name: str, value: RuntimeValue):
        self.values[name] = value

    def assign(self, name: str, value: RuntimeValue):
        if name in self.values:
            self.values[name] = value
        elif self.parent:
            self.parent.assign(name, value)
        else:
            raise RuntimeError(f"Undefined variable '{name}'")

    def get(self, name: str) -> RuntimeValue:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable '{name}'")

    def has_local(self, name: str) -> bool:
        return name in self.values

    def enter_scope(self) -> "Environment":
        return Environment(self)

    def __repr__(self):
        return f"Environment({list(self.values.keys())})"
