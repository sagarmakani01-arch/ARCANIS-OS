from .tokens import TokenType
from .ast import *
from .errors import ParserError

class Parser:
    def __init__(self, tokens, filename="<stdin>"):
        self.tokens = tokens
        self.filename = filename
        self.idx = 0

    def _error(self, msg):
        tok = self._peek()
        raise ParserError(msg, tok.line, tok.column)

    def _peek(self):
        return self.tokens[self.idx] if self.idx < len(self.tokens) else self.tokens[-1]

    def _previous(self):
        return self.tokens[self.idx - 1] if self.idx > 0 else self.tokens[0]

    def _advance(self):
        tok = self.tokens[self.idx]
        self.idx += 1
        return tok

    def _check(self, *types):
        return self._peek().type in types

    def _match(self, *types):
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, ttype, msg=None):
        if self._check(ttype):
            return self._advance()
        tok = self._peek()
        actual = tok.type.name
        expected = ttype.name if hasattr(ttype, 'name') else str(ttype)
        self._error(msg or f"Expected {expected}, got {actual} ({tok.value!r})")

    def parse(self):
        statements = self._parse_statements()
        self._expect(TokenType.EOF)
        return Program(statements)

    def _parse_statements(self, end_types=None):
        statements = []
        end_types = end_types or {TokenType.EOF, TokenType.DEDENT}
        while self.idx < len(self.tokens) and not self._check(*end_types):
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
        return statements

    def _parse_statement(self):
        if self._check(TokenType.IF):
            return self._parse_if()
        if self._check(TokenType.WHILE):
            return self._parse_while()
        if self._check(TokenType.FOR):
            return self._parse_for()
        if self._check(TokenType.FUN):
            return self._parse_fun_def()
        if self._check(TokenType.ASYNC):
            return self._parse_async_fun_def()
        if self._check(TokenType.CLASS):
            return self._parse_class_def()
        if self._check(TokenType.TRY):
            return self._parse_try()
        if self._check(TokenType.IMPORT):
            return self._parse_import()
        if self._check(TokenType.FROM):
            return self._parse_from_import()
        if self._check(TokenType.RAISE):
            return self._parse_raise()
        if self._check(TokenType.RETURN):
            return self._parse_return()
        if self._check(TokenType.BREAK):
            tok = self._advance()
            self._expect(TokenType.NEWLINE)
            return Break(tok.line, tok.column)
        if self._check(TokenType.CONTINUE):
            tok = self._advance()
            self._expect(TokenType.NEWLINE)
            return Continue(tok.line, tok.column)
        if self._check(TokenType.PASS):
            tok = self._advance()
            self._expect(TokenType.NEWLINE)
            return Pass(tok.line, tok.column)
        return self._parse_simple_stmt()

    def _parse_simple_stmt(self):
        expr = self._parse_expr()
        if self._match(TokenType.ASSIGN):
            value = self._parse_expr()
            self._expect(TokenType.NEWLINE)
            return Assign(expr, value, '=', expr.line, expr.column)
        if self._match(TokenType.PLUS_ASSIGN):
            value = self._parse_expr()
            self._expect(TokenType.NEWLINE)
            return Assign(expr, BinaryOp(expr, '+', value), '+=', expr.line, expr.column)
        if self._match(TokenType.MINUS_ASSIGN):
            value = self._parse_expr()
            self._expect(TokenType.NEWLINE)
            return Assign(expr, BinaryOp(expr, '-', value), '-=', expr.line, expr.column)
        self._expect(TokenType.NEWLINE)
        return expr

    def _parse_expr(self):
        return self._parse_or()

    def _parse_or(self):
        left = self._parse_and()
        while self._match(TokenType.OR):
            op = self._previous().value
            right = self._parse_and()
            left = BinaryOp(left, op, right, left.line, left.column)
        return left

    def _parse_and(self):
        left = self._parse_not()
        while self._match(TokenType.AND):
            op = self._previous().value
            right = self._parse_not()
            left = BinaryOp(left, op, right, left.line, left.column)
        return left

    def _parse_not(self):
        if self._match(TokenType.NOT):
            op = self._previous().value
            operand = self._parse_not()
            return UnaryOp(op, operand, operand.line, operand.column)
        return self._parse_comparison()

    def _parse_comparison(self):
        left = self._parse_sum()
        while self._check(TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self._advance().value
            right = self._parse_sum()
            left = BinaryOp(left, op, right, left.line, left.column)
        return left

    def _parse_sum(self):
        left = self._parse_term()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_term()
            left = BinaryOp(left, op, right, left.line, left.column)
        return left

    def _parse_term(self):
        left = self._parse_unary()
        while self._check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._advance().value
            right = self._parse_unary()
            left = BinaryOp(left, op, right, left.line, left.column)
        return left

    def _parse_unary(self):
        if self._check(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            operand = self._parse_unary()
            return UnaryOp(op, operand, operand.line, operand.column)
        return self._parse_power()

    def _parse_power(self):
        left = self._parse_call()
        if self._match(TokenType.POW):
            op = self._previous().value
            right = self._parse_unary()
            left = BinaryOp(left, op, right, left.line, left.column)
        return left

    def _parse_call(self):
        node = self._parse_primary()
        while True:
            if self._match(TokenType.LPAREN):
                args = self._parse_args()
                self._expect(TokenType.RPAREN)
                node = Call(node, args, node.line, node.column)
            elif self._match(TokenType.LBRACKET):
                index = self._parse_expr()
                self._expect(TokenType.RBRACKET)
                node = Subscript(node, index, node.line, node.column)
            elif self._match(TokenType.DOT):
                member = self._expect(TokenType.IDENTIFIER)
                node = MemberAccess(node, member.value, node.line, node.column)
            else:
                break
        return node

    def _parse_primary(self):
        if self._check(TokenType.INTEGER):
            tok = self._advance()
            return Literal(tok.value, tok.line, tok.column)
        if self._check(TokenType.FLOAT):
            tok = self._advance()
            return Literal(tok.value, tok.line, tok.column)
        if self._check(TokenType.STRING):
            tok = self._advance()
            return Literal(tok.value, tok.line, tok.column)
        if self._check(TokenType.BOOLEAN):
            tok = self._advance()
            return Literal(tok.value, tok.line, tok.column)
        if self._check(TokenType.NONE):
            tok = self._advance()
            return Literal(tok.value, tok.line, tok.column)
        if self._check(TokenType.IDENTIFIER):
            tok = self._advance()
            return Identifier(tok.value, tok.line, tok.column)
        if self._check(TokenType.LPAREN):
            self._advance()
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return expr
        if self._check(TokenType.LBRACKET):
            return self._parse_list_literal()
        if self._check(TokenType.LBRACE):
            return self._parse_map_literal()
        if self._check(TokenType.LAMBDA):
            return self._parse_lambda()
        if self._check(TokenType.AWAIT):
            tok = self._advance()
            expr = self._parse_expr()
            return Await(expr, tok.line, tok.column)
        self._error(f"Unexpected token: {self._peek().type.name} ({self._peek().value!r})")

    def _parse_list_literal(self):
        self._expect(TokenType.LBRACKET)
        elements = []
        if not self._check(TokenType.RBRACKET):
            elements.append(self._parse_expr())
            while self._match(TokenType.COMMA):
                if self._check(TokenType.RBRACKET):
                    break
                elements.append(self._parse_expr())
        self._expect(TokenType.RBRACKET)
        return ListLiteral(elements)

    def _parse_map_literal(self):
        self._expect(TokenType.LBRACE)
        pairs = []
        if not self._check(TokenType.RBRACE):
            key = self._parse_expr()
            self._expect(TokenType.COLON)
            value = self._parse_expr()
            pairs.append((key, value))
            while self._match(TokenType.COMMA):
                if self._check(TokenType.RBRACE):
                    break
                key = self._parse_expr()
                self._expect(TokenType.COLON)
                value = self._parse_expr()
                pairs.append((key, value))
        self._expect(TokenType.RBRACE)
        return MapLiteral(pairs)

    def _parse_lambda(self):
        self._advance()
        self._expect(TokenType.LPAREN)
        params = self._parse_params()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.COLON)
        body = self._parse_expr()
        func_name = f"<lambda>"
        return FunctionDef(func_name, params, [Return(body)])

    def _parse_args(self):
        args = []
        if not self._check(TokenType.RPAREN):
            args.append(self._parse_expr())
            while self._match(TokenType.COMMA):
                args.append(self._parse_expr())
        return args

    def _parse_if(self):
        tok = self._advance()
        condition = self._parse_expr()
        self._expect(TokenType.COLON)
        body = self._parse_block()
        elifs = []
        while self._check(TokenType.ELIF):
            self._advance()
            elif_cond = self._parse_expr()
            self._expect(TokenType.COLON)
            elif_body = self._parse_block()
            elifs.append((elif_cond, elif_body))
        else_body = None
        if self._match(TokenType.ELSE):
            self._expect(TokenType.COLON)
            else_body = self._parse_block()
        return If(condition, body, elifs, else_body, tok.line, tok.column)

    def _parse_while(self):
        tok = self._advance()
        condition = self._parse_expr()
        self._expect(TokenType.COLON)
        body = self._parse_block()
        return While(condition, body, tok.line, tok.column)

    def _parse_for(self):
        tok = self._advance()
        target = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.IN)
        iterable = self._parse_expr()
        self._expect(TokenType.COLON)
        body = self._parse_block()
        return For(Identifier(target.value, target.line, target.column),
                   iterable, body, tok.line, tok.column)

    def _parse_fun_def(self):
        tok = self._advance()
        return self._parse_fun_body(tok)

    def _parse_async_fun_def(self):
        async_tok = self._advance()
        tok = self._expect(TokenType.FUN)
        node = self._parse_fun_body(tok)
        node.is_async = True
        return node

    def _parse_fun_body(self, tok):
        name = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.LPAREN)
        params = self._parse_params()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.COLON)
        body = self._parse_block()
        return FunctionDef(name.value, params, body, line=tok.line, column=tok.column)

    def _parse_params(self):
        params = []
        if not self._check(TokenType.RPAREN):
            param = self._expect(TokenType.IDENTIFIER)
            params.append(param.value)
            while self._match(TokenType.COMMA):
                if self._check(TokenType.RPAREN):
                    break
                param = self._expect(TokenType.IDENTIFIER)
                params.append(param.value)
        return params

    def _parse_class_def(self):
        tok = self._advance()
        name = self._expect(TokenType.IDENTIFIER)
        base_classes = []
        if self._match(TokenType.LPAREN):
            if not self._check(TokenType.RPAREN):
                bc = self._expect(TokenType.IDENTIFIER)
                base_classes.append(bc.value)
                while self._match(TokenType.COMMA):
                    bc = self._expect(TokenType.IDENTIFIER)
                    base_classes.append(bc.value)
            self._expect(TokenType.RPAREN)
        self._expect(TokenType.COLON)
        body = self._parse_block()
        return ClassDef(name.value, base_classes, body, tok.line, tok.column)

    def _parse_try(self):
        tok = self._advance()
        self._expect(TokenType.COLON)
        try_body = self._parse_block()
        self._expect(TokenType.CATCH)
        catch_var = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.COLON)
        catch_body = self._parse_block()
        return TryCatch(try_body, catch_var.value, catch_body, tok.line, tok.column)

    def _parse_import(self):
        tok = self._advance()
        module = self._expect(TokenType.IDENTIFIER)
        alias = None
        if self._check(TokenType.IDENTIFIER) and self._peek().value == 'as':
            self._advance()
            alias = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.NEWLINE)
        return Import(module.value, alias, tok.line, tok.column)

    def _parse_from_import(self):
        tok = self._advance()
        module = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.IMPORT)
        names = []
        name = self._expect(TokenType.IDENTIFIER)
        alias = None
        if self._check(TokenType.IDENTIFIER) and self._peek().value == 'as':
            self._advance()
            alias = self._expect(TokenType.IDENTIFIER).value
        names.append((name.value, alias))
        while self._match(TokenType.COMMA):
            name = self._expect(TokenType.IDENTIFIER)
            alias = None
            if self._check(TokenType.IDENTIFIER) and self._peek().value == 'as':
                self._advance()
                alias = self._expect(TokenType.IDENTIFIER).value
            names.append((name.value, alias))
        self._expect(TokenType.NEWLINE)
        return FromImport(module.value, names, tok.line, tok.column)

    def _parse_return(self):
        tok = self._advance()
        if self._check(TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF):
            self._expect(TokenType.NEWLINE)
            return Return(None, tok.line, tok.column)
        value = self._parse_expr()
        self._expect(TokenType.NEWLINE)
        return Return(value, tok.line, tok.column)

    def _parse_raise(self):
        tok = self._advance()
        if self._check(TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF):
            self._expect(TokenType.NEWLINE)
            return Raise(None, tok.line, tok.column)
        expr = self._parse_expr()
        self._expect(TokenType.NEWLINE)
        return Raise(expr, tok.line, tok.column)

    def _parse_block(self):
        if self._match(TokenType.NEWLINE):
            self._expect(TokenType.INDENT)
            stmts = self._parse_statements({TokenType.DEDENT, TokenType.EOF})
            self._expect(TokenType.DEDENT)
            return stmts
        stmt = self._parse_simple_stmt()
        return [stmt]
