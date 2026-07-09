class Node:
    def __init__(self, line=None, column=None):
        self.line = line
        self.column = column

class Program(Node):
    def __init__(self, statements):
        super().__init__()
        self.statements = statements

class Literal(Node):
    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

class Identifier(Node):
    def __init__(self, name, line=None, column=None):
        super().__init__(line, column)
        self.name = name

class BinaryOp(Node):
    def __init__(self, left, op, right, line=None, column=None):
        super().__init__(line, column)
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(Node):
    def __init__(self, op, operand, line=None, column=None):
        super().__init__(line, column)
        self.op = op
        self.operand = operand

class Assign(Node):
    def __init__(self, target, value, op='=', line=None, column=None):
        super().__init__(line, column)
        self.target = target
        self.value = value
        self.op = op

class If(Node):
    def __init__(self, condition, body, elifs=None, else_body=None, line=None, column=None):
        super().__init__(line, column)
        self.condition = condition
        self.body = body
        self.elifs = elifs or []
        self.else_body = else_body

class While(Node):
    def __init__(self, condition, body, line=None, column=None):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

class For(Node):
    def __init__(self, target, iterable, body, line=None, column=None):
        super().__init__(line, column)
        self.target = target
        self.iterable = iterable
        self.body = body

class FunctionDef(Node):
    def __init__(self, name, params, body, is_async=False, line=None, column=None):
        super().__init__(line, column)
        self.name = name
        self.params = params
        self.body = body
        self.is_async = is_async

class Return(Node):
    def __init__(self, value=None, line=None, column=None):
        super().__init__(line, column)
        self.value = value

class Break(Node):
    def __init__(self, line=None, column=None):
        super().__init__(line, column)

class Continue(Node):
    def __init__(self, line=None, column=None):
        super().__init__(line, column)

class ClassDef(Node):
    def __init__(self, name, base_classes, body, line=None, column=None):
        super().__init__(line, column)
        self.name = name
        self.base_classes = base_classes
        self.body = body

class Call(Node):
    def __init__(self, func, args, line=None, column=None):
        super().__init__(line, column)
        self.func = func
        self.args = args

class Subscript(Node):
    def __init__(self, obj, index, line=None, column=None):
        super().__init__(line, column)
        self.obj = obj
        self.index = index

class MemberAccess(Node):
    def __init__(self, obj, member, line=None, column=None):
        super().__init__(line, column)
        self.obj = obj
        self.member = member

class ListLiteral(Node):
    def __init__(self, elements, line=None, column=None):
        super().__init__(line, column)
        self.elements = elements

class MapLiteral(Node):
    def __init__(self, pairs, line=None, column=None):
        super().__init__(line, column)
        self.pairs = pairs

class Import(Node):
    def __init__(self, module, alias=None, line=None, column=None):
        super().__init__(line, column)
        self.module = module
        self.alias = alias

class FromImport(Node):
    def __init__(self, module, names, line=None, column=None):
        super().__init__(line, column)
        self.module = module
        self.names = names

class TryCatch(Node):
    def __init__(self, try_body, catch_var, catch_body, line=None, column=None):
        super().__init__(line, column)
        self.try_body = try_body
        self.catch_var = catch_var
        self.catch_body = catch_body

class Raise(Node):
    def __init__(self, expr=None, line=None, column=None):
        super().__init__(line, column)
        self.expr = expr

class Await(Node):
    def __init__(self, expr, line=None, column=None):
        super().__init__(line, column)
        self.expr = expr

class Pass(Node):
    def __init__(self, line=None, column=None):
        super().__init__(line, column)
