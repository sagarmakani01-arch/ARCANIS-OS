from .token import Token, TokenType, KEYWORDS


class LexerError(Exception):
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"line {line}:{column}: {message}")


SINGLE_CHAR_TOKENS = {
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ",": TokenType.COMMA,
    ":": TokenType.COLON,
    ";": TokenType.SEMICOLON,
    "|": TokenType.PIPE,
    "&": TokenType.AMPERSAND,
    "@": TokenType.AT,
}

TWO_CHAR_SEQUENCES = {
    "==": TokenType.EQ_EQ,
    "!=": TokenType.BANG_EQ,
    "<=": TokenType.LT_EQ,
    ">=": TokenType.GT_EQ,
    "->": TokenType.ARROW,
    "=>": TokenType.FAT_ARROW,
    "..": TokenType.DOTDOT,
    "+=": TokenType.PLUS_EQ,
    "-=": TokenType.MINUS_EQ,
    "*=": TokenType.STAR_EQ,
    "/=": TokenType.SLASH_EQ,
    "??": TokenType.QUESTION_QUESTION,
    "++": TokenType.PLUS_PLUS,
    "//": TokenType.ERROR,
}

THREE_CHAR_SEQUENCES = {
    "..=": TokenType.DOTDOT_EQ,
}

ONE_CHAR_OPERATORS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "%": TokenType.PERCENT,
    "=": TokenType.EQ,
    "!": TokenType.BANG,
    "<": TokenType.LT,
    ">": TokenType.GT,
    "?": TokenType.QUESTION,
    ".": TokenType.DOT,
}


class Lexer:
    def __init__(self, source: str, filename: str = "<unknown>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 0
        self.tokens = []
        self.indent_stack = [0]
        self.at_line_start = True
        self.paren_depth = 0

    def error(self, message):
        return LexerError(message, self.line, self.col)

    def peek(self, offset=0):
        idx = self.pos + offset
        return self.source[idx] if 0 <= idx < len(self.source) else "\0"

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        self.col += 1
        return ch

    def is_at_end(self):
        return self.pos >= len(self.source)

    def match_sequence(self, seq, token_type):
        if self.source[self.pos:self.pos + len(seq)] == seq:
            for _ in range(len(seq)):
                self.advance()
            self.tokens.append(Token(token_type, seq, self.line, self.col - len(seq)))
            return True
        return False

    def skip_comment(self):
        while not self.is_at_end() and self.peek() != "\n":
            self.advance()

    def skip_block_comment(self):
        depth = 1
        while depth > 0 and not self.is_at_end():
            if self.peek() == "/" and self.peek(1) == "*":
                self.advance()
                self.advance()
                depth += 1
            elif self.peek() == "*" and self.peek(1) == "/":
                self.advance()
                self.advance()
                depth -= 1
            else:
                ch = self.advance()
                if ch == "\n":
                    self.line += 1
                    self.col = 0

    def read_string(self, quote):
        result = []
        while not self.is_at_end():
            ch = self.advance()
            if ch == "\\":
                if self.is_at_end():
                    raise self.error("Unterminated string escape")
                esc = self.advance()
                esc_map = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "{": "{", "}": "}"}
                result.append(esc_map.get(esc, esc))
            elif ch == quote:
                return "".join(result)
            elif ch == "\n":
                raise self.error("Unterminated string")
            else:
                result.append(ch)
        raise self.error("Unterminated string")

    def read_number(self):
        start_col = self.col
        start_pos = self.pos
        ch = self.advance()

        if ch == "0" and self.peek() in ("x", "X"):
            self.advance()
            while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
                self.advance()
            value = self.source[start_pos:self.pos]
            return Token(TokenType.INTEGER, value, self.line, start_col)

        if ch == "0" and self.peek() in ("b", "B"):
            self.advance()
            while self.peek() in ("0", "1", "_"):
                self.advance()
            value = self.source[start_pos:self.pos]
            return Token(TokenType.INTEGER, value, self.line, start_col)

        value = ch
        while self.peek() and (self.peek().isdigit() or self.peek() == "_"):
            value += self.advance()

        is_float = False
        if self.peek() == "." and self.peek(1) and self.peek(1).isdigit():
            is_float = True
            value += self.advance()
            while self.peek() and (self.peek().isdigit() or self.peek() == "_"):
                value += self.advance()

        if self.peek() in ("e", "E"):
            is_float = True
            value += self.advance()
            if self.peek() in ("+", "-"):
                value += self.advance()
            while self.peek() and (self.peek().isdigit() or self.peek() == "_"):
                value += self.advance()

        return Token(TokenType.FLOAT if is_float else TokenType.INTEGER, value, self.line, start_col)

    def read_identifier(self):
        start_col = self.col
        start_pos = self.pos
        self.pos += 1
        self.col += 1
        while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
            self.advance()
        value = self.source[start_pos:self.pos]
        tok_type = KEYWORDS.get(value, TokenType.IDENTIFIER)
        return Token(tok_type, value, self.line, start_col)

    def scan_operator_or_punct(self):
        start_col = self.col
        ch = self.advance()

        three = ch + self.peek(0) + self.peek(1) if not self.is_at_end() else ""
        two = ch + self.peek(0) if not self.is_at_end() else ""

        if len(three) >= 3 and three in THREE_CHAR_SEQUENCES:
            for _ in range(2):
                self.advance()
            self.tokens.append(Token(THREE_CHAR_SEQUENCES[three], three, self.line, start_col))
            return

        if len(two) >= 2 and two in TWO_CHAR_SEQUENCES:
            self.advance()
            self.tokens.append(Token(TWO_CHAR_SEQUENCES[two], two, self.line, start_col))
            return

        if ch in ONE_CHAR_OPERATORS:
            self.tokens.append(Token(ONE_CHAR_OPERATORS[ch], ch, self.line, start_col))
            return

        if ch in SINGLE_CHAR_TOKENS:
            self.tokens.append(Token(SINGLE_CHAR_TOKENS[ch], ch, self.line, start_col))
            return

        if ch == "(":
            self.paren_depth += 1
            self.tokens.append(Token(TokenType.LPAREN, "(", self.line, start_col))
            return

        if ch == ")":
            self.paren_depth = max(0, self.paren_depth - 1)
            self.tokens.append(Token(TokenType.RPAREN, ")", self.line, start_col))
            return

        if ch == "\n":
            self.line += 1
            self.col = 0
            self.tokens.append(Token(TokenType.NEWLINE, "\n", self.line - 1, start_col))
            return

        if ch == "#":
            self.skip_comment()
            return

        raise self.error(f"Unexpected character: {ch!r}")

    def handle_indent(self):
        col = 0
        while self.peek() in (" ", "\t"):
            if self.peek() == " ":
                col += 1
            else:
                col += 4
            self.advance()

        if self.is_at_end():
            return
        if self.peek() == "\n":
            return
        if self.peek() == "#":
            self.skip_comment()
            return
        if self.peek() == "\0":
            return

        if col > self.indent_stack[-1]:
            self.indent_stack.append(col)
            self.tokens.append(Token(TokenType.INDENT, "", self.line, 1))
        elif col < self.indent_stack[-1]:
            while col < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, "", self.line, 1))
            if col != self.indent_stack[-1]:
                raise self.error("Inconsistent indentation")

    def tokenize(self):
        while not self.is_at_end():
            ch = self.peek()

            if ch in (" ", "\t"):
                self.advance()
                continue

            if ch == "\n":
                self.advance()
                self.line += 1
                self.col = 0
                if self.paren_depth == 0:
                    self.tokens.append(Token(TokenType.NEWLINE, "\n", self.line - 1, 1))
                    self.handle_indent()
                continue

            if ch == "#":
                self.skip_comment()
                continue

            if ch == "/" and self.peek(1) == "/":
                self.advance()
                self.advance()
                self.skip_comment()
                continue

            if ch == "/" and self.peek(1) == "*":
                self.advance()
                self.advance()
                self.skip_block_comment()
                continue

            if ch.isdigit():
                self.tokens.append(self.read_number())
                continue

            if ch.isalpha() or ch == "_":
                self.tokens.append(self.read_identifier())
                continue

            if ch == '"':
                if self.peek(1) == '"' and self.peek(2) == '"':
                    self.advance()
                    self.advance()
                    self.advance()
                    start_col = self.col - 3
                    result = []
                    while not self.is_at_end():
                        if self.peek() == '"' and self.peek(1) == '"' and self.peek(2) == '"':
                            self.advance()
                            self.advance()
                            self.advance()
                            self.tokens.append(Token(TokenType.STRING_BLOCK, "".join(result), self.line, start_col))
                            break
                        else:
                            c = self.advance()
                            if c == "\n":
                                self.line += 1
                                self.col = 0
                            result.append(c)
                    else:
                        raise self.error("Unterminated block string")
                else:
                    self.advance()
                    start_col = self.col
                    value = self.read_string('"')
                    self.tokens.append(Token(TokenType.STRING, value, self.line, start_col))
                continue

            if self.peek() == "/" and self.peek(1) == "*":
                self.advance()
                self.advance()
                self.skip_block_comment()
                continue

            self.scan_operator_or_punct()

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, "", self.line, 1))

        self.tokens.append(Token(TokenType.EOF, "", self.line, 1))
        return self.tokens
