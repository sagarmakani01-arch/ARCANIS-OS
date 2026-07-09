from .tokens import Token, TokenType, KEYWORDS
from .errors import LexerError

class Lexer:
    def __init__(self, source, filename="<stdin>"):
        if source and source[-1] != '\n':
            source = source + '\n'
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.indent_stack = [0]
        self._tokenize()
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))

    def _error(self, msg):
        raise LexerError(msg, self.line, self.column)

    def _peek(self, offset=0):
        idx = self.pos + offset
        if idx >= len(self.source):
            return '\0'
        return self.source[idx]

    def _advance(self):
        if self.pos >= len(self.source):
            return '\0'
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _tokenize(self):
        at_line_start = True
        bracket_depth = 0

        while self.pos < len(self.source):
            ch = self._peek()

            if at_line_start and bracket_depth == 0:
                indent = 0
                while self.pos < len(self.source) and self._peek() in ' \t':
                    if self._peek() == '\t':
                        indent += 4
                    else:
                        indent += 1
                    self._advance()
                at_line_start = False
                pos_save = self.pos
                ch2 = self._peek()
                if ch2 == '\n' or ch2 == '#':
                    while self.pos < len(self.source) and self._peek() != '\n':
                        self._advance()
                    if self._peek() == '\n':
                        self._advance()
                    at_line_start = True
                    continue
                if ch2 == '\0':
                    break
                if indent > self.indent_stack[-1]:
                    self.indent_stack.append(indent)
                    self.tokens.append(Token(TokenType.INDENT, indent, self.line, self.column))
                elif indent < self.indent_stack[-1]:
                    while indent < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        self.tokens.append(Token(TokenType.DEDENT, indent, self.line, self.column))
                continue

            ch = self._peek()

            if ch == '\n':
                if bracket_depth == 0:
                    self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column))
                    at_line_start = True
                self._advance()
                if bracket_depth > 0:
                    at_line_start = False
                continue

            if ch in ' \t\r':
                self._advance()
                continue

            if ch == '#':
                while self.pos < len(self.source) and self._peek() != '\n':
                    self._advance()
                continue

            if ch == '"' or ch == "'":
                quote = ch
                self._advance()
                value = ''
                while self.pos < len(self.source):
                    ch2 = self._advance()
                    if ch2 == '\\':
                        esc = self._advance()
                        escape_map = {'n': '\n', 't': '\t', 'r': '\r', '0': '\0',
                                      '\\': '\\', "'": "'", '"': '"'}
                        value += escape_map.get(esc, esc)
                    elif ch2 == quote:
                        self.tokens.append(Token(TokenType.STRING, value, self.line, self.column))
                        break
                    else:
                        value += ch2
                else:
                    self._error("Unterminated string literal")
                continue

            if ch.isdigit():
                col = self.column
                value = ''
                is_float = False
                while self.pos < len(self.source) and (self._peek().isdigit() or (self._peek() == '.' and not is_float)):
                    if self._peek() == '.':
                        nxt = self._peek(1)
                        if nxt and not nxt.isdigit():
                            break
                        is_float = True
                    value += self._advance()
                if is_float:
                    self.tokens.append(Token(TokenType.FLOAT, float(value), self.line, col))
                else:
                    self.tokens.append(Token(TokenType.INTEGER, int(value), self.line, col))
                continue

            if ch.isalpha() or ch == '_':
                col = self.column
                value = ''
                while self.pos < len(self.source) and (self._peek().isalnum() or self._peek() == '_'):
                    value += self._advance()
                ttype = KEYWORDS.get(value, TokenType.IDENTIFIER)
                if ttype == TokenType.BOOLEAN:
                    tval = value == "true"
                elif ttype == TokenType.NONE:
                    tval = None
                else:
                    tval = value
                self.tokens.append(Token(ttype, tval, self.line, col))
                continue

            op_map = {
                '==': TokenType.EQ, '!=': TokenType.NEQ,
                '<=': TokenType.LTE, '>=': TokenType.GTE,
                '<': TokenType.LT, '>': TokenType.GT,
                '**': TokenType.POW,
                '+=': TokenType.PLUS_ASSIGN, '-=': TokenType.MINUS_ASSIGN,
                '+': TokenType.PLUS, '-': TokenType.MINUS,
                '*': TokenType.STAR, '/': TokenType.SLASH, '%': TokenType.PERCENT,
                '=': TokenType.ASSIGN,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                ',': TokenType.COMMA, '.': TokenType.DOT,
                ':': TokenType.COLON, ';': TokenType.SEMICOLON,
                '->': TokenType.ARROW,
            }
            open_brackets = {'(': TokenType.LPAREN, '[': TokenType.LBRACKET, '{': TokenType.LBRACE}
            close_brackets = {')': TokenType.RPAREN, ']': TokenType.RBRACKET, '}': TokenType.RBRACE}
            two_char = ch + self._peek(1) if self.pos + 1 < len(self.source) else ch
            if two_char in op_map:
                ttype = op_map[two_char]
                self._advance()
                self._advance()
                self.tokens.append(Token(ttype, two_char, self.line, self.column - 2))
                if two_char == '->':
                    pass
                elif two_char[0] in open_brackets:
                    bracket_depth += 1
                elif two_char[0] in close_brackets:
                    bracket_depth -= 1
                continue
            if ch in op_map:
                ttype = op_map[ch]
                self._advance()
                self.tokens.append(Token(ttype, ch, self.line, self.column - 1))
                if ch in open_brackets:
                    bracket_depth += 1
                elif ch in close_brackets:
                    bracket_depth -= 1
                continue

            self._error(f"Unexpected character: {ch!r}")

        while self.indent_stack[-1] > 0:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 0, self.line, self.column))
