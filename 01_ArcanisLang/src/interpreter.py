import os
import sys
from .ast import *
from .errors import RuntimeError_
from .builtins import ArcanisBuiltin, STANDARD_ENV

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class BreakSignal(Exception):
    pass

class ContinueSignal(Exception):
    pass

class ErrorSignal(Exception):
    def __init__(self, value):
        self.value = value

class ArcanisFunction:
    def __init__(self, node, env, is_async=False):
        self.node = node
        self.env = env
        self.is_async = is_async

    def __repr__(self):
        return f"<fun {self.node.name}>"

class ArcanisClass:
    def __init__(self, name, base_classes, body, env):
        self.name = name
        self.base_classes = base_classes
        self.body = body
        self.env = env
        self.methods = {}
        for stmt in body:
            if isinstance(stmt, FunctionDef):
                self.methods[stmt.name] = ArcanisFunction(stmt, env)

    def __repr__(self):
        return f"<class {self.name}>"

class ArcanisInstance:
    def __init__(self, cls):
        self._class = cls
        self._attrs = {}

    def _resolve_method(self, name):
        visited = set()
        queue = [self._class]
        while queue:
            cls = queue.pop(0)
            if id(cls) in visited:
                continue
            visited.add(id(cls))
            if name in cls.methods:
                return cls.methods[name]
            queue.extend(cls.base_classes)
        return None

    def __getitem__(self, name):
        if name in self._attrs:
            return self._attrs[name]
        method = self._resolve_method(name)
        if method is not None:
            return method
        raise RuntimeError_(f"Instance of '{self._class.name}' has no attribute '{name}'")

    def __setitem__(self, name, value):
        self._attrs[name] = value

    def __repr__(self):
        return f"<instance of {self._class.name}>"

class BoundMethod:
    def __init__(self, func, instance, interp):
        self.func = func
        self.instance = instance
        self.interp = interp

    def __call__(self, *args):
        env = dict(self.func.env)
        env["self"] = self.instance
        params = self.func.node.params
        if params and params[0] == "self":
            params = params[1:]
        for p, a in zip(params, args):
            env[p] = a
        self.interp.env_stack.append(env)
        try:
            for stmt in self.func.node.body:
                self.interp.visit(stmt)
            return None
        except ReturnSignal as rs:
            return rs.value
        finally:
            self.interp.env_stack.pop()

    def __repr__(self):
        return f"<bound method {self.func.node.name}>"

class Interpreter:
    def __init__(self, env=None):
        self.env_stack = [env or {}]
        self.module_cache = {}

    @property
    def globals(self):
        return self.env_stack[0]

    @globals.setter
    def globals(self, val):
        self.env_stack[0] = val

    def visit(self, node):
        method = f"visit_{type(node).__name__}"
        visitor = getattr(self, method, self._generic_visit)
        return visitor(node)

    def _generic_visit(self, node):
        pass

    def _current_env(self):
        return self.env_stack[-1]

    def _get_var(self, name):
        for env in reversed(self.env_stack):
            if name in env:
                return env[name]
        raise RuntimeError_(f"Undefined variable '{name}'")

    def _set_var(self, name, value):
        for env in reversed(self.env_stack):
            if name in env:
                env[name] = value
                return
        self._current_env()[name] = value

    def visit_Program(self, node):
        result = None
        for stmt in node.statements:
            result = self.visit(stmt)
        return result

    def visit_Literal(self, node):
        return node.value

    def visit_Identifier(self, node):
        return self._get_var(node.name)

    def visit_BinaryOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if op == '+':
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        if op == '-': return left - right
        if op == '*': return left * right
        if op == '/':
            if right == 0:
                raise RuntimeError_("Division by zero", node.line, node.column)
            return left / right
        if op == '%': return left % right
        if op == '**': return left ** right
        if op == '==': return left == right
        if op == '!=': return left != right
        if op == '<': return left < right
        if op == '>': return left > right
        if op == '<=': return left <= right
        if op == '>=': return left >= right
        if op == 'and': return left and right
        if op == 'or': return left or right
        raise RuntimeError_(f"Unknown operator '{op}'", node.line, node.column)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if node.op == '-':
            return -operand
        if node.op == '+':
            return +operand
        if node.op == 'not':
            return not operand
        raise RuntimeError_(f"Unknown unary operator '{node.op}'", node.line, node.column)

    def visit_Assign(self, node):
        value = self.visit(node.value)
        target = node.target
        if isinstance(target, Identifier):
            self._set_var(target.name, value)
        elif isinstance(target, Subscript):
            obj = self.visit(target.obj)
            idx = self.visit(target.index)
            obj[idx] = value
        elif isinstance(target, MemberAccess):
            obj = self.visit(target.obj)
            obj[target.member] = value
        return value

    def visit_If(self, node):
        cond = self.visit(node.condition)
        if cond:
            for stmt in node.body:
                self.visit(stmt)
            return
        for elif_cond, elif_body in node.elifs:
            if self.visit(elif_cond):
                for stmt in elif_body:
                    self.visit(stmt)
                return
        if node.else_body:
            for stmt in node.else_body:
                self.visit(stmt)

    def visit_While(self, node):
        while self.visit(node.condition):
            try:
                for stmt in node.body:
                    try:
                        self.visit(stmt)
                    except ContinueSignal:
                        break
                    except BreakSignal:
                        raise BreakSignal()
            except BreakSignal:
                break

    def visit_For(self, node):
        iterable = self.visit(node.iterable)
        for item in iterable:
            self._set_var(node.target.name, item)
            try:
                for stmt in node.body:
                    try:
                        self.visit(stmt)
                    except ContinueSignal:
                        break
                    except BreakSignal:
                        raise BreakSignal()
            except BreakSignal:
                break

    def visit_FunctionDef(self, node):
        func = ArcanisFunction(node, self._current_env(), node.is_async)
        self._set_var(node.name, func)
        return func

    def visit_Return(self, node):
        value = self.visit(node.value) if node.value else None
        raise ReturnSignal(value)

    def visit_Break(self, node):
        raise BreakSignal()

    def visit_Continue(self, node):
        raise ContinueSignal()

    def visit_ClassDef(self, node):
        base_classes = []
        for name in node.base_classes:
            cls = self._get_var(name)
            if cls is None:
                raise RuntimeError_(f"Class '{node.name}' inherits from unknown class '{name}'")
            base_classes.append(cls)
        cls = ArcanisClass(node.name, base_classes, node.body, self._current_env())
        self._set_var(node.name, cls)
        return cls

    def visit_Call(self, node):
        func = self.visit(node.func)
        args = [self.visit(a) for a in node.args]
        if isinstance(func, ArcanisBuiltin):
            return func(*args)
        if isinstance(func, ArcanisFunction):
            new_env = dict(func.env)
            for param, arg in zip(func.node.params, args):
                new_env[param] = arg
            self.env_stack.append(new_env)
            try:
                for stmt in func.node.body:
                    self.visit(stmt)
                return None
            except ReturnSignal as rs:
                return rs.value
            finally:
                self.env_stack.pop()
        if isinstance(func, ArcanisClass):
            instance = ArcanisInstance(func)
            if 'init' in func.methods:
                init_func = func.methods['init']
                new_env = dict(init_func.env)
                new_env['self'] = instance
                for p, a in zip(init_func.node.params[1:], args):
                    new_env[p] = a
                self.env_stack.append(new_env)
                try:
                    for stmt in init_func.node.body:
                        self.visit(stmt)
                except ReturnSignal:
                    pass
                finally:
                    self.env_stack.pop()
            return instance
        if isinstance(func, BoundMethod):
            return func(*args)
        if callable(func):
            return func(*args)
        raise RuntimeError_(f"Cannot call {type(func).__name__}", node.line, node.column)

    def visit_Subscript(self, node):
        obj = self.visit(node.obj)
        idx = self.visit(node.index)
        return obj[idx]

    def visit_MemberAccess(self, node):
        obj = self.visit(node.obj)
        if isinstance(obj, ArcanisInstance):
            val = obj[node.member]
            if isinstance(val, ArcanisFunction):
                return BoundMethod(val, obj, self)
            return val
        if isinstance(obj, ArcanisClass):
            return obj[node.member]
        if isinstance(obj, dict):
            return obj[node.member]
        raise RuntimeError_(f"'{type(obj).__name__}' has no attribute '{node.member}'",
                           node.line, node.column)

    def visit_ListLiteral(self, node):
        return [self.visit(e) for e in node.elements]

    def visit_MapLiteral(self, node):
        return {self.visit(k): self.visit(v) for k, v in node.pairs}

    def visit_Import(self, node):
        module_name = node.module
        alias = node.alias or module_name
        if module_name in self.module_cache:
            self._set_var(alias, self.module_cache[module_name])
            return
        module = self._load_module(module_name)
        self.module_cache[module_name] = module
        self._set_var(alias, module)

    def visit_FromImport(self, node):
        module_name = node.module
        if module_name not in self.module_cache:
            module = self._load_module(module_name)
            self.module_cache[module_name] = module
        module = self.module_cache[module_name]
        for name, alias in node.names:
            target = alias or name
            if isinstance(module, dict) and name in module:
                self._set_var(target, module[name])
            else:
                self._set_var(target, module)

    def _load_module(self, module_name):
        search_paths = [
            os.path.join(os.getcwd(), module_name + ".arc"),
            os.path.join(os.getcwd(), module_name, "__init__.arc"),
        ]
        for path in search_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    source = f.read()
                from .lexer import Lexer
                from .parser import Parser
                from .semantic import SemanticAnalyzer
                lexer = Lexer(source, path)
                parser = Parser(lexer.tokens, path)
                ast = parser.parse()
                analyzer = SemanticAnalyzer()
                analyzer.visit(ast)
                mod_env = dict(self.globals)
                interp = Interpreter(mod_env)
                interp.module_cache = self.module_cache
                interp.visit(ast)
                return mod_env
        raise RuntimeError_(f"Module '{module_name}' not found")

    def visit_TryCatch(self, node):
        try:
            for stmt in node.try_body:
                self.visit(stmt)
        except (RuntimeError_, ErrorSignal) as e:
            err_msg = str(e)
            self._set_var(node.catch_var, err_msg)
            for stmt in node.catch_body:
                self.visit(stmt)

    def visit_Raise(self, node):
        value = self.visit(node.expr) if node.expr else RuntimeError_("Error raised")
        if isinstance(value, str):
            raise ErrorSignal(value)
        raise ErrorSignal(str(value))

    def visit_Await(self, node):
        coro = self.visit(node.expr)
        if hasattr(coro, '__next__'):
            try:
                while True:
                    next(coro)
            except StopIteration as e:
                return e.value if hasattr(e, 'value') else None
        return coro

    def visit_Pass(self, node):
        pass
