import time as _time
import math as _math

class ArcanisBuiltin:
    def __init__(self, name, func, arity=None):
        self.name = name
        self.func = func
        self.arity = arity

    def __call__(self, *args):
        return self.func(*args)

    def __repr__(self):
        return f"<builtin {self.name}>"


def _print(*args):
    print(*args)
    return None

def _len(obj):
    if isinstance(obj, (list, str, dict)):
        return len(obj)
    raise TypeError(f"len() not supported for {type(obj).__name__}")

def _range(*args):
    if len(args) == 1:
        return list(range(args[0]))
    elif len(args) == 2:
        return list(range(args[0], args[1]))
    elif len(args) == 3:
        return list(range(args[0], args[1], args[2]))
    raise TypeError(f"range() takes 1-3 arguments ({len(args)} given)")

def _int(x):
    return int(x)

def _float(x):
    return float(x)

def _str(x):
    return str(x)

def _type(x):
    if isinstance(x, ArcanisBuiltin):
        return "builtin"
    return type(x).__name__

def _input(prompt=""):
    return input(prompt)

def _isinstance(obj, cls_name):
    if hasattr(obj, '_class'):
        return obj._class.__name__ == cls_name
    return False

def _sleep(secs):
    _time.sleep(secs)
    return None

def _abs(x):
    return abs(x)

def _max(*args):
    return max(args)

def _min(*args):
    return min(args)

def _sum(iterable):
    return sum(iterable)

STANDARD_BUILTINS = {
    "print": ArcanisBuiltin("print", _print),
    "len": ArcanisBuiltin("len", _len, 1),
    "range": ArcanisBuiltin("range", _range),
    "int": ArcanisBuiltin("int", _int, 1),
    "float": ArcanisBuiltin("float", _float, 1),
    "str": ArcanisBuiltin("str", _str, 1),
    "type": ArcanisBuiltin("type", _type, 1),
    "input": ArcanisBuiltin("input", _input),
    "isinstance": ArcanisBuiltin("isinstance", _isinstance, 2),
    "sleep": ArcanisBuiltin("sleep", _sleep),
    "abs": ArcanisBuiltin("abs", _abs, 1),
    "max": ArcanisBuiltin("max", _max),
    "min": ArcanisBuiltin("min", _min),
    "sum": ArcanisBuiltin("sum", _sum, 1),
    "true": True,
    "false": False,
    "none": None,
}

STANDARD_ENV = dict(STANDARD_BUILTINS)
