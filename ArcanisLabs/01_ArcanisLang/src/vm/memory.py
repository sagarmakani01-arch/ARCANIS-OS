from typing import Any, Dict, Optional
import sys


class Value:
    __slots__ = ('_data', '_type', '_ref_count', '_gc_mark')

    def __init__(self, data: Any = None, vtype: str = "nil"):
        self._data = data
        self._type = vtype
        self._ref_count = 0
        self._gc_mark = False

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, val):
        self._data = val

    @property
    def vtype(self):
        return self._type

    def inc_ref(self):
        self._ref_count += 1

    def dec_ref(self):
        self._ref_count -= 1
        return self._ref_count <= 0

    @property
    def ref_count(self):
        return self._ref_count

    def __repr__(self):
        return f"Value({self._type}, {self._data})"

    def __str__(self):
        if self._type == "list":
            return "[" + ", ".join(str(e) for e in self._data) + "]"
        if self._type == "tuple":
            return "(" + ", ".join(str(e) for e in self._data) + ")"
        if self._type == "struct":
            fields = ", ".join(f"{k}: {v}" for k, v in self._data.get("fields", {}).items())
            return f"{self._data.get('name', 'Struct')}({fields})"
        if self._type == "function":
            return f"<fn {self._data.get('name', '?')}>"
        if self._type == "native_function":
            return f"<builtin {self._data.get('name', '?')}>"
        return str(self._data)


def make_int(val: int) -> Value:
    return Value(val, "int")

def make_float(val: float) -> Value:
    return Value(val, "float")

def make_bool(val: bool) -> Value:
    return Value(val, "bool")

def make_string(val: str) -> Value:
    return Value(val, "string")

def make_nil() -> Value:
    return Value(None, "nil")

def make_list(elements: list) -> Value:
    v = Value(elements, "list")
    for e in elements:
        if isinstance(e, Value):
            e.inc_ref()
    return v

def make_tuple(elements: list) -> Value:
    v = Value(elements, "tuple")
    for e in elements:
        if isinstance(e, Value):
            e.inc_ref()
    return v

def make_function(name: str, params: list, body: Any, closure: Any = None) -> Value:
    return Value({"name": name, "params": params, "body": body, "closure": closure}, "function")

def make_native_function(name: str, func) -> Value:
    return Value({"name": name, "func": func}, "native_function")

def make_struct(name: str, fields: dict) -> Value:
    return Value({"name": name, "fields": fields}, "struct")

def make_agent(name: str, methods: dict) -> Value:
    return Value({"name": name, "methods": methods}, "agent")


class MemoryManager:
    def __init__(self, max_heap: int = 1024 * 1024):
        self.max_heap = max_heap
        self.allocated: list[Value] = []
        self.total_allocated = 0
        self.gc_count = 0
        self.bytes_allocated = 0

    def allocate(self, value: Value) -> Value:
        self.allocated.append(value)
        self.total_allocated += 1
        self.bytes_allocated += sys.getsizeof(value)

        if self.bytes_allocated > self.max_heap:
            self.collect()

        return value

    def collect(self):
        self.gc_count += 1
        unreachable = []
        for val in self.allocated:
            if val.ref_count <= 0:
                unreachable.append(val)

        for val in unreachable:
            self.allocated.remove(val)
            self.bytes_allocated -= sys.getsizeof(val)

        for val in self.allocated:
            val._gc_mark = False

    def stats(self) -> dict:
        return {
            "total_allocated": self.total_allocated,
            "current_live": len(self.allocated),
            "gc_count": self.gc_count,
            "bytes_allocated": self.bytes_allocated,
        }
