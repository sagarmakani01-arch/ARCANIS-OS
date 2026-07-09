from typing import List, Optional, Any
import random
import math

from lexer.token import TokenType
from parser.ast import *
from .values import *
from .environment import Environment


class ReturnException(Exception):
    def __init__(self, value: RuntimeValue):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class InterpreterError(Exception):
    def __init__(self, message: str, pos: Position = None):
        self.pos = pos
        pos_str = f"line {pos.line}:{pos.column}: " if pos else ""
        super().__init__(f"{pos_str}{message}")


class Interpreter:
    def __init__(self):
        self.env = Environment()
        self._init_builtins()

    def _init_builtins(self):
        env = self.env
        env.define("print", BuiltinFunction("print", 1, lambda a: (print(str(a[0])), NIL)[1]))
        env.define("println", BuiltinFunction("println", 1, lambda a: (print(str(a[0])), NIL)[1]))
        env.define("int", BuiltinFunction("int", 1, lambda a: self._to_int(a[0])))
        env.define("float", BuiltinFunction("float", 1, lambda a: self._to_float(a[0])))
        env.define("str", BuiltinFunction("str", 1, lambda a: StringValue(str(a[0]))))
        env.define("cosine_similarity", BuiltinFunction("cosine_similarity", 2, self._cosine_sim))
        env.define("semantic_search", BuiltinFunction("semantic_search", 3, self._semantic_search))
        env.define("token_count", BuiltinFunction("token_count", 1, lambda a: IntValue(len(str(a[0]).split()))))
        env.define("read_line", BuiltinFunction("read_line", 0, lambda a: StringValue(input())))
        env.define("read_file", BuiltinFunction("read_file", 1, self._read_file))
        env.define("write_file", BuiltinFunction("write_file", 2, self._write_file))
        env.define("sleep", BuiltinFunction("sleep", 1, lambda a: NIL))
        for name in ("sin", "cos", "tan", "sqrt", "abs", "floor", "ceil", "round"):
            env.define(name, BuiltinFunction(name, 1, lambda a, n=name: self._math_op(n, a[0])))
        env.define("random", BuiltinFunction("random", 0, lambda a: FloatValue(random.random())))
        env.define("pi", FloatValue(math.pi))
        env.define("e", FloatValue(math.e))

    def _to_int(self, v):
        if isinstance(v, IntValue):
            return IntValue(v.value)
        if isinstance(v, FloatValue):
            return IntValue(int(v.value))
        if isinstance(v, StringValue):
            return IntValue(int(v.value))
        if isinstance(v, BoolValue):
            return IntValue(1 if v.value else 0)
        return IntValue(0)

    def _to_float(self, v):
        if isinstance(v, FloatValue):
            return FloatValue(v.value)
        if isinstance(v, IntValue):
            return FloatValue(float(v.value))
        if isinstance(v, StringValue):
            return FloatValue(float(v.value))
        return FloatValue(0.0)

    def _cosine_sim(self, args):
        a, b = args
        if isinstance(a, EmbeddingValue) and isinstance(b, EmbeddingValue):
            dot = sum(x * y for x, y in zip(a.data, b.data))
            na = math.sqrt(sum(x * x for x in a.data))
            nb = math.sqrt(sum(x * x for x in b.data))
            if na == 0 or nb == 0:
                return FloatValue(0.0)
            return FloatValue(dot / (na * nb))
        return FloatValue(0.0)

    def _semantic_search(self, args):
        query, docs, k = args
        return ArrayValue([])

    def _read_file(self, args):
        path = str(args[0])
        try:
            with open(path, "r", encoding="utf-8") as f:
                return ResultValue(True, StringValue(f.read()))
        except Exception as e:
            return ResultValue(False, StringValue(str(e)))

    def _write_file(self, args):
        path, content = str(args[0]), str(args[1])
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return ResultValue(True, NIL)
        except Exception as e:
            return ResultValue(False, StringValue(str(e)))

    def _math_op(self, name, v):
        val = v.value if isinstance(v, (IntValue, FloatValue)) else 0
        val = float(val)
        ops = {
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "sqrt": math.sqrt, "abs": abs,
            "floor": math.floor, "ceil": math.ceil, "round": round,
        }
        return FloatValue(ops[name](val))

    def interpret(self, program: Program):
        try:
            for stmt in program.statements:
                self.exec_stmt(stmt)
        except ReturnException as e:
            return e.value
        return NIL

    def exec_stmt(self, stmt: Stmt, env: Environment = None):
        if env is None:
            env = self.env

        if isinstance(stmt, ExpressionStmt):
            self.eval_expr(stmt.expression, env)
        elif isinstance(stmt, LetStmt):
            value = self.eval_expr(stmt.value, env) if stmt.value else NIL
            env.define(stmt.name, value)
        elif isinstance(stmt, ConstStmt):
            value = self.eval_expr(stmt.value, env) if stmt.value else NIL
            env.define(stmt.name, value)
        elif isinstance(stmt, FnDecl):
            fn = FunctionValue(stmt.name, stmt.params, stmt.body, env)
            env.define(stmt.name, fn)
        elif isinstance(stmt, ReturnStmt):
            value = self.eval_expr(stmt.value, env) if stmt.value else NIL
            raise ReturnException(value)
        elif isinstance(stmt, StructDecl):
            field_names = [f.name for f in stmt.fields]
            env.define(stmt.name, ("__struct__", stmt.name, field_names))
        elif isinstance(stmt, EnumDecl):
            env.define(stmt.name, StringValue(f"<enum {stmt.name}>"))
        elif isinstance(stmt, TraitDecl):
            env.define(stmt.name, StringValue(f"<trait {stmt.name}>"))
        elif isinstance(stmt, ImplDecl):
            pass
        elif isinstance(stmt, AgentDecl):
            methods = {m.name: FunctionValue(m.name, m.params, m.body, env) for m in stmt.methods}
            agent = AgentValue(stmt.name, stmt.role, stmt.model, methods)
            env.define(stmt.name, agent)
        elif isinstance(stmt, ForStmt):
            self._exec_for(stmt, env)
        elif isinstance(stmt, WhileStmt):
            self._exec_while(stmt, env)
        elif isinstance(stmt, BreakStmt):
            raise BreakException()
        elif isinstance(stmt, ContinueStmt):
            raise ContinueException()
        elif isinstance(stmt, ThrowStmt):
            val = self.eval_expr(stmt.value, env)
            raise InterpreterError(f"Throw: {val}")
        elif isinstance(stmt, DeferStmt):
            pass
        elif isinstance(stmt, PassStmt):
            pass
        elif isinstance(stmt, ImportStmt):
            pass
        elif isinstance(stmt, UseStmt):
            pass
        elif isinstance(stmt, TypeAlias):
            pass
        elif isinstance(stmt, ModDecl):
            pass

    def _exec_for(self, stmt: ForStmt, env: Environment):
        iterable = self.eval_expr(stmt.iterable, env)
        items = []
        if isinstance(iterable, ArrayValue):
            items = iterable.elements
        elif isinstance(iterable, StringValue):
            items = [StringValue(c) for c in iterable.value]
        elif isinstance(iterable, RangeValue):
            items = iterable.elements

        for item in items:
            body_env = env.enter_scope()
            if isinstance(stmt.pattern, IdentifierExpr):
                body_env.define(stmt.pattern.name, item)
            try:
                for s in stmt.body.statements:
                    self.exec_stmt(s, body_env)
            except BreakException:
                break
            except ContinueException:
                continue

    def _exec_while(self, stmt: WhileStmt, env: Environment):
        while True:
            cond = self.eval_expr(stmt.condition, env)
            if not self._is_truthy(cond):
                break
            try:
                body_env = env.enter_scope()
                for s in stmt.body.statements:
                    self.exec_stmt(s, body_env)
            except BreakException:
                break
            except ContinueException:
                continue

    def _is_truthy(self, v: RuntimeValue) -> bool:
        if isinstance(v, BoolValue):
            return v.value
        if isinstance(v, NilValue):
            return False
        if isinstance(v, IntValue):
            return v.value != 0
        if isinstance(v, FloatValue):
            return v.value != 0.0
        if isinstance(v, StringValue):
            return len(v.value) > 0
        return True

    def eval_expr(self, expr: Expr, env: Environment = None) -> RuntimeValue:
        if env is None:
            env = self.env

        if isinstance(expr, LiteralExpr):
            return self._eval_literal(expr)
        elif isinstance(expr, IdentifierExpr):
            return self._eval_identifier(expr, env)
        elif isinstance(expr, BinaryExpr):
            return self._eval_binary(expr, env)
        elif isinstance(expr, UnaryExpr):
            return self._eval_unary(expr, env)
        elif isinstance(expr, CallExpr):
            return self._eval_call(expr, env)
        elif isinstance(expr, IndexExpr):
            return self._eval_index(expr, env)
        elif isinstance(expr, AttributeExpr):
            return self._eval_attribute(expr, env)
        elif isinstance(expr, IfExpr):
            return self._eval_if(expr, env)
        elif isinstance(expr, MatchExpr):
            return self._eval_match(expr, env)
        elif isinstance(expr, BlockExpr):
            return self._eval_block(expr, env)
        elif isinstance(expr, ClosureExpr):
            return self._eval_closure(expr, env)
        elif isinstance(expr, ListExpr):
            return ArrayValue([self.eval_expr(e, env) for e in expr.elements])
        elif isinstance(expr, MapExpr):
            return self._eval_map(expr, env)
        elif isinstance(expr, AIExpr):
            return self._eval_ai(expr, env)
        elif isinstance(expr, EmbedExpr):
            return self._eval_embed(expr, env)
        elif isinstance(expr, MemExpr):
            return MemoryValue()
        elif isinstance(expr, AsyncExpr):
            return self.eval_expr(expr.expression, env)
        elif isinstance(expr, AwaitExpr):
            return self.eval_expr(expr.expression, env)
        elif isinstance(expr, TryExpr):
            return self._eval_try(expr, env)
        elif isinstance(expr, RangeExpr):
            return self._eval_range(expr, env)
        elif isinstance(expr, StructExpr):
            return self._eval_struct_init(expr, env)
        elif isinstance(expr, PromptClause):
            return self.eval_expr(expr.expression, env)
        elif isinstance(expr, ModelClause):
            return self.eval_expr(expr.expression, env)
        return NIL

    def _eval_literal(self, expr: LiteralExpr) -> RuntimeValue:
        if isinstance(expr.value, bool):
            return BoolValue(expr.value)
        if isinstance(expr.value, int):
            return IntValue(expr.value)
        if isinstance(expr.value, float):
            return FloatValue(expr.value)
        if isinstance(expr.value, str):
            return StringValue(expr.value)
        if expr.value is None:
            return NIL
        return NIL

    def _eval_identifier(self, expr: IdentifierExpr, env: Environment) -> RuntimeValue:
        return env.get(expr.name)

    def _eval_binary(self, expr: BinaryExpr, env: Environment) -> RuntimeValue:
        left = self.eval_expr(expr.left, env)
        right = self.eval_expr(expr.right, env)
        op = expr.op

        if op == "=":
            if isinstance(expr.left, IdentifierExpr):
                env.assign(expr.left.name, right)
                return right
            if isinstance(expr.left, IndexExpr):
                target = self.eval_expr(expr.left.target, env)
                index = self.eval_expr(expr.left.index, env)
                if isinstance(target, ArrayValue) and isinstance(index, IntValue):
                    target.elements[index.value] = right
                return right
            if isinstance(expr.left, AttributeExpr):
                obj = self.eval_expr(expr.left.target, env)
                if isinstance(obj, StructValue) and expr.left.attr in obj.fields:
                    obj.fields[expr.left.attr] = right
                return right
            return right
        if op == "+=":
            val = self._add(left, right)
            if isinstance(expr.left, IdentifierExpr):
                env.assign(expr.left.name, val)
            return val
        if op == "-=":
            val = self._sub(left, right)
            if isinstance(expr.left, IdentifierExpr):
                env.assign(expr.left.name, val)
            return val
        if op == "*=":
            val = self._mul(left, right)
            if isinstance(expr.left, IdentifierExpr):
                env.assign(expr.left.name, val)
            return val
        if op == "/=":
            val = self._div(left, right)
            if isinstance(expr.left, IdentifierExpr):
                env.assign(expr.left.name, val)
            return val

        if op == "+":
            return self._add(left, right)
        if op == "-":
            return self._sub(left, right)
        if op == "*":
            return self._mul(left, right)
        if op == "/":
            return self._div(left, right)
        if op == "%":
            if isinstance(left, IntValue) and isinstance(right, IntValue):
                return IntValue(left.value % right.value)
            return IntValue(0)
        if op == "==":
            return BoolValue(self._eq(left, right))
        if op == "!=":
            return BoolValue(not self._eq(left, right))
        if op == "<":
            return BoolValue(self._cmp(left, right) < 0)
        if op == ">":
            return BoolValue(self._cmp(left, right) > 0)
        if op == "<=":
            return BoolValue(self._cmp(left, right) <= 0)
        if op == ">=":
            return BoolValue(self._cmp(left, right) >= 0)
        if op == "and":
            return BoolValue(self._is_truthy(left) and self._is_truthy(right))
        if op == "or":
            return BoolValue(self._is_truthy(left) or self._is_truthy(right))
        if op == "++":
            return StringValue(str(left) + str(right))
        if op == "??":
            if isinstance(left, NilValue):
                return right
            return left
        if op == "..":
            start = left.value if isinstance(left, IntValue) else 0
            end = right.value if isinstance(right, IntValue) else 0
            return ArrayValue([IntValue(i) for i in range(start, end)])
        if op == "..=":
            start = left.value if isinstance(left, IntValue) else 0
            end = right.value if isinstance(right, IntValue) else 0
            return ArrayValue([IntValue(i) for i in range(start, end + 1)])

        return NIL

    def _add(self, a, b):
        if isinstance(a, IntValue) and isinstance(b, IntValue):
            return IntValue(a.value + b.value)
        if isinstance(a, (IntValue, FloatValue)) and isinstance(b, (IntValue, FloatValue)):
            return FloatValue(float(a.value) + float(b.value))
        if isinstance(a, StringValue) or isinstance(b, StringValue):
            return StringValue(str(a) + str(b))
        if isinstance(a, ArrayValue) and isinstance(b, ArrayValue):
            return ArrayValue(a.elements + b.elements)
        return NIL

    def _sub(self, a, b):
        if isinstance(a, IntValue) and isinstance(b, IntValue):
            return IntValue(a.value - b.value)
        return FloatValue(float(a.value) - float(b.value))

    def _mul(self, a, b):
        if isinstance(a, IntValue) and isinstance(b, IntValue):
            return IntValue(a.value * b.value)
        return FloatValue(float(a.value) * float(b.value))

    def _div(self, a, b):
        if isinstance(a, IntValue) and isinstance(b, IntValue):
            if b.value == 0:
                return NIL
            return IntValue(a.value // b.value)
        bv = float(b.value)
        if bv == 0:
            return NIL
        return FloatValue(float(a.value) / bv)

    def _eq(self, a, b):
        if type(a) != type(b):
            return False
        if isinstance(a, (IntValue, FloatValue, BoolValue, StringValue)):
            return a.value == b.value
        if isinstance(a, NilValue):
            return True
        if isinstance(a, ArrayValue):
            if len(a.elements) != len(b.elements):
                return False
            return all(self._eq(x, y) for x, y in zip(a.elements, b.elements))
        return a is b

    def _cmp(self, a, b):
        if isinstance(a, (IntValue, FloatValue)) and isinstance(b, (IntValue, FloatValue)):
            av = a.value if isinstance(a, IntValue) else float(a.value)
            bv = b.value if isinstance(b, IntValue) else float(b.value)
            return -1 if av < bv else 1 if av > bv else 0
        if isinstance(a, StringValue) and isinstance(b, StringValue):
            return -1 if a.value < b.value else 1 if a.value > b.value else 0
        return 0

    def _eval_unary(self, expr: UnaryExpr, env: Environment) -> RuntimeValue:
        right = self.eval_expr(expr.right, env)
        if expr.op == "-":
            if isinstance(right, IntValue):
                return IntValue(-right.value)
            if isinstance(right, FloatValue):
                return FloatValue(-right.value)
            return NIL
        if expr.op == "!":
            return BoolValue(not self._is_truthy(right))
        if expr.op == "+":
            return right
        return NIL

    def _eval_call(self, expr: CallExpr, env: Environment) -> RuntimeValue:
        callee = self.eval_expr(expr.callee, env)
        args = [self.eval_expr(a, env) for a in expr.args]

        if isinstance(callee, BuiltinFunction):
            return callee.func(args)

        if isinstance(callee, FunctionValue):
            call_env = callee.closure.enter_scope() if callee.closure else Environment()
            for param, arg in zip(callee.params, args):
                call_env.define(param.name, arg)
            result = NIL
            try:
                for s in callee.body.statements:
                    if isinstance(s, ExpressionStmt):
                        result = self.eval_expr(s.expression, call_env)
                    else:
                        self.exec_stmt(s, call_env)
                        result = NIL
            except ReturnException as e:
                return e.value
            return result

        if isinstance(callee, AgentValue) and callee.methods:
            call_env = Environment()
            call_env.define("self", callee)
            for param, arg in zip(callee.params if hasattr(callee, 'params') else [], args):
                call_env.define(param.name, arg)
            return NIL

        if isinstance(callee, StructValue):
            return callee

        if isinstance(callee, tuple) and len(callee) == 3 and callee[0] == "__struct__":
            _, struct_name, field_names = callee
            fields = {}
            for i, fname in enumerate(field_names):
                fields[fname] = args[i] if i < len(args) else NIL
            return StructValue(struct_name, fields)

        return NIL

    def _eval_index(self, expr: IndexExpr, env: Environment) -> RuntimeValue:
        target = self.eval_expr(expr.target, env)
        index = self.eval_expr(expr.index, env)

        if isinstance(target, ArrayValue) and isinstance(index, IntValue):
            i = index.value
            if 0 <= i < len(target.elements):
                return target.elements[i]
            raise InterpreterError(f"Index {i} out of bounds for array of length {len(target.elements)}", expr.pos)

        if isinstance(target, TupleValue) and isinstance(index, IntValue):
            i = index.value
            if 0 <= i < len(target.elements):
                return target.elements[i]
            raise InterpreterError(f"Index {i} out of bounds for tuple of length {len(target.elements)}", expr.pos)

        if isinstance(target, StringValue) and isinstance(index, IntValue):
            i = index.value
            if 0 <= i < len(target.value):
                return StringValue(target.value[i])
            return StringValue("")

        if isinstance(target, ArrayValue) and isinstance(expr.index, RangeExpr):
            arr = target.elements
            sv = self.eval_expr(expr.index.start, env).value if expr.index.start else 0
            ev = self.eval_expr(expr.index.end, env).value if expr.index.end else len(arr)
            return ArrayValue(arr[sv:ev])

        if isinstance(expr.index, LiteralExpr) and expr.index.value is None:
            return target

        if isinstance(index, IntValue):
            return target.elements[index.value] if isinstance(target, ArrayValue) else NIL

        return NIL

    def _eval_attribute(self, expr: AttributeExpr, env: Environment) -> RuntimeValue:
        target = self.eval_expr(expr.target, env)

        if isinstance(target, StructValue) and expr.attr in target.fields:
            return target.fields[expr.attr]

        if isinstance(target, AgentValue) and expr.attr == "self":
            return target

        if isinstance(target, StringValue):
            if expr.attr == "len":
                return IntValue(len(target.value))
            if expr.attr in ("upper", "lower", "strip"):
                return BuiltinFunction(expr.attr, 0, lambda a, s=target: StringValue(getattr(s.value, expr.attr)()))
            if expr.attr == "split":
                return BuiltinFunction(expr.attr, 0, lambda a, s=target: ArrayValue([StringValue(x) for x in s.value.split()]))
            if expr.attr == "join":
                return BuiltinFunction(expr.attr, 1, lambda a, s=target: StringValue(str(a[0]).join(s.value)))
            if expr.attr == "starts_with":
                return BuiltinFunction(expr.attr, 1, lambda a, s=target: BoolValue(s.value.startswith(str(a[0]))))
            if expr.attr == "ends_with":
                return BuiltinFunction(expr.attr, 1, lambda a, s=target: BoolValue(s.value.endswith(str(a[0]))))
            if expr.attr == "contains":
                return BuiltinFunction(expr.attr, 1, lambda a, s=target: BoolValue(str(a[0]) in s.value))

        if isinstance(target, ArrayValue):
            if expr.attr == "len":
                return IntValue(len(target.elements))
            if expr.attr == "push":
                return BuiltinFunction("push", 1, lambda a, arr=target: (arr.elements.append(a[0]), NIL)[1])
            if expr.attr == "pop":
                return BuiltinFunction("pop", 0, lambda a, arr=target: arr.elements.pop() if arr.elements else NIL)
            if expr.attr == "sort":
                return BuiltinFunction("sort", 1, lambda a, arr=target: (arr.elements.sort(key=lambda x: float(x.value) if hasattr(x, 'value') else 0), arr)[1])

        if isinstance(target, AgentValue) and expr.attr in (target.methods or {}):
            return target.methods[expr.attr]

        if isinstance(target, TupleValue):
            if expr.attr.lstrip("-").lstrip("+").isdigit():
                idx = int(expr.attr)
                if 0 <= idx < len(target.elements):
                    return target.elements[idx]

        return NIL

    def _eval_if(self, expr: IfExpr, env: Environment) -> RuntimeValue:
        cond = self.eval_expr(expr.condition, env)
        if self._is_truthy(cond):
            block_env = env.enter_scope()
            try:
                for s in expr.then_branch.statements:
                    self.exec_stmt(s, block_env)
            except ReturnException:
                raise
            result = self._last_expr_value(expr.then_branch, block_env)
            return result
        elif expr.else_branch:
            block_env = env.enter_scope()
            try:
                for s in expr.else_branch.statements:
                    self.exec_stmt(s, block_env)
            except ReturnException:
                raise
            return self._last_expr_value(expr.else_branch, block_env)
        return NIL

    def _eval_match(self, expr: MatchExpr, env: Environment) -> RuntimeValue:
        value = self.eval_expr(expr.value, env)
        for arm in expr.arms:
            if isinstance(arm.pattern, IdentifierExpr) and arm.pattern.name == "_":
                return self.eval_expr(arm.body, env)
            pattern_val = self.eval_expr(arm.pattern, env)
            if self._eq(value, pattern_val):
                return self.eval_expr(arm.body, env)
        return NIL

    def _eval_block(self, expr: BlockExpr, env: Environment) -> RuntimeValue:
        block_env = env.enter_scope()
        result = NIL
        try:
            for s in expr.statements:
                if isinstance(s, ExpressionStmt):
                    result = self.eval_expr(s.expression, block_env)
                else:
                    self.exec_stmt(s, block_env)
                    result = NIL
        except ReturnException:
            raise
        return result

    def _eval_closure(self, expr: ClosureExpr, env: Environment) -> RuntimeValue:
        fn = FunctionValue("<closure>", expr.params, expr.body, env)
        return fn

    def _eval_map(self, expr: MapExpr, env: Environment) -> RuntimeValue:
        entries = {}
        for key, value in expr.entries:
            if key is not None:
                k = str(self.eval_expr(key, env))
            else:
                k = str(len(entries))
            v = self.eval_expr(value, env)
            entries[k] = v
        return MapValue(entries)

    def _eval_ai(self, expr: AIExpr, env: Environment) -> RuntimeValue:
        prompt_text = ""
        if expr.prompt:
            pv = self.eval_expr(expr.prompt.expression, env)
            prompt_text = str(pv)
        system_text = ""
        if expr.system:
            sv = self.eval_expr(expr.system.expression, env)
            system_text = str(sv)
        model_name = "arcanis-default"
        if expr.model:
            mv = self.eval_expr(expr.model.expression, env)
            model_name = str(mv)

        return StringValue(f"<AI response to: {prompt_text[:50]}>")

    def _eval_embed(self, expr: EmbedExpr, env: Environment) -> RuntimeValue:
        val = self.eval_expr(expr.expression, env)
        text = str(val)
        dims = min(4, max(1, len(text) // 10))
        random.seed(hash(text) % (2**31))
        data = [random.random() for _ in range(dims)]
        return EmbeddingValue(data)

    def _eval_try(self, expr: TryExpr, env: Environment) -> RuntimeValue:
        try:
            val = self.eval_expr(expr.expression, env)
            return val
        except Exception as e:
            if expr.force:
                return NIL
            return ResultValue(False, StringValue(str(e)))

    def _eval_range(self, expr: RangeExpr, env: Environment) -> RuntimeValue:
        start = self.eval_expr(expr.start, env)
        end = self.eval_expr(expr.end, env)
        sv = start.value if isinstance(start, IntValue) else 0
        ev = end.value if isinstance(end, IntValue) else 0
        return ArrayValue([IntValue(i) for i in range(sv, ev)])

    def _eval_struct_init(self, expr: StructExpr, env: Environment) -> RuntimeValue:
        fields = expr.fields if hasattr(expr, 'fields') and expr.fields else []
        field_vals = {}
        for f in fields:
            val = self.eval_expr(f.value, env) if hasattr(f, 'value') and f.value else NIL
            field_vals[f.name] = val
        return StructValue(expr.name, field_vals)

    def _last_expr_value(self, block: BlockExpr, env: Environment) -> RuntimeValue:
        result = NIL
        for s in block.statements:
            if isinstance(s, ExpressionStmt):
                result = self.eval_expr(s.expression, env)
        return result
