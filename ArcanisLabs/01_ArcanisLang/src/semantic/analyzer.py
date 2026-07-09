from typing import List, Optional, Any

from parser.ast import *
from .types import *
from .symbol_table import SymbolTable, SymbolKind, Symbol


class SemanticError(Exception):
    def __init__(self, message: str, pos: Position):
        self.message = message
        self.pos = pos
        super().__init__(f"line {pos.line}:{pos.column}: {message}")


class Analyzer:
    def __init__(self):
        self.symbols = SymbolTable()
        self.errors: List[SemanticError] = []
        self._init_builtins()

    def _init_builtins(self):
        sym = self.symbols
        # Print function
        sym.define("print", SymbolKind.BUILTIN,
                    FunctionType([TypeVariable()], NULL))
        sym.define("println", SymbolKind.BUILTIN,
                    FunctionType([TypeVariable()], NULL))
        # Type conversion
        sym.define("int", SymbolKind.BUILTIN,
                    FunctionType([TypeVariable()], I32))
        sym.define("float", SymbolKind.BUILTIN,
                    FunctionType([TypeVariable()], F64))
        sym.define("str", SymbolKind.BUILTIN,
                    FunctionType([TypeVariable()], STRING))
        # AI builtins
        sym.define("cosine_similarity", SymbolKind.BUILTIN,
                    FunctionType([NamedType("Embedding"), NamedType("Embedding")], F64))
        sym.define("semantic_search", SymbolKind.BUILTIN,
                    FunctionType([STRING, ArrayType(STRING), I32], ArrayType(TupleType([STRING, F64]))))
        sym.define("token_count", SymbolKind.BUILTIN,
                    FunctionType([STRING], I32))
        # IO builtins
        sym.define("read_line", SymbolKind.BUILTIN,
                    FunctionType([], STRING))
        sym.define("read_file", SymbolKind.BUILTIN,
                    FunctionType([STRING], ResultType(STRING, STRING)))
        sym.define("write_file", SymbolKind.BUILTIN,
                    FunctionType([STRING, STRING], ResultType(NULL, STRING)))
        # Time builtins
        sym.define("sleep", SymbolKind.BUILTIN,
                    FunctionType([I64], NULL))
        # Math builtins
        for name in ("sin", "cos", "tan", "sqrt", "abs", "floor", "ceil", "round"):
            sym.define(name, SymbolKind.BUILTIN, FunctionType([F64], F64))
        sym.define("random", SymbolKind.BUILTIN, FunctionType([], F64))
        # Constants
        sym.define("pi", SymbolKind.BUILTIN, F64)
        sym.define("e", SymbolKind.BUILTIN, F64)

    def analyze(self, program: Program):
        for stmt in program.statements:
            self.analyze_stmt(stmt)

        if self.errors:
            raise self.errors[0]
        return True

    def error(self, message: str, pos: Position):
        self.errors.append(SemanticError(message, pos))

    def analyze_stmt(self, stmt: Stmt):
        if isinstance(stmt, ExpressionStmt):
            self.analyze_expr(stmt.expression)
        elif isinstance(stmt, LetStmt):
            self.analyze_let(stmt)
        elif isinstance(stmt, ConstStmt):
            self.analyze_const(stmt)
        elif isinstance(stmt, FnDecl):
            self.analyze_fn_decl(stmt)
        elif isinstance(stmt, ReturnStmt):
            self.analyze_return(stmt)
        elif isinstance(stmt, StructDecl):
            self.analyze_struct(stmt)
        elif isinstance(stmt, EnumDecl):
            self.analyze_enum(stmt)
        elif isinstance(stmt, TraitDecl):
            self.analyze_trait(stmt)
        elif isinstance(stmt, ImplDecl):
            self.analyze_impl(stmt)
        elif isinstance(stmt, AgentDecl):
            self.analyze_agent(stmt)
        elif isinstance(stmt, ImportStmt):
            pass
        elif isinstance(stmt, UseStmt):
            pass
        elif isinstance(stmt, ForStmt):
            self.analyze_for(stmt)
        elif isinstance(stmt, WhileStmt):
            self.analyze_while(stmt)
        elif isinstance(stmt, BreakStmt):
            pass
        elif isinstance(stmt, ContinueStmt):
            pass
        elif isinstance(stmt, ThrowStmt):
            self.analyze_expr(stmt.value)
        elif isinstance(stmt, DeferStmt):
            self.analyze_expr(stmt.call)
        elif isinstance(stmt, PassStmt):
            pass
        elif isinstance(stmt, TypeAlias):
            self.symbols.define(stmt.name, SymbolKind.TYPE, NamedType(stmt.name))
        elif isinstance(stmt, ModDecl):
            pass

    def analyze_let(self, stmt: LetStmt):
        value_type = self.analyze_expr(stmt.value) if stmt.value else NULL
        declared_type = self.resolve_type(stmt.type_annotation) if stmt.type_annotation else value_type
        self.symbols.define(stmt.name, SymbolKind.VARIABLE, declared_type, stmt.mutable, stmt.pos)

    def analyze_const(self, stmt: ConstStmt):
        value_type = self.analyze_expr(stmt.value) if stmt.value else NULL
        declared_type = self.resolve_type(stmt.type_annotation) if stmt.type_annotation else value_type
        self.symbols.define(stmt.name, SymbolKind.VARIABLE, declared_type, False, stmt.pos)

    def analyze_fn_decl(self, stmt: FnDecl, is_method: bool = False):
        param_types = []
        self.symbols.enter_scope()

        if is_method:
            self.symbols.define("self", SymbolKind.PARAMETER, NamedType("Self"), False, stmt.pos)

        for param in stmt.params:
            ptype = NULL
            if param.type_annotation:
                ptype = self.resolve_type(param.type_annotation)
            param_types.append(ptype)
            self.symbols.define(param.name, SymbolKind.PARAMETER, ptype, False, param.pos)

        return_type = NULL
        if stmt.return_type:
            return_type = self.resolve_type(stmt.return_type)

        for s in stmt.body.statements:
            self.analyze_stmt(s)

        self.symbols.exit_scope()

        fn_type = FunctionType(param_types, return_type)
        self.symbols.define(stmt.name, SymbolKind.FUNCTION, fn_type, False, stmt.pos)

    def analyze_return(self, stmt: ReturnStmt):
        if stmt.value:
            self.analyze_expr(stmt.value)

    def analyze_struct(self, stmt: StructDecl):
        field_types = {}
        self.symbols.enter_scope()
        for f in stmt.fields:
            ftype = self.resolve_type(f.type_annotation) if f.type_annotation else TypeVariable()
            field_types[f.name] = ftype
            self.symbols.define(f.name, SymbolKind.VARIABLE, ftype, True, f.pos)
        self.symbols.exit_scope()

        self.symbols.define(stmt.name, SymbolKind.TYPE, NamedType(stmt.name), False, stmt.pos)

    def analyze_enum(self, stmt: EnumDecl):
        self.symbols.define(stmt.name, SymbolKind.TYPE, NamedType(stmt.name), False, stmt.pos)

    def analyze_trait(self, stmt: TraitDecl):
        self.symbols.define(stmt.name, SymbolKind.TRAIT, TraitType(stmt.name), False, stmt.pos)

    def analyze_impl(self, stmt: ImplDecl):
        for method in stmt.methods:
            self.analyze_fn_decl(method, is_method=True)

    def analyze_agent(self, stmt: AgentDecl):
        self.symbols.enter_scope()
        self.symbols.define("self", SymbolKind.PARAMETER, AgentType(stmt.name), False, stmt.pos)

        for tool in stmt.tools:
            param_types = []
            for p in tool.params:
                pt = self.resolve_type(p.type_annotation) if p.type_annotation else TypeVariable()
                param_types.append(pt)
            return_type = self.resolve_type(tool.return_type) if tool.return_type else NULL
            self.symbols.define(tool.name, SymbolKind.FUNCTION,
                                FunctionType(param_types, return_type), False, tool.pos)

        for method in stmt.methods:
            self.analyze_fn_decl(method, is_method=True)

        self.symbols.exit_scope()
        self.symbols.define(stmt.name, SymbolKind.AGENT, AgentType(stmt.name), False, stmt.pos)

    def analyze_for(self, stmt: ForStmt):
        iter_type = self.analyze_expr(stmt.iterable)
        self.symbols.enter_scope()
        elem_type = TypeVariable()
        if isinstance(iter_type, ArrayType):
            elem_type = iter_type.element_type
        if isinstance(stmt.pattern, IdentifierExpr):
            self.symbols.define(stmt.pattern.name, SymbolKind.VARIABLE, elem_type, False, stmt.pattern.pos)
        for s in stmt.body.statements:
            self.analyze_stmt(s)
        self.symbols.exit_scope()

    def analyze_while(self, stmt: WhileStmt):
        self.analyze_expr(stmt.condition)
        self.symbols.enter_scope()
        for s in stmt.body.statements:
            self.analyze_stmt(s)
        self.symbols.exit_scope()

    def analyze_expr(self, expr: Expr) -> Type:
        if isinstance(expr, LiteralExpr):
            return self._type_of_literal(expr)
        elif isinstance(expr, IdentifierExpr):
            return self._resolve_identifier(expr)
        elif isinstance(expr, BinaryExpr):
            return self._analyze_binary(expr)
        elif isinstance(expr, UnaryExpr):
            return self._analyze_unary(expr)
        elif isinstance(expr, CallExpr):
            return self._analyze_call(expr)
        elif isinstance(expr, IndexExpr):
            return self._analyze_index(expr)
        elif isinstance(expr, AttributeExpr):
            return self._analyze_attribute(expr)
        elif isinstance(expr, IfExpr):
            return self._analyze_if(expr)
        elif isinstance(expr, MatchExpr):
            return self._analyze_match(expr)
        elif isinstance(expr, BlockExpr):
            return self._analyze_block(expr)
        elif isinstance(expr, ClosureExpr):
            return self._analyze_closure(expr)
        elif isinstance(expr, ListExpr):
            return self._analyze_list(expr)
        elif isinstance(expr, MapExpr):
            return self._analyze_map(expr)
        elif isinstance(expr, AIExpr):
            return self._analyze_ai(expr)
        elif isinstance(expr, EmbedExpr):
            return self._analyze_embed(expr)
        elif isinstance(expr, MemExpr):
            return NamedType("Memory")
        elif isinstance(expr, PromptClause):
            return NamedType("Prompt")
        elif isinstance(expr, ModelClause):
            return NamedType("Model")
        elif isinstance(expr, AsyncExpr):
            return self.analyze_expr(expr.expression)
        elif isinstance(expr, AwaitExpr):
            return self.analyze_expr(expr.expression)
        elif isinstance(expr, TryExpr):
            inner = self.analyze_expr(expr.expression)
            return ResultType(inner, STRING) if not expr.force else inner
        elif isinstance(expr, RangeExpr):
            return ArrayType(I32)
        elif isinstance(expr, StructExpr):
            return NamedType(expr.name)
        return TypeVariable()

    def _type_of_literal(self, expr: LiteralExpr) -> Type:
        if isinstance(expr.value, bool):
            return BOOL
        elif isinstance(expr.value, int):
            return I32
        elif isinstance(expr.value, float):
            return F64
        elif isinstance(expr.value, str):
            return STRING
        elif expr.value is None:
            return NULL
        return TypeVariable()

    def _resolve_identifier(self, expr: IdentifierExpr) -> Type:
        sym = self.symbols.resolve(expr.name)
        if sym is None:
            self.error(f"Undefined variable '{expr.name}'", expr.pos)
            return TypeVariable()
        return sym.type

    def _analyze_binary(self, expr: BinaryExpr) -> Type:
        left = self.analyze_expr(expr.left)
        right = self.analyze_expr(expr.right)

        if expr.op in ("+", "-", "*", "/", "%"):
            if expr.op == "+" and left == STRING:
                return STRING
            if is_numeric(left) and is_numeric(right):
                return F64 if isinstance(left, PrimitiveType) and left.name.startswith("f") else left
            return left
        elif expr.op in ("==", "!=", "<", ">", "<=", ">="):
            return BOOL
        elif expr.op in ("and", "or"):
            return BOOL
        elif expr.op == "=":
            if isinstance(expr.left, IdentifierExpr):
                sym = self.symbols.resolve(expr.left.name)
                if sym and not sym.mutable:
                    self.error(f"Cannot assign to immutable variable '{expr.left.name}'", expr.pos)
            return left
        elif expr.op in ("+=", "-=", "*=", "/="):
            if isinstance(expr.left, IdentifierExpr):
                sym = self.symbols.resolve(expr.left.name)
                if sym and not sym.mutable:
                    self.error(f"Cannot assign to immutable variable '{expr.left.name}'", expr.pos)
            return left
        elif expr.op == "??":
            return OptionalType(left) if right == NULL else right
        elif expr.op == "++":
            return STRING
        return left

    def _analyze_unary(self, expr: UnaryExpr) -> Type:
        inner = self.analyze_expr(expr.right)
        if expr.op == "-":
            if not is_numeric(inner):
                self.error(f"Cannot negate non-numeric type {inner}", expr.pos)
            return inner
        elif expr.op == "!":
            if inner != BOOL and inner != TypeVariable():
                self.error(f"Cannot apply '!' to type {inner}", expr.pos)
            return BOOL
        return inner

    def _analyze_call(self, expr: CallExpr) -> Type:
        callee_type = self.analyze_expr(expr.callee)
        for arg in expr.args:
            self.analyze_expr(arg)

        if isinstance(callee_type, FunctionType):
            return callee_type.return_type
        if isinstance(callee_type, TypeVariable):
            return TypeVariable()
        if isinstance(callee_type, (NamedType, AgentType)):
            return callee_type
        self.error(f"Cannot call non-function type {callee_type}", expr.pos)
        return TypeVariable()

    def _analyze_index(self, expr: IndexExpr) -> Type:
        target_type = self.analyze_expr(expr.target)
        index_type = self.analyze_expr(expr.index)

        if isinstance(target_type, ArrayType):
            return target_type.element_type
        if isinstance(target_type, TupleType):
            if isinstance(expr.index, LiteralExpr) and isinstance(expr.index.value, int):
                idx = expr.index.value
                if 0 <= idx < len(target_type.types):
                    return target_type.types[idx]
                self.error(f"Tuple index {idx} out of bounds", expr.pos)
            return TypeVariable()
        if isinstance(target_type, TypeVariable):
            return TypeVariable()
        self.error(f"Cannot index type {target_type}", expr.pos)
        return TypeVariable()

    def _analyze_attribute(self, expr: AttributeExpr) -> Type:
        target_type = self.analyze_expr(expr.target)
        if isinstance(target_type, NamedType):
            return TypeVariable()
        return TypeVariable()

    def _analyze_if(self, expr: IfExpr) -> Type:
        self.analyze_expr(expr.condition)
        then_type = self.analyze_expr(expr.then_branch)
        else_type = self.analyze_expr(expr.else_branch) if expr.else_branch else NULL
        return then_type if then_type == else_type else TypeVariable()

    def _analyze_match(self, expr: MatchExpr) -> Type:
        self.analyze_expr(expr.value)
        result_type = TypeVariable()
        for arm in expr.arms:
            arm_type = self.analyze_expr(arm.body)
            if isinstance(result_type, TypeVariable) and not isinstance(arm_type, TypeVariable):
                result_type = arm_type
        return result_type

    def _analyze_block(self, expr: BlockExpr) -> Type:
        last_type = NULL
        self.symbols.enter_scope()
        for stmt in expr.statements:
            if isinstance(stmt, ExpressionStmt):
                last_type = self.analyze_expr(stmt.expression)
            else:
                self.analyze_stmt(stmt)
                last_type = NULL
        self.symbols.exit_scope()
        return last_type

    def _analyze_closure(self, expr: ClosureExpr) -> Type:
        param_types = []
        self.symbols.enter_scope()
        for p in expr.params:
            ptype = TypeVariable()
            param_types.append(ptype)
            self.symbols.define(p.name, SymbolKind.PARAMETER, ptype, False, p.pos)
        body_type = self.analyze_expr(expr.body)
        self.symbols.exit_scope()
        return FunctionType(param_types, body_type)

    def _analyze_list(self, expr: ListExpr) -> Type:
        element_type = TypeVariable()
        for elem in expr.elements:
            et = self.analyze_expr(elem)
            if isinstance(element_type, TypeVariable) and not isinstance(et, TypeVariable):
                element_type = et
        return ArrayType(element_type)

    def _analyze_map(self, expr: MapExpr) -> Type:
        for key, value in expr.entries:
            self.analyze_expr(key)
            self.analyze_expr(value)
        return NamedType("Map")

    def _analyze_ai(self, expr: AIExpr) -> Type:
        if expr.prompt:
            self.analyze_expr(expr.prompt.expression)
        if expr.model:
            self.analyze_expr(expr.model.expression)
        if expr.system:
            self.analyze_expr(expr.system.expression)
        for opt in expr.options:
            self.analyze_expr(opt.value)
        return STRING

    def _analyze_embed(self, expr: EmbedExpr) -> Type:
        self.analyze_expr(expr.expression)
        return NamedType("Embedding")

    def resolve_type(self, type_ref: Optional["TypeRef"]) -> Type:
        if type_ref is None:
            return TypeVariable()
        if type_ref.name in PRIMITIVE_TYPES:
            return PRIMITIVE_TYPES[type_ref.name]
        if type_ref.name == "Array":
            inner = self.resolve_type(type_ref.generic_args[0]) if type_ref.generic_args else TypeVariable()
            return ArrayType(inner)
        if type_ref.name == "Tuple":
            types = [self.resolve_type(a) for a in type_ref.generic_args]
            return TupleType(types)
        if type_ref.name == "Option":
            inner = self.resolve_type(type_ref.generic_args[0]) if type_ref.generic_args else TypeVariable()
            return OptionalType(inner)
        if type_ref.name == "Result":
            ok = self.resolve_type(type_ref.generic_args[0]) if len(type_ref.generic_args) > 0 else TypeVariable()
            err = self.resolve_type(type_ref.generic_args[1]) if len(type_ref.generic_args) > 1 else TypeVariable()
            return ResultType(ok, err)
        if type_ref.name == "Ref":
            inner = self.resolve_type(type_ref.generic_args[0]) if type_ref.generic_args else TypeVariable()
            return inner
        if type_ref.name == "Self":
            return NamedType("Self")
        if type_ref.name == "own":
            inner = self.resolve_type(type_ref.generic_args[0]) if type_ref.generic_args else TypeVariable()
            return inner

        sym = self.symbols.resolve(type_ref.name)
        if sym:
            return sym.type
        return NamedType(type_ref.name)
