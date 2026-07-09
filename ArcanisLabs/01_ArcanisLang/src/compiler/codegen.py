from typing import List, Optional, Dict
from lexer.token import TokenType
from parser.ast import *
from .ir import IRProgram, Function, BasicBlock, Instruction, Opcode


class CodeGenError(Exception):
    def __init__(self, message: str, pos=None):
        self.pos = pos
        pos_str = f"line {pos.line}:{pos.column}: " if pos else ""
        super().__init__(f"{pos_str}{message}")


class CodeGenerator:
    def __init__(self):
        self.program = IRProgram()
        self.current_fn: Optional[Function] = None
        self.current_block: Optional[BasicBlock] = None
        self.reg_counter = 0
        self.string_table: Dict[str, str] = {}
        self._init_native_builtins()

    def _init_native_builtins(self):
        pass

    def _new_reg(self) -> str:
        self.reg_counter += 1
        return f"r{self.reg_counter}"

    def _new_block(self, label: str) -> BasicBlock:
        block = BasicBlock(label)
        if self.current_fn:
            if self.current_block and self.current_block in self.current_fn.blocks:
                if self.current_block.successor is None:
                    self.current_block.successor = label
                if self.current_block.fallthrough is None:
                    self.current_block.fallthrough = label
            self.current_fn.blocks.append(block)
        return block

    def _emit(self, opcode: Opcode, dest=None, args=None, const_val=None, source_pos=None) -> str:
        instr = self.current_block.add(opcode, dest, args or [], const_val, source_pos)
        return dest or ""

    def compile(self, program: Program) -> IRProgram:
        main_fn = Function(name="__main__", params=[], is_native=False)
        self.program.add_function(main_fn)
        self.current_fn = main_fn
        self.current_block = self._new_block("entry")

        for stmt in program.statements:
            self._gen_stmt(stmt)

        if self.current_block:
            self._emit(Opcode.NOP)

        self.current_fn = None
        self.current_block = None
        return self.program

    def _gen_stmt(self, stmt: Stmt, fn: Function = None):
        if isinstance(stmt, LetStmt):
            self._gen_let(stmt)
        elif isinstance(stmt, ConstStmt):
            self._gen_const(stmt)
        elif isinstance(stmt, FnDecl):
            self._gen_fn_decl(stmt)
        elif isinstance(stmt, ReturnStmt):
            self._gen_return(stmt)
        elif isinstance(stmt, ExpressionStmt):
            self._gen_expr_stmt(stmt)
        elif isinstance(stmt, StructDecl):
            pass
        elif isinstance(stmt, EnumDecl):
            pass
        elif isinstance(stmt, TraitDecl):
            pass
        elif isinstance(stmt, ImplDecl):
            pass
        elif isinstance(stmt, AgentDecl):
            self._gen_agent_decl(stmt)
        elif isinstance(stmt, ForStmt):
            self._gen_for(stmt)
        elif isinstance(stmt, WhileStmt):
            self._gen_while(stmt)
        elif isinstance(stmt, BreakStmt):
            pass
        elif isinstance(stmt, ContinueStmt):
            pass
        elif isinstance(stmt, ThrowStmt):
            pass
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

    def _gen_let(self, stmt: LetStmt):
        if self.current_block:
            val = self._gen_expr(stmt.value) if stmt.value else self._emit_const(None)
            self._emit(Opcode.STORE_VAR, dest=None, args=[stmt.name, val], source_pos=stmt.pos)

    def _gen_const(self, stmt: ConstStmt):
        if self.current_block:
            val = self._gen_expr(stmt.value) if stmt.value else self._emit_const(None)
            self._emit(Opcode.STORE_VAR, dest=None, args=[stmt.name, val], source_pos=stmt.pos)

    def _gen_fn_decl(self, stmt: FnDecl):
        func = Function(
            name=stmt.name,
            params=[p.name for p in stmt.params],
            arity=len(stmt.params),
        )
        self.program.add_function(func)

        saved_fn = self.current_fn
        saved_block = self.current_block
        self.current_fn = func

        entry = self._new_block("entry")
        self.current_block = entry

        for param in stmt.params:
            self._emit(Opcode.LOAD_VAR, dest=param.name, args=[param.name], source_pos=param.pos)

        body_stmts = stmt.body.statements if stmt.body else []
        has_explicit_return = body_stmts and isinstance(body_stmts[-1], ReturnStmt)

        for stmt_node in body_stmts[:-1]:
            self._gen_stmt(stmt_node)

        if body_stmts:
            last = body_stmts[-1]
            if isinstance(last, ReturnStmt):
                self._gen_return(last)
            elif isinstance(last, ExpressionStmt):
                val = self._gen_expr(last.expression)
                self._emit(Opcode.RETURN, args=[val], source_pos=last.pos)
            else:
                self._gen_stmt(last)
                if not has_explicit_return:
                    self._emit(Opcode.RETURN, source_pos=stmt.pos)
        else:
            self._emit(Opcode.RETURN, source_pos=stmt.pos)

        self.current_fn = saved_fn
        self.current_block = saved_block

    def _gen_block_body(self, block: BlockExpr):
        for stmt in block.statements:
            self._gen_stmt(stmt)

    def _gen_agent_decl(self, stmt: AgentDecl):
        for method in stmt.methods:
            self._gen_fn_decl(method)

    def _gen_return(self, stmt: ReturnStmt):
        if self.current_block and stmt.value:
            val = self._gen_expr(stmt.value)
            self._emit(Opcode.RETURN, args=[val], source_pos=stmt.pos)
        elif self.current_block:
            self._emit(Opcode.RETURN, source_pos=stmt.pos)

    def _gen_expr_stmt(self, stmt: ExpressionStmt):
        if self.current_block:
            self._gen_expr(stmt.expression)

    def _gen_for(self, stmt: ForStmt):
        if not self.current_block:
            return

        iter_val = self._gen_expr(stmt.iterable)
        iter_var = self.current_fn.name + "_for_iter"
        idx_var = self.current_fn.name + "_for_idx"
        self._emit(Opcode.STORE_VAR, dest=None, args=[iter_var, iter_val], source_pos=stmt.pos)

        zero = self._emit_const(0)
        self._emit(Opcode.STORE_VAR, dest=None, args=[idx_var, zero], source_pos=stmt.pos)

        cond_label = self.current_fn.name + "_for_cond"
        body_label = self.current_fn.name + "_for_body"
        end_label = self.current_fn.name + "_for_end"

        self._emit(Opcode.JUMP, args=[cond_label], source_pos=stmt.pos)

        cond_block = self._new_block(cond_label)
        self.current_block = cond_block

        idx_reg = self._new_reg()
        self._emit(Opcode.LOAD_VAR, dest=idx_reg, args=[idx_var], source_pos=stmt.pos)

        len_reg = self._new_reg()
        self._emit(Opcode.CALL_NATIVE, dest=len_reg, args=["len", iter_var], source_pos=stmt.pos)

        cond_reg = self._new_reg()
        self._emit(Opcode.LT, dest=cond_reg, args=[idx_reg, len_reg], source_pos=stmt.pos)
        self._emit(Opcode.JUMP_IF_NOT, args=[cond_reg, end_label], source_pos=stmt.pos)

        body_block = self._new_block(body_label)
        self.current_block = body_block

        if isinstance(stmt.pattern, IdentifierExpr):
            elem_reg = self._new_reg()
            self._emit(Opcode.INDEX, dest=elem_reg, args=[iter_var, idx_reg], source_pos=stmt.pos)
            self._emit(Opcode.STORE_VAR, dest=None, args=[stmt.pattern.name, elem_reg], source_pos=stmt.pos)

        self._gen_block_body(stmt.body)

        one = self._emit_const(1)
        new_idx = self._new_reg()
        self._emit(Opcode.ADD, dest=new_idx, args=[idx_reg, one], source_pos=stmt.pos)
        self._emit(Opcode.STORE_VAR, dest=None, args=[idx_var, new_idx], source_pos=stmt.pos)

        self._emit(Opcode.JUMP, args=[cond_label], source_pos=stmt.pos)

        end_block = self._new_block(end_label)
        self.current_block = end_block

    def _gen_while(self, stmt: WhileStmt):
        if not self.current_block:
            return

        cond_label = self.current_fn.name + "_while_cond"
        body_label = self.current_fn.name + "_while_body"
        end_label = self.current_fn.name + "_while_end"

        self._emit(Opcode.JUMP, args=[cond_label], source_pos=stmt.pos)

        cond_block = self._new_block(cond_label)
        self.current_block = cond_block
        cond = self._gen_expr(stmt.condition)
        self._emit(Opcode.JUMP_IF_NOT, args=[cond, end_label], source_pos=stmt.pos)

        body_block = self._new_block(body_label)
        self.current_block = body_block
        self._gen_block_body(stmt.body)
        self._emit(Opcode.JUMP, args=[cond_label], source_pos=stmt.pos)

        end_block = self._new_block(end_label)
        self.current_block = end_block

    def _gen_expr(self, expr: Expr) -> str:
        if isinstance(expr, LiteralExpr):
            return self._gen_literal(expr)
        elif isinstance(expr, IdentifierExpr):
            return self._gen_identifier(expr)
        elif isinstance(expr, BinaryExpr):
            return self._gen_binary(expr)
        elif isinstance(expr, UnaryExpr):
            return self._gen_unary(expr)
        elif isinstance(expr, CallExpr):
            return self._gen_call(expr)
        elif isinstance(expr, IndexExpr):
            return self._gen_index(expr)
        elif isinstance(expr, AttributeExpr):
            return self._gen_attribute(expr)
        elif isinstance(expr, IfExpr):
            return self._gen_if(expr)
        elif isinstance(expr, MatchExpr):
            return self._gen_match(expr)
        elif isinstance(expr, BlockExpr):
            return self._gen_block_expr(expr)
        elif isinstance(expr, ClosureExpr):
            return self._gen_closure(expr)
        elif isinstance(expr, ListExpr):
            return self._gen_list(expr)
        elif isinstance(expr, MapExpr):
            return self._gen_map(expr)
        elif isinstance(expr, AIExpr):
            return self._gen_ai(expr)
        elif isinstance(expr, EmbedExpr):
            return self._gen_embed(expr)
        elif isinstance(expr, StructExpr):
            return self._gen_struct_expr(expr)
        elif isinstance(expr, RangeExpr):
            return self._gen_range(expr)
        elif isinstance(expr, AsyncExpr):
            return self._gen_expr(expr.expression)
        elif isinstance(expr, AwaitExpr):
            return self._gen_expr(expr.expression)
        elif isinstance(expr, TryExpr):
            return self._gen_expr(expr.expression)
        elif isinstance(expr, MemExpr):
            return self._new_reg()
        return self._new_reg()

    def _gen_literal(self, expr: LiteralExpr) -> str:
        return self._emit_const(expr.value)

    def _emit_const(self, value) -> str:
        reg = self._new_reg()
        self._emit(Opcode.LOAD_CONST, dest=reg, const_val=value, source_pos=None)
        return reg

    def _gen_identifier(self, expr: IdentifierExpr) -> str:
        reg = self._new_reg()
        self._emit(Opcode.LOAD_VAR, dest=reg, args=[expr.name], source_pos=expr.pos)
        return reg

    def _gen_binary(self, expr: BinaryExpr) -> str:
        if expr.op in ("=", "+=", "-=", "*=", "/="):
            return self._gen_assignment(expr)

        left = self._gen_expr(expr.left)
        right = self._gen_expr(expr.right)
        dest = self._new_reg()

        op_map = {
            "+": Opcode.ADD, "-": Opcode.SUB, "*": Opcode.MUL,
            "/": Opcode.DIV, "%": Opcode.MOD,
            "==": Opcode.EQ, "!=": Opcode.NE,
            "<": Opcode.LT, ">": Opcode.GT,
            "<=": Opcode.LE, ">=": Opcode.GE,
            "and": Opcode.AND, "or": Opcode.OR,
            "++": Opcode.CONCAT,
        }

        opcode = op_map.get(expr.op, Opcode.NOP)
        self._emit(opcode, dest=dest, args=[left, right], source_pos=expr.pos)
        return dest

    def _gen_assignment(self, expr: BinaryExpr) -> str:
        if isinstance(expr.left, IdentifierExpr):
            val = self._gen_expr(expr.right)
            if expr.op == "=":
                self._emit(Opcode.STORE_VAR, dest=None, args=[expr.left.name, val], source_pos=expr.pos)
            elif expr.op == "+=":
                old = self._new_reg()
                self._emit(Opcode.LOAD_VAR, dest=old, args=[expr.left.name], source_pos=expr.pos)
                new_val = self._new_reg()
                self._emit(Opcode.ADD, dest=new_val, args=[old, val], source_pos=expr.pos)
                self._emit(Opcode.STORE_VAR, dest=None, args=[expr.left.name, new_val], source_pos=expr.pos)
            elif expr.op == "-=":
                old = self._new_reg()
                self._emit(Opcode.LOAD_VAR, dest=old, args=[expr.left.name], source_pos=expr.pos)
                new_val = self._new_reg()
                self._emit(Opcode.SUB, dest=new_val, args=[old, val], source_pos=expr.pos)
                self._emit(Opcode.STORE_VAR, dest=None, args=[expr.left.name, new_val], source_pos=expr.pos)
            elif expr.op == "*=":
                old = self._new_reg()
                self._emit(Opcode.LOAD_VAR, dest=old, args=[expr.left.name], source_pos=expr.pos)
                new_val = self._new_reg()
                self._emit(Opcode.MUL, dest=new_val, args=[old, val], source_pos=expr.pos)
                self._emit(Opcode.STORE_VAR, dest=None, args=[expr.left.name, new_val], source_pos=expr.pos)
            elif expr.op == "/=":
                old = self._new_reg()
                self._emit(Opcode.LOAD_VAR, dest=old, args=[expr.left.name], source_pos=expr.pos)
                new_val = self._new_reg()
                self._emit(Opcode.DIV, dest=new_val, args=[old, val], source_pos=expr.pos)
                self._emit(Opcode.STORE_VAR, dest=None, args=[expr.left.name, new_val], source_pos=expr.pos)
            return val
        elif isinstance(expr.left, IndexExpr):
            target = self._gen_expr(expr.left.target)
            index = self._gen_expr(expr.left.index)
            val = self._gen_expr(expr.right)
            self._emit(Opcode.STORE_INDEX, dest=None, args=[target, index, val], source_pos=expr.pos)
            return val
        elif isinstance(expr.left, AttributeExpr):
            obj = self._gen_expr(expr.left.target)
            val = self._gen_expr(expr.right)
            self._emit(Opcode.SET_ATTR, dest=None, args=[obj, expr.left.attr, val], source_pos=expr.pos)
            return val
        val = self._gen_expr(expr.right)
        return val

    def _gen_unary(self, expr: UnaryExpr) -> str:
        operand = self._gen_expr(expr.right)
        dest = self._new_reg()

        if expr.op == "-":
            self._emit(Opcode.NEG, dest=dest, args=[operand], source_pos=expr.pos)
        elif expr.op == "!":
            self._emit(Opcode.NOT, dest=dest, args=[operand], source_pos=expr.pos)
        else:
            self._emit(Opcode.NOP, dest=dest, args=[operand], source_pos=expr.pos)

        return dest

    def _gen_call(self, expr: CallExpr) -> str:
        callee_name = ""
        if isinstance(expr.callee, IdentifierExpr):
            callee_name = expr.callee.name

        arg_regs = [self._gen_expr(arg) for arg in expr.args]

        if callee_name in ("print", "println"):
            if callee_name == "print":
                self._emit(Opcode.PRINT, args=arg_regs, source_pos=expr.pos)
            else:
                self._emit(Opcode.PRINTLN, args=arg_regs, source_pos=expr.pos)
            return self._new_reg()

        if callee_name in ("cosine_similarity", "semantic_search", "token_count",
                           "read_line", "read_file", "write_file", "sleep",
                           "sin", "cos", "tan", "sqrt", "abs", "floor", "ceil", "round", "random",
                           "int", "float", "str"):
            dest = self._new_reg()
            self._emit(Opcode.CALL_NATIVE, dest=dest, args=[callee_name] + arg_regs, source_pos=expr.pos)
            return dest

        callee_reg = self._gen_expr(expr.callee) if not callee_name else callee_name
        dest = self._new_reg()
        self._emit(Opcode.CALL, dest=dest, args=[callee_reg] + arg_regs, source_pos=expr.pos)
        return dest

    def _gen_index(self, expr: IndexExpr) -> str:
        target = self._gen_expr(expr.target)
        index = self._gen_expr(expr.index)
        dest = self._new_reg()
        self._emit(Opcode.INDEX, dest=dest, args=[target, index], source_pos=expr.pos)
        return dest

    def _gen_attribute(self, expr: AttributeExpr) -> str:
        target = self._gen_expr(expr.target)
        dest = self._new_reg()
        self._emit(Opcode.GET_ATTR, dest=dest, args=[target, expr.attr], source_pos=expr.pos)
        return dest

    def _gen_if(self, expr: IfExpr) -> str:
        dest = self._new_reg()

        then_label = self.current_fn.name + "_if_then"
        else_label = self.current_fn.name + "_if_else"
        end_label = self.current_fn.name + "_if_end"

        cond = self._gen_expr(expr.condition)
        self._emit(Opcode.JUMP_IF_NOT, args=[cond, else_label if expr.else_branch else end_label], source_pos=expr.pos)

        then_block = self._new_block(then_label)
        saved_block = self.current_block
        self.current_block = then_block
        then_result = self._gen_block_expr(expr.then_branch)
        self._emit(Opcode.MOV, dest=dest, args=[then_result], source_pos=expr.pos)
        self._emit(Opcode.JUMP, args=[end_label], source_pos=expr.pos)

        if expr.else_branch:
            else_block = self._new_block(else_label)
            self.current_block = else_block
            else_result = self._gen_block_expr(expr.else_branch)
            self._emit(Opcode.MOV, dest=dest, args=[else_result], source_pos=expr.pos)
            self._emit(Opcode.JUMP, args=[end_label], source_pos=expr.pos)

        end_block = self._new_block(end_label)
        self.current_block = end_block

        return dest

    def _gen_match(self, expr: MatchExpr) -> str:
        dest = self._new_reg()
        self._gen_expr(expr.value)
        for arm in expr.arms:
            self._gen_expr(arm.body)
        return dest

    def _gen_block_expr(self, expr: BlockExpr) -> str:
        dest = self._new_reg()
        for stmt in expr.statements:
            if isinstance(stmt, ExpressionStmt):
                dest = self._gen_expr(stmt.expression)
            else:
                self._gen_stmt(stmt)
        return dest

    def _gen_closure(self, expr: ClosureExpr) -> str:
        reg = self._new_reg()
        self._emit(Opcode.MAKE_CLOSURE, dest=reg, args=[], source_pos=None)
        return reg

    def _gen_list(self, expr: ListExpr) -> str:
        elem_regs = [self._gen_expr(e) for e in expr.elements]
        dest = self._new_reg()
        self._emit(Opcode.BUILD_LIST, dest=dest, args=elem_regs, source_pos=expr.pos)
        return dest

    def _gen_map(self, expr: MapExpr) -> str:
        dest = self._new_reg()
        self._emit(Opcode.BUILD_MAP, dest=dest, args=[], source_pos=expr.pos)
        return dest

    def _gen_ai(self, expr: AIExpr) -> str:
        dest = self._new_reg()
        args = []
        if expr.prompt:
            prompt_reg = self._gen_expr(expr.prompt.expression)
            args.append(prompt_reg)
        if expr.model:
            model_reg = self._gen_expr(expr.model.expression)
            args.append(model_reg)
        self._emit(Opcode.AI_PROMPT, dest=dest, args=args, source_pos=expr.pos)
        return dest

    def _gen_embed(self, expr: EmbedExpr) -> str:
        arg = self._gen_expr(expr.expression)
        dest = self._new_reg()
        self._emit(Opcode.EMBED, dest=dest, args=[arg], source_pos=expr.pos)
        return dest

    def _gen_struct_expr(self, expr: StructExpr) -> str:
        dest = self._new_reg()
        field_vals = []
        for f in (expr.fields or []):
            val = self._gen_expr(f.value) if hasattr(f, 'value') and f.value else self._emit_const(None)
            field_vals.extend([f.name, val])
        self._emit(Opcode.BUILD_STRUCT, dest=dest, args=[expr.name] + field_vals, source_pos=expr.pos)
        return dest

    def _gen_range(self, expr: RangeExpr) -> str:
        start = self._gen_expr(expr.start) if expr.start else self._emit_const(0)
        end = self._gen_expr(expr.end) if expr.end else self._emit_const(0)
        dest = self._new_reg()
        self._emit(Opcode.BUILD_LIST, dest=dest, args=[start, end], source_pos=expr.pos)
        return dest
