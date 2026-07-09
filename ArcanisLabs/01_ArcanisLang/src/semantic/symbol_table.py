from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum, auto

from .types import Type


class SymbolKind(Enum):
    VARIABLE = auto()
    FUNCTION = auto()
    TYPE = auto()
    TRAIT = auto()
    AGENT = auto()
    PARAMETER = auto()
    BUILTIN = auto()


@dataclass
class Symbol:
    name: str
    kind: SymbolKind
    type: Type
    mutable: bool = False
    defined_at: Optional[Any] = None


class Scope:
    def __init__(self, parent: Optional["Scope"] = None, level: int = 0):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.level = level

    def define(self, symbol: Symbol):
        self.symbols[symbol.name] = symbol

    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        scope = self
        while scope:
            sym = scope.symbols.get(name)
            if sym:
                return sym
            scope = scope.parent
        return None

    def __repr__(self):
        return f"Scope(level={self.level}, symbols={list(self.symbols.keys())})"


class SymbolTable:
    def __init__(self):
        self.global_scope = Scope(level=0)
        self.current_scope = self.global_scope
        self.scopes: List[Scope] = [self.global_scope]

    def enter_scope(self) -> Scope:
        scope = Scope(parent=self.current_scope, level=self.current_scope.level + 1)
        self.current_scope = scope
        self.scopes.append(scope)
        return scope

    def exit_scope(self) -> Optional[Scope]:
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
            return self.current_scope
        return None

    def define(self, name: str, kind: SymbolKind, type: Type, mutable: bool = False, defined_at=None) -> Symbol:
        sym = Symbol(name, kind, type, mutable, defined_at)
        self.current_scope.define(sym)
        return sym

    def lookup(self, name: str) -> Optional[Symbol]:
        return self.current_scope.lookup(name)

    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self.current_scope.lookup_local(name)

    def resolve(self, name: str) -> Optional[Symbol]:
        return self.current_scope.lookup(name)
