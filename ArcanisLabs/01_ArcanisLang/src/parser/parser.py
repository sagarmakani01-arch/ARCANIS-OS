from lexer.token import Token, TokenType
from .ast import *


class ParseError(Exception):
    def __init__(self, message, pos):
        self.message = message
        self.pos = pos
        super().__init__(f"line {pos.line}:{pos.column}: {message}")


def _pos(token):
    return Position(token.line, token.column)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def peek(self, offset=0):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self):
        tok = self.current()
        self.pos += 1
        return tok

    def is_at_end(self):
        return self.current().type == TokenType.EOF

    def check(self, *types):
        return self.current().type in types

    def match(self, *types):
        if self.current().type in types:
            return self.advance()
        return None

    def expect(self, *types, message=None):
        tok = self.current()
        if tok.type in types:
            return self.advance()
        expected = ", ".join(t.name for t in types)
        msg = message or f"Expected {expected}, got {tok.type.name} ({tok.value!r})"
        raise ParseError(msg, _pos(tok))

    def skip_newlines(self):
        while self.match(TokenType.NEWLINE, TokenType.SEMICOLON):
            pass

    def parse(self):
        statements = []
        pos = _pos(self.current())
        while not self.is_at_end():
            stmt = self.parse_stmt()
            if stmt is not None:
                statements.append(stmt)
            else:
                self.advance()
        return Program(statements, pos)

    # --- Statements ---

    def parse_stmt(self):
        tok = self.current()
        pos = _pos(tok)

        if tok.type == TokenType.IMPORT:
            return self.parse_import()
        if tok.type == TokenType.USE:
            return self.parse_use()
        if tok.type == TokenType.PUB:
            return self.parse_pub_decl()
        if tok.type == TokenType.LET:
            return self.parse_let()
        if tok.type == TokenType.CONST:
            return self.parse_const()
        if tok.type == TokenType.FN:
            return self.parse_fn()
        if tok.type == TokenType.STRUCT:
            return self.parse_struct()
        if tok.type == TokenType.ENUM:
            return self.parse_enum()
        if tok.type == TokenType.TRAIT:
            return self.parse_trait()
        if tok.type == TokenType.IMPL:
            return self.parse_impl()
        if tok.type == TokenType.AGENT:
            return self.parse_agent()
        if tok.type == TokenType.TYPE:
            return self.parse_type_alias()
        if tok.type == TokenType.MOD:
            return self.parse_mod()
        if tok.type == TokenType.RETURN:
            return self.parse_return()
        if tok.type == TokenType.BREAK:
            self.advance()
            return BreakStmt(pos)
        if tok.type == TokenType.CONTINUE:
            self.advance()
            return ContinueStmt(pos)
        if tok.type == TokenType.THROW:
            return self.parse_throw()
        if tok.type == TokenType.PASS:
            self.advance()
            self.skip_newlines()
            return PassStmt(pos)
        if tok.type == TokenType.DEFER:
            return self.parse_defer()
        if tok.type == TokenType.FOR:
            return self.parse_for()
        if tok.type == TokenType.WHILE:
            return self.parse_while()
        if tok.type in (TokenType.NEWLINE, TokenType.DEDENT, TokenType.INDENT, TokenType.SEMICOLON, TokenType.EOF):
            return None

        expr = self.parse_expr()
        if expr is not None:
            self.skip_newlines()
            return ExpressionStmt(expr, pos)
        return None

    def parse_import(self):
        self.advance()
        pos = _pos(self.current())
        path_tok = self.expect(TokenType.STRING, message="Expected module path string")
        path = path_tok.value

        names = None
        alias = None

        if self.match(TokenType.LBRACE):
            names = []
            while not self.check(TokenType.RBRACE) and not self.is_at_end():
                name_tok = self.expect(TokenType.IDENTIFIER, message="Expected identifier in import list")
                names.append(name_tok.value)
                self.match(TokenType.COMMA)
            self.expect(TokenType.RBRACE, message="Expected '}' after import list")

        if self.match(TokenType.AS):
            alias_tok = self.expect(TokenType.IDENTIFIER, message="Expected alias name")
            alias = alias_tok.value

        self.skip_newlines()
        return ImportStmt(path, names, alias, pos)

    def parse_use(self):
        self.advance()
        pos = _pos(self.current())
        parts = []
        while self.check(TokenType.IDENTIFIER):
            parts.append(self.advance().value)
            if not self.match(TokenType.DOT):
                break
        alias = None
        if self.match(TokenType.AS):
            alias = self.expect(TokenType.IDENTIFIER, message="Expected alias name").value
        self.skip_newlines()
        return UseStmt(parts, alias, pos)

    def parse_pub_decl(self):
        self.advance()
        tok = self.current()
        if tok.type == TokenType.FN:
            decl = self.parse_fn()
            decl.pub = True
            return decl
        if tok.type == TokenType.STRUCT:
            decl = self.parse_struct()
            decl.pub = True
            return decl
        if tok.type == TokenType.ENUM:
            decl = self.parse_enum()
            decl.pub = True
            return decl
        if tok.type == TokenType.TRAIT:
            decl = self.parse_trait()
            decl.pub = True
            return decl
        if tok.type == TokenType.CONST:
            decl = self.parse_const()
            return decl
        raise ParseError("Expected declaration after 'pub'", _pos(tok))

    def parse_let(self):
        self.advance()
        pos = _pos(self.current())
        mutable = self.match(TokenType.MUT) is not None
        name_tok = self.expect(TokenType.IDENTIFIER, message="Expected variable name")
        name = name_tok.value

        type_anno = None
        if self.match(TokenType.COLON):
            type_anno = self.parse_type()

        self.expect(TokenType.EQ, message=f"Expected '=' in let declaration for '{name}'")
        value = self.parse_expr()
        self.skip_newlines()
        return LetStmt(name, mutable, type_anno, value, pos)

    def parse_const(self):
        self.advance()
        pos = _pos(self.current())
        name_tok = self.expect(TokenType.IDENTIFIER, message="Expected constant name")
        name = name_tok.value
        self.expect(TokenType.COLON, message="Expected ':' in const declaration")
        type_anno = self.parse_type()
        self.expect(TokenType.EQ, message=f"Expected '=' in const declaration for '{name}'")
        value = self.parse_expr()
        self.skip_newlines()
        return ConstStmt(name, type_anno, value, pos)

    def parse_fn(self):
        self.advance()
        pos = _pos(self.current())
        async_ = False
        name_tok = self.expect(TokenType.IDENTIFIER, message="Expected function name")
        name = name_tok.value

        self.expect(TokenType.LPAREN, message="Expected '(' after function name")
        params = self.parse_params()
        self.expect(TokenType.RPAREN, message="Expected ')' after parameters")

        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.parse_type()

        body = self.parse_block()
        return FnDecl(name, params, return_type, body, pub=False, async_=async_, pos=pos)

    def parse_params(self):
        params = []
        while not self.check(TokenType.RPAREN) and not self.is_at_end():
            if self.check(TokenType.COMMA):
                self.advance()
                continue
            name_tok = self.match(TokenType.IDENTIFIER, TokenType.SELF)
            if not name_tok:
                name_tok = self.expect(TokenType.IDENTIFIER, message="Expected parameter name")
            name = name_tok.value
            type_anno = None
            default = None
            if self.match(TokenType.COLON):
                type_anno = self.parse_type()
            if self.match(TokenType.EQ):
                default = self.parse_expr()
            params.append(Param(name, type_anno, default, _pos(name_tok)))
        return params

    def parse_block(self):
        pos = _pos(self.current())
        statements = []

        if self.match(TokenType.COLON):
            self.skip_newlines()
            if self.match(TokenType.INDENT):
                while not self.check(TokenType.DEDENT) and not self.is_at_end():
                    stmt = self.parse_stmt()
                    if stmt:
                        statements.append(stmt)
                    else:
                        self.advance()
                self.match(TokenType.DEDENT)
                return BlockExpr(statements, pos)

        if self.match(TokenType.LBRACE):
            while not self.check(TokenType.RBRACE) and not self.is_at_end():
                stmt = self.parse_stmt()
                if stmt:
                    statements.append(stmt)
                else:
                    self.advance()
            self.expect(TokenType.RBRACE, message="Expected '}' to close block")
            return BlockExpr(statements, pos)

        if self.match(TokenType.INDENT):
            while not self.check(TokenType.DEDENT) and not self.is_at_end():
                stmt = self.parse_stmt()
                if stmt:
                    statements.append(stmt)
                else:
                    self.advance()
            self.match(TokenType.DEDENT)
            return BlockExpr(statements, pos)

        if self.check(TokenType.NEWLINE):
            self.skip_newlines()
            return self.parse_block()

        stmt = self.parse_stmt()
        if stmt:
            statements.append(stmt)
        return BlockExpr(statements, pos)

    def parse_struct(self):
        self.advance()
        pos = _pos(self.current())
        name_tok = self.expect(TokenType.IDENTIFIER, message="Expected struct name")
        name = name_tok.value

        fields = []
        if self.match(TokenType.LBRACE):
            self.skip_newlines()
            while not self.check(TokenType.RBRACE) and not self.is_at_end():
                if self.check(TokenType.INDENT, TokenType.DEDENT):
                    self.advance()
                    self.skip_newlines()
                    continue
                fname = self.expect(TokenType.IDENTIFIER, message="Expected field name").value
                self.expect(TokenType.COLON, message="Expected ':' after field name")
                ftype = self.parse_type()
                fields.append(Param(fname, ftype, None, _pos(self.current())))
                self.match(TokenType.COMMA)
                self.skip_newlines()
            self.expect(TokenType.RBRACE, message="Expected '}' to close struct")
        elif self.match(TokenType.COLON):
            self.skip_newlines()
            if self.match(TokenType.INDENT):
                while not self.check(TokenType.DEDENT) and not self.is_at_end():
                    fname = self.expect(TokenType.IDENTIFIER, message="Expected field name").value
                    self.expect(TokenType.COLON, message="Expected ':' after field name")
                    ftype = self.parse_type()
                    fields.append(Param(fname, ftype, None, _pos(self.current())))
                    self.skip_newlines()
                self.match(TokenType.DEDENT)
        self.skip_newlines()
        return StructDecl(name, fields, pub=False, pos=pos)

    def parse_enum(self):
        self.advance()
        pos = _pos(self.current())
        name_tok = self.expect(TokenType.IDENTIFIER, message="Expected enum name")
        name = name_tok.value

        variants = []
        if self.match(TokenType.LBRACE):
            while not self.check(TokenType.RBRACE) and not self.is_at_end():
                vname = self.expect(TokenType.IDENTIFIER, message="Expected variant name").value
                variant_types = []
                if self.match(TokenType.LPAREN):
                    variant_types.append(self.parse_type())
                    while self.match(TokenType.COMMA):
                        variant_types.append(self.parse_type())
                    self.expect(TokenType.RPAREN, message="Expected ')' after variant types")
                variants.append(EnumVariant(vname, variant_types, _pos(self.current())))
                self.match(TokenType.COMMA)
                self.skip_newlines()
            self.expect(TokenType.RBRACE, message="Expected '}' to close enum")
        elif self.match(TokenType.COLON):
            self.skip_newlines()
            if self.match(TokenType.INDENT):
                while not self.check(TokenType.DEDENT) and not self.is_at_end():
                    vname = self.expect(TokenType.IDENTIFIER, message="Expected variant name").value
                    variant_types = []
                    if self.match(TokenType.LPAREN):
                        variant_types.append(self.parse_type())
                        while self.match(TokenType.COMMA):
                            variant_types.append(self.parse_type())
                        self.expect(TokenType.RPAREN, message="Expected ')' after variant types")
                    variants.append(EnumVariant(vname, variant_types, _pos(self.current())))
                    self.skip_newlines()
                self.match(TokenType.DEDENT)
        self.skip_newlines()
        return EnumDecl(name, variants, pub=False, pos=pos)

    def parse_trait(self):
        self.advance()
        pos = _pos(self.current())
        name_tok = self.expect(TokenType.IDENTIFIER, message="Expected trait name")
        name = name_tok.value
        methods = []
        if self.match(TokenType.LBRACE):
            while not self.check(TokenType.RBRACE) and not self.is_at_end():
                self.skip_newlines()
                if self.check(TokenType.FN):
                    self.advance()
                    mname = self.expect(TokenType.IDENTIFIER, message="Expected method name").value
                    self.expect(TokenType.LPAREN)
                    mparams = self.parse_params()
                    self.expect(TokenType.RPAREN)
                    mreturn = None
                    if self.match(TokenType.ARROW):
                        mreturn = self.parse_type()
                    methods.append(TraitMethod(mname, mparams, mreturn, _pos(self.current())))
                    self.skip_newlines()
            self.expect(TokenType.RBRACE, message="Expected '}' to close trait")
        elif self.match(TokenType.COLON):
            self.skip_newlines()
            if self.match(TokenType.INDENT):
                while not self.check(TokenType.DEDENT) and not self.is_at_end():
                    self.skip_newlines()
                    if self.check(TokenType.FN):
                        self.advance()
                        mname = self.expect(TokenType.IDENTIFIER, message="Expected method name").value
                        self.expect(TokenType.LPAREN)
                        mparams = self.parse_params()
                        self.expect(TokenType.RPAREN)
                        mreturn = None
                        if self.match(TokenType.ARROW):
                            mreturn = self.parse_type()
                        methods.append(TraitMethod(mname, mparams, mreturn, _pos(self.current())))
                    self.skip_newlines()
                self.match(TokenType.DEDENT)
        self.skip_newlines()
        return TraitDecl(name, methods, pub=False, pos=pos)

    def parse_impl(self):
        self.advance()
        pos = _pos(self.current())
        type_name = self.parse_type()
        trait_name = None
        if self.match(TokenType.FOR):
            trait_name = type_name
            type_name = self.parse_type()

        methods = []
        if self.match(TokenType.LBRACE):
            while not self.check(TokenType.RBRACE) and not self.is_at_end():
                self.skip_newlines()
                if self.check(TokenType.FN):
                    methods.append(self.parse_fn())
                else:
                    self.advance()
            self.expect(TokenType.RBRACE, message="Expected '}' to close impl")
        self.skip_newlines()
        return ImplDecl(type_name, trait_name, methods, pos)

    def parse_agent_body(self):
        role = None
        model = None
        memory = None
        tools = []
        methods = []

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            self.skip_newlines()
            if self.check(TokenType.INDENT, TokenType.DEDENT):
                self.advance()
                continue
            tok = self.current()
            if tok.type == TokenType.ROLE:
                self.advance()
                self.expect(TokenType.COLON)
                role = self.parse_expr()
            elif tok.type == TokenType.MODEL:
                self.advance()
                self.expect(TokenType.COLON)
                model = self.parse_expr()
            elif tok.type == TokenType.MEMORY:
                self.advance()
                self.expect(TokenType.COLON)
                memory = self.parse_expr()
            elif tok.type == TokenType.TOOL:
                self.advance()
                tname = self.expect(TokenType.IDENTIFIER, message="Expected tool name").value
                self.expect(TokenType.LPAREN)
                tparams = self.parse_params()
                self.expect(TokenType.RPAREN)
                treturn = None
                if self.match(TokenType.ARROW):
                    treturn = self.parse_type()
                tools.append(AgentTool(tname, tparams, treturn, _pos(self.current())))
            elif tok.type == TokenType.FN:
                methods.append(self.parse_fn())
            else:
                if not self.check(TokenType.RBRACE, TokenType.NEWLINE, TokenType.DEDENT):
                    self.advance()
        return role, model, memory, tools, methods

    def parse_agent(self):
        self.advance()
        pos = _pos(self.current())
        name_tok = self.expect(TokenType.IDENTIFIER, message="Expected agent name")
        name = name_tok.value

        role = None
        model = None
        memory = None
        tools = []
        methods = []

        if self.match(TokenType.LBRACE):
            role, model, memory, tools, methods = self.parse_agent_body()
            self.expect(TokenType.RBRACE, message="Expected '}' to close agent")
        elif self.match(TokenType.COLON):
            self.skip_newlines()
            if self.match(TokenType.INDENT):
                role, model, memory, tools, methods = self.parse_agent_body()
                self.match(TokenType.DEDENT)
        self.skip_newlines()
        return AgentDecl(name, role, model, memory, tools, methods, pos)

    def parse_type_alias(self):
        self.advance()
        pos = _pos(self.current())
        name_tok = self.expect(TokenType.IDENTIFIER, message="Expected type name")
        name = name_tok.value
        self.expect(TokenType.EQ, message="Expected '=' in type alias")
        target = self.parse_type()
        self.skip_newlines()
        return TypeAlias(name, target, pos)

    def parse_mod(self):
        self.advance()
        pos = _pos(self.current())
        name_tok = self.expect(TokenType.IDENTIFIER, message="Expected module name")
        name = name_tok.value
        self.skip_newlines()
        return ModDecl(name, pos)

    def parse_return(self):
        self.advance()
        pos = _pos(self.current())
        value = None
        if not self.check(TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF, TokenType.RBRACE):
            value = self.parse_expr()
        self.skip_newlines()
        return ReturnStmt(value, pos)

    def parse_throw(self):
        self.advance()
        pos = _pos(self.current())
        value = self.parse_expr()
        self.skip_newlines()
        return ThrowStmt(value, pos)

    def parse_defer(self):
        self.advance()
        pos = _pos(self.current())
        call = self.parse_expr()
        self.skip_newlines()
        return DeferStmt(call, pos)

    def parse_for(self):
        self.advance()
        pos = _pos(self.current())
        pattern = self.parse_expr()
        self.expect(TokenType.IN, message="Expected 'in' after for pattern")
        iterable = self.parse_expr()
        self.skip_newlines()
        body = self.parse_block()
        return ForStmt(pattern, iterable, body, pos)

    def parse_while(self):
        self.advance()
        pos = _pos(self.current())
        condition = self.parse_expr()
        self.skip_newlines()
        body = self.parse_block()
        return WhileStmt(condition, body, pos)

    # --- Types ---

    def parse_type(self):
        pos = _pos(self.current())
        tok = self.current()
        if tok.type == TokenType.IDENTIFIER:
            name = self.advance().value
            generic_args = []
            if self.match(TokenType.LT):
                generic_args.append(self.parse_type())
                while self.match(TokenType.COMMA):
                    generic_args.append(self.parse_type())
                self.expect(TokenType.GT, message="Expected '>' to close generic args")
            return TypeRef(name, pos, generic_args)
        if tok.type == TokenType.LBRACKET:
            self.advance()
            inner = self.parse_type()
            self.expect(TokenType.RBRACKET, message="Expected ']' to close array type")
            return TypeRef("Array", pos, [inner])
        if tok.type == TokenType.LPAREN:
            self.advance()
            types = [self.parse_type()]
            while self.match(TokenType.COMMA):
                types.append(self.parse_type())
            self.expect(TokenType.RPAREN)
            return TypeRef("Tuple", pos, types)
        if tok.type == TokenType.AMPERSAND:
            self.advance()
            is_mut = False
            if self.match(TokenType.MUT):
                is_mut = True
            inner = self.parse_type()
            return TypeRef("Ref", pos, [inner])
        if tok.type == TokenType.PIPE:
            self.advance()
            types = [self.parse_type()]
            while self.match(TokenType.PIPE):
                types.append(self.parse_type())
            return TypeRef("Union", pos, types)
        if tok.type == TokenType.SELF:
            self.advance()
            return TypeRef("Self", pos, [])
        raise ParseError(f"Expected type, got {tok.type.name} ({tok.value!r})", pos)

    # --- Expressions ---

    POSTFIX_TYPES = {TokenType.LPAREN, TokenType.LBRACKET, TokenType.DOT}

    def parse_expr(self, min_prec=0):
        tok = self.current()
        pos = _pos(tok)

        left = self.parse_prefix()
        if left is None:
            return None

        while True:
            tok = self.current()
            if tok.type in self.POSTFIX_TYPES:
                left = self.parse_infix(left, 0)
                continue
            prec = self.get_precedence(tok.type)
            if prec is None or prec < min_prec:
                break
            left = self.parse_infix(left, prec)

        return left

    def get_precedence(self, tok_type):
        table = {
            TokenType.OR: 10,
            TokenType.AND: 20,
            TokenType.EQ_EQ: 30,
            TokenType.BANG_EQ: 30,
            TokenType.LT: 30,
            TokenType.GT: 30,
            TokenType.LT_EQ: 30,
            TokenType.GT_EQ: 30,
            TokenType.DOTDOT: 35,
            TokenType.DOTDOT_EQ: 35,
            TokenType.PLUS_PLUS: 40,
            TokenType.PLUS: 40,
            TokenType.MINUS: 40,
            TokenType.STAR: 50,
            TokenType.SLASH: 50,
            TokenType.PERCENT: 50,
            TokenType.EQ: 5,
            TokenType.PLUS_EQ: 5,
            TokenType.MINUS_EQ: 5,
            TokenType.STAR_EQ: 5,
            TokenType.SLASH_EQ: 5,
            TokenType.QUESTION: 60,
        }
        return table.get(tok_type)

    def parse_prefix(self):
        tok = self.advance()
        pos = _pos(tok)

        if tok.type == TokenType.INTEGER:
            return LiteralExpr(int(tok.value.replace("_", ""), 0), pos)
        if tok.type == TokenType.FLOAT:
            return LiteralExpr(float(tok.value.replace("_", "")), pos)
        if tok.type == TokenType.STRING:
            return LiteralExpr(tok.value, pos)
        if tok.type == TokenType.STRING_BLOCK:
            return LiteralExpr(tok.value, pos)
        if tok.type == TokenType.TRUE:
            return LiteralExpr(True, pos)
        if tok.type == TokenType.FALSE:
            return LiteralExpr(False, pos)
        if tok.type == TokenType.NIL:
            return LiteralExpr(None, pos)
        if tok.type == TokenType.IDENTIFIER:
            return IdentifierExpr(tok.value, pos)
        if tok.type == TokenType.SELF:
            return IdentifierExpr("self", pos)
        if tok.type == TokenType.UNDERSCORE:
            return IdentifierExpr("_", pos)

        if tok.type == TokenType.MINUS:
            right = self.parse_expr(70)
            return UnaryExpr("-", right, pos)
        if tok.type == TokenType.BANG:
            right = self.parse_expr(70)
            return UnaryExpr("!", right, pos)

        if tok.type == TokenType.LPAREN:
            exprs = [self.parse_expr()]
            while self.match(TokenType.COMMA):
                if self.check(TokenType.RPAREN):
                    break
                exprs.append(self.parse_expr())
            self.expect(TokenType.RPAREN, message="Expected ')' after expression")
            if len(exprs) == 1:
                return exprs[0]
            return ListExpr(exprs, pos)

        if tok.type == TokenType.LBRACKET:
            elements = []
            while not self.check(TokenType.RBRACKET) and not self.is_at_end():
                elements.append(self.parse_expr())
                self.match(TokenType.COMMA)
            self.expect(TokenType.RBRACKET, message="Expected ']' to close list")
            return ListExpr(elements, pos)

        if tok.type == TokenType.LBRACE:
            entries = []
            while not self.check(TokenType.RBRACE) and not self.is_at_end():
                key = self.parse_expr()
                if self.match(TokenType.COLON):
                    value = self.parse_expr()
                    entries.append((key, value))
                else:
                    entries.append((key, LiteralExpr(True, pos)))
                self.match(TokenType.COMMA)
            self.expect(TokenType.RBRACE, message="Expected '}' to close map/set")
            if entries and all(isinstance(k, LiteralExpr) for k, _ in entries):
                pass
            return MapExpr(entries, pos) if any(
                len(e) == 2 for e in entries if isinstance(e, tuple)
            ) else ListExpr([k for k, _ in entries], pos)

        if tok.type == TokenType.FN:
            if self.match(TokenType.LPAREN):
                params = self.parse_params()
                self.expect(TokenType.RPAREN, message="Expected ')' after closure params")
                body = self.parse_expr()
                return ClosureExpr(params, body, pos)
            name_tok = IdentifierExpr(self.expect(
                TokenType.IDENTIFIER, message="Expected function name").value, _pos(self.current()))
            self.expect(TokenType.LPAREN, message="Expected '(' after function name")
            params = self.parse_params()
            self.expect(TokenType.RPAREN, message="Expected ')' after parameters")
            return_type = None
            if self.match(TokenType.ARROW):
                return_type = self.parse_type()
            body = self.parse_block()
            return FnDecl(name_tok.name, params, return_type, body, pub=False, async_=False, pos=pos)

        if tok.type == TokenType.IF:
            condition = self.parse_expr()
            self.match(TokenType.COLON)
            self.skip_newlines()
            then_branch = self.parse_block()
            else_branch = None
            if self.match(TokenType.ELSE):
                self.match(TokenType.COLON)
                self.skip_newlines()
                else_branch = self.parse_block()
            return IfExpr(condition, then_branch, else_branch, pos)

        if tok.type == TokenType.MATCH:
            value = self.parse_expr()
            self.match(TokenType.COLON)
            self.skip_newlines()
            if not self.match(TokenType.LBRACE):
                self.match(TokenType.INDENT)
            arms = []
            while not self.check(TokenType.RBRACE, TokenType.DEDENT) and not self.is_at_end():
                self.skip_newlines()
                if self.check(TokenType.INDENT, TokenType.DEDENT):
                    self.advance()
                    continue
                if self.check(TokenType.RBRACE):
                    break
                pattern = self.parse_expr()
                self.expect(TokenType.FAT_ARROW, message="Expected '=>' in match arm")
                if self.check(TokenType.LBRACE):
                    body = self.parse_block()
                else:
                    body = self.parse_expr()
                arms.append(MatchArm(pattern, body, _pos(self.current())))
                self.match(TokenType.COMMA)
                self.skip_newlines()
            self.match(TokenType.RBRACE)
            self.match(TokenType.DEDENT)
            return MatchExpr(value, arms, pos)

        if tok.type == TokenType.AI:
            return self.parse_ai_expr(pos)

        if tok.type == TokenType.PROMPT:
            return self.parse_prompt_call(pos)

        if tok.type == TokenType.EMBED:
            return self.parse_embed(pos)

        if tok.type == TokenType.MODEL:
            return self.parse_model_ref(pos)

        if tok.type == TokenType.MEMORY:
            return self.parse_memory_expr(pos)

        if tok.type == TokenType.ASYNC:
            expr = self.parse_expr(70)
            return AsyncExpr(expr, pos)

        if tok.type == TokenType.AWAIT:
            expr = self.parse_expr(70)
            return AwaitExpr(expr, pos)

        if tok.type == TokenType.TRY:
            force = self.match(TokenType.BANG) is not None
            expr = self.parse_expr(70)
            return TryExpr(expr, force, pos)

        if tok.type == TokenType.PIPE:
            params = []
            while not self.check(TokenType.PIPE) and not self.is_at_end():
                name_tok = self.match(TokenType.IDENTIFIER)
                if name_tok:
                    params.append(Param(name_tok.value, None, None, _pos(name_tok)))
                self.match(TokenType.COMMA)
            self.expect(TokenType.PIPE, message="Expected '|' to close closure params")
            body = self.parse_expr()
            return ClosureExpr(params, body, pos)

        if tok.type == TokenType.STRUCT:
            return self.parse_struct_expr(pos)

        if tok.type == TokenType.DOTDOT:
            end = self.parse_expr(35)
            return RangeExpr(LiteralExpr(0, pos), end, False, pos)

        return None

    def parse_infix(self, left, prec):
        tok = self.current()
        pos = _pos(tok)

        if tok.type == TokenType.EQ:
            self.advance()
            right = self.parse_expr(prec)
            return BinaryExpr(left, "=", right, pos)

        if tok.type in (TokenType.PLUS_EQ, TokenType.MINUS_EQ,
                        TokenType.STAR_EQ, TokenType.SLASH_EQ):
            op_map = {TokenType.PLUS_EQ: "+=", TokenType.MINUS_EQ: "-=",
                      TokenType.STAR_EQ: "*=", TokenType.SLASH_EQ: "/="}
            op = op_map[tok.type]
            self.advance()
            right = self.parse_expr(prec)
            return BinaryExpr(left, op, right, pos)

        if tok.type in (TokenType.PLUS, TokenType.PLUS_PLUS, TokenType.MINUS, TokenType.STAR,
                        TokenType.SLASH, TokenType.PERCENT,
                        TokenType.EQ_EQ, TokenType.BANG_EQ,
                        TokenType.LT, TokenType.GT, TokenType.LT_EQ, TokenType.GT_EQ,
                        TokenType.AND, TokenType.OR):
            op_map = {
                TokenType.PLUS: "+", TokenType.PLUS_PLUS: "++",
                TokenType.MINUS: "-",
                TokenType.STAR: "*", TokenType.SLASH: "/",
                TokenType.PERCENT: "%",
                TokenType.EQ_EQ: "==", TokenType.BANG_EQ: "!=",
                TokenType.LT: "<", TokenType.GT: ">",
                TokenType.LT_EQ: "<=", TokenType.GT_EQ: ">=",
                TokenType.AND: "and", TokenType.OR: "or",
            }
            op = op_map[tok.type]
            self.advance()
            right = self.parse_expr(prec)
            return BinaryExpr(left, op, right, pos)

        if tok.type in (TokenType.DOTDOT, TokenType.DOTDOT_EQ):
            inclusive = tok.type == TokenType.DOTDOT_EQ
            self.advance()
            end = self.parse_expr(prec)
            return RangeExpr(left, end, inclusive, pos)

        if tok.type == TokenType.LPAREN:
            return self.parse_call(left, pos)

        if tok.type == TokenType.LBRACKET:
            self.advance()
            if self.check(TokenType.COLON):
                self.advance()
                end = self.parse_expr() if not self.check(TokenType.RBRACKET) else LiteralExpr(None, pos)
                self.expect(TokenType.RBRACKET, message="Expected ']' after slice")
                return IndexExpr(left, RangeExpr(LiteralExpr(0, pos), end, False, pos), pos)
            if self.check(TokenType.RBRACKET):
                self.advance()
                return left
            index = self.parse_expr()
            self.expect(TokenType.RBRACKET, message="Expected ']' after index")
            return IndexExpr(left, index, pos)

        if tok.type == TokenType.DOT:
            self.advance()
            if self.check(TokenType.INTEGER):
                idx = int(self.advance().value)
                return IndexExpr(left, LiteralExpr(idx, _pos(self.current())), pos)
            attr = self.expect(TokenType.IDENTIFIER, message="Expected attribute name").value
            return AttributeExpr(left, attr, pos)

        if tok.type == TokenType.QUESTION:
            self.advance()
            then_branch = self.parse_expr()
            self.expect(TokenType.COLON, message="Expected ':' in ternary")
            else_branch = self.parse_expr()
            return IfExpr(left, then_branch, else_branch, pos)

        if tok.type == TokenType.QUESTION_QUESTION:
            self.advance()
            right = self.parse_expr(prec)
            return BinaryExpr(left, "??", right, pos)

        return left

    def parse_call(self, callee, pos):
        self.advance()
        args = []
        while not self.check(TokenType.RPAREN) and not self.is_at_end():
            args.append(self.parse_expr())
            self.match(TokenType.COMMA)
        self.expect(TokenType.RPAREN, message="Expected ')' after arguments")
        return CallExpr(callee, args, pos)

    def parse_prompt_call(self, pos):
        self.expect(TokenType.LPAREN, message="Expected '(' after prompt")
        expr = self.parse_expr()
        self.expect(TokenType.RPAREN, message="Expected ')' after prompt argument")
        return PromptClause(expr, pos)

    def parse_embed(self, pos):
        self.expect(TokenType.LPAREN, message="Expected '(' after embed")
        expr = self.parse_expr()
        self.expect(TokenType.RPAREN, message="Expected ')' after embed argument")
        return EmbedExpr(expr, pos)

    def parse_model_ref(self, pos):
        model_expr = None
        if self.match(TokenType.LPAREN):
            model_expr = self.parse_expr()
            self.expect(TokenType.RPAREN, message="Expected ')' after model name")
        return ModelClause(model_expr or LiteralExpr("", pos), pos)

    def parse_memory_expr(self, pos):
        expr = None
        if self.match(TokenType.LPAREN):
            if not self.check(TokenType.RPAREN):
                expr = self.parse_expr()
            self.expect(TokenType.RPAREN, message="Expected ')' after memory")
        return MemExpr(expr, pos)

    def parse_ai_expr(self, pos):
        prompt_clause = None
        model_clause = None
        system_clause = None
        options = []

        while not self.is_at_end() and not self.check(
                TokenType.NEWLINE, TokenType.DEDENT, TokenType.RBRACE, TokenType.RPAREN,
                TokenType.COMMA, TokenType.SEMICOLON):
            tok = self.current()

            if tok.type == TokenType.PROMPT:
                self.advance()
                p = self.parse_prompt_call(_pos(tok))
                prompt_clause = p

            elif tok.type == TokenType.MODEL:
                self.advance()
                m = self.parse_model_ref(_pos(tok))
                model_clause = m

            elif tok.type == TokenType.SYSTEM:
                self.advance()
                self.expect(TokenType.LPAREN, message="Expected '(' after system")
                sys_expr = self.parse_expr()
                self.expect(TokenType.RPAREN, message="Expected ')' after system argument")
                system_clause = SystemClause(sys_expr, _pos(tok))

            elif tok.type == TokenType.TEMPERATURE:
                self.advance()
                self.expect(TokenType.LPAREN)
                val = self.parse_expr()
                self.expect(TokenType.RPAREN)
                options.append(AIOption("temperature", val, _pos(tok)))

            elif tok.type == TokenType.MAX_TOKENS:
                self.advance()
                self.expect(TokenType.LPAREN)
                val = self.parse_expr()
                self.expect(TokenType.RPAREN)
                options.append(AIOption("max_tokens", val, _pos(tok)))

            elif tok.type == TokenType.TOP_P:
                self.advance()
                self.expect(TokenType.LPAREN)
                val = self.parse_expr()
                self.expect(TokenType.RPAREN)
                options.append(AIOption("top_p", val, _pos(tok)))

            elif tok.type == TokenType.IDENTIFIER:
                if prompt_clause is None:
                    id_expr = IdentifierExpr(tok.value, _pos(tok))
                    self.advance()
                    if self.match(TokenType.LPAREN):
                        prompt_clause = PromptClause(self.parse_expr(), _pos(self.current()))
                        self.expect(TokenType.RPAREN)
                    else:
                        if self.check(TokenType.LBRACE):
                            prompt_clause = PromptClause(self.parse_expr(), _pos(tok))
                        else:
                            return id_expr
            else:
                break

        if prompt_clause is None:
            raise ParseError("Expected prompt expression in AI expression", pos)

        return AIExpr(prompt_clause, model_clause, system_clause, pos, options)

    def parse_struct_expr(self, pos):
        name_tok = self.expect(TokenType.IDENTIFIER, message="Expected struct name")
        name = name_tok.value
        fields = []
        if self.match(TokenType.LBRACE):
            while not self.check(TokenType.RBRACE) and not self.is_at_end():
                fname = self.expect(TokenType.IDENTIFIER, message="Expected field name").value
                self.expect(TokenType.COLON, message="Expected ':' in struct literal")
                fvalue = self.parse_expr()
                fields.append((fname, fvalue))
                self.match(TokenType.COMMA)
            self.expect(TokenType.RBRACE, message="Expected '}' to close struct literal")
        return StructExpr(name, fields, pos)
