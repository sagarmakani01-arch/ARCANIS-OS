from .ast import *
from .errors import SemanticError

BUILTIN_NAMES = {
    "print", "len", "range", "int", "float", "str", "type", "input",
    "isinstance", "sleep", "abs", "max", "min", "sum",
    "true", "false", "none",
}

class SemanticAnalyzer:
    def __init__(self):
        self.scopes = [set(BUILTIN_NAMES)]
        self.current_func = None
        self.loop_depth = 0

    def _error(self, msg, node):
        raise SemanticError(msg, node.line, node.column)

    def _push_scope(self):
        self.scopes.append(set())

    def _pop_scope(self):
        self.scopes.pop()

    def _declare(self, name, node):
        self.scopes[-1].add(name)

    def _resolve(self, name, node):
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        self._error(f"Undefined variable '{name}'", node)

    def visit(self, node):
        method = f"visit_{type(node).__name__}"
        visitor = getattr(self, method, self._generic_visit)
        return visitor(node)

    def _generic_visit(self, node):
        for attr in dir(node):
            val = getattr(node, attr)
            if isinstance(val, Node):
                self.visit(val)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, Node):
                        self.visit(item)
                    elif isinstance(item, tuple):
                        for sub in item:
                            if isinstance(sub, Node):
                                self.visit(sub)

    def visit_Program(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Literal(self, node):
        pass

    def visit_Identifier(self, node):
        self._resolve(node.name, node)

    def visit_BinaryOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node):
        self.visit(node.operand)

    def visit_Assign(self, node):
        self.visit(node.value)
        if isinstance(node.target, Identifier):
            self._declare(node.target.name, node.target)
        else:
            self.visit(node.target)

    def visit_If(self, node):
        self.visit(node.condition)
        for stmt in node.body:
            self.visit(stmt)
        for cond, body in node.elifs:
            self.visit(cond)
            for stmt in body:
                self.visit(stmt)
        if node.else_body:
            for stmt in node.else_body:
                self.visit(stmt)

    def visit_While(self, node):
        self.visit(node.condition)
        self.loop_depth += 1
        for stmt in node.body:
            self.visit(stmt)
        self.loop_depth -= 1

    def visit_For(self, node):
        self.visit(node.iterable)
        self._declare(node.target.name, node.target)
        self.loop_depth += 1
        for stmt in node.body:
            self.visit(stmt)
        self.loop_depth -= 1

    def visit_FunctionDef(self, node):
        self._declare(node.name, node)
        old_func = self.current_func
        self.current_func = node.name
        self._push_scope()
        for param in node.params:
            self._declare(param, node)
        for stmt in node.body:
            self.visit(stmt)
        self._pop_scope()
        self.current_func = old_func

    def visit_Return(self, node):
        if self.current_func is None:
            self._error("'return' outside function", node)
        if node.value:
            self.visit(node.value)

    def visit_Break(self, node):
        if self.loop_depth == 0:
            self._error("'break' outside loop", node)

    def visit_Continue(self, node):
        if self.loop_depth == 0:
            self._error("'continue' outside loop", node)

    def visit_ClassDef(self, node):
        self._declare(node.name, node)
        self._push_scope()
        self._declare("self", node)
        for stmt in node.body:
            if isinstance(stmt, FunctionDef):
                self.visit_FunctionDef(stmt)
            else:
                self.visit(stmt)
        self._pop_scope()

    def visit_Call(self, node):
        self.visit(node.func)
        for arg in node.args:
            self.visit(arg)

    def visit_Subscript(self, node):
        self.visit(node.obj)
        self.visit(node.index)

    def visit_MemberAccess(self, node):
        self.visit(node.obj)

    def visit_ListLiteral(self, node):
        for elem in node.elements:
            self.visit(elem)

    def visit_MapLiteral(self, node):
        for key, val in node.pairs:
            self.visit(key)
            self.visit(val)

    def visit_Import(self, node):
        pass

    def visit_FromImport(self, node):
        pass

    def visit_TryCatch(self, node):
        for stmt in node.try_body:
            self.visit(stmt)
        self._declare(node.catch_var, node)
        for stmt in node.catch_body:
            self.visit(stmt)

    def visit_Raise(self, node):
        if node.expr:
            self.visit(node.expr)

    def visit_Await(self, node):
        self.visit(node.expr)

    def visit_Pass(self, node):
        pass
