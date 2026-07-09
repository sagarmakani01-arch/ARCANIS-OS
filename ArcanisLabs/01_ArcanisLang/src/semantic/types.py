from dataclasses import dataclass, field
from typing import List, Optional, Any
from parser.ast import Position


class Type:
    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return str(self)


class PrimitiveType(Type):
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, PrimitiveType) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class FunctionType(Type):
    def __init__(self, params: List[Type], return_type: Type):
        self.params = params
        self.return_type = return_type

    def __str__(self):
        params = ", ".join(str(p) for p in self.params)
        return f"({params}) -> {self.return_type}"

    def __eq__(self, other):
        return (isinstance(other, FunctionType) and
                self.params == other.params and
                self.return_type == other.return_type)


class ArrayType(Type):
    def __init__(self, element_type: Type, size: Optional[int] = None):
        self.element_type = element_type
        self.size = size

    def __str__(self):
        if self.size:
            return f"[{self.element_type}; {self.size}]"
        return f"[{self.element_type}]"

    def __eq__(self, other):
        return (isinstance(other, ArrayType) and
                self.element_type == other.element_type and
                self.size == other.size)


class TupleType(Type):
    def __init__(self, types: List[Type]):
        self.types = types

    def __str__(self):
        inner = ", ".join(str(t) for t in self.types)
        return f"({inner})"

    def __eq__(self, other):
        return isinstance(other, TupleType) and self.types == other.types


class OptionalType(Type):
    def __init__(self, inner: Type):
        self.inner = inner

    def __str__(self):
        return f"{self.inner}?"

    def __eq__(self, other):
        return isinstance(other, OptionalType) and self.inner == other.inner


class ResultType(Type):
    def __init__(self, ok_type: Type, err_type: Type):
        self.ok_type = ok_type
        self.err_type = err_type

    def __str__(self):
        return f"Result<{self.ok_type}, {self.err_type}>"

    def __eq__(self, other):
        return (isinstance(other, ResultType) and
                self.ok_type == other.ok_type and
                self.err_type == other.err_type)


class NamedType(Type):
    def __init__(self, name: str, generic_args: Optional[List[Type]] = None):
        self.name = name
        self.generic_args = generic_args or []

    def __str__(self):
        if self.generic_args:
            args = ", ".join(str(a) for a in self.generic_args)
            return f"{self.name}<{args}>"
        return self.name

    def __eq__(self, other):
        return (isinstance(other, NamedType) and
                self.name == other.name and
                self.generic_args == other.generic_args)

    def __hash__(self):
        return hash(self.name)


class TraitType(Type):
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, TraitType) and self.name == other.name


class AgentType(Type):
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, AgentType) and self.name == other.name


class TypeVariable(Type):
    _counter = 0

    def __init__(self, constraint: Optional[Type] = None):
        TypeVariable._counter += 1
        self.id = TypeVariable._counter
        self.constraint = constraint
        self.instance: Optional[Type] = None

    def __str__(self):
        if self.instance:
            return str(self.instance)
        return f"T{self.id}"

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)


# Predefined types
NULL = PrimitiveType("nil")
BOOL = PrimitiveType("bool")
I8 = PrimitiveType("i8")
I16 = PrimitiveType("i16")
I32 = PrimitiveType("i32")
I64 = PrimitiveType("i64")
U8 = PrimitiveType("u8")
U16 = PrimitiveType("u16")
U32 = PrimitiveType("u32")
U64 = PrimitiveType("u64")
F32 = PrimitiveType("f32")
F64 = PrimitiveType("f64")
STRING = PrimitiveType("String")
CHAR = PrimitiveType("char")
NEVER = PrimitiveType("never")

PRIMITIVE_TYPES = {
    "nil": NULL, "bool": BOOL,
    "i8": I8, "i16": I16, "i32": I32, "i64": I64,
    "u8": U8, "u16": U16, "u32": U32, "u64": U64,
    "f32": F32, "f64": F64,
    "String": STRING, "char": CHAR,
}


def is_numeric(t: Type) -> bool:
    return t in (I8, I16, I32, I64, U8, U16, U32, U64, F32, F64)


def is_integer(t: Type) -> bool:
    return t in (I8, I16, I32, I64, U8, U16, U32, U64)
