from enum import Enum, auto

class TokenType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOLEAN = auto()
    NONE = auto()
    IDENTIFIER = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    POW = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    ASSIGN = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()

    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    DOT = auto()
    COLON = auto()
    ARROW = auto()
    SEMICOLON = auto()

    IF = auto()
    ELIF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    FUN = auto()
    RETURN = auto()
    CLASS = auto()
    IMPORT = auto()
    FROM = auto()
    TRY = auto()
    CATCH = auto()
    RAISE = auto()
    BREAK = auto()
    CONTINUE = auto()
    ASYNC = auto()
    AWAIT = auto()
    PASS = auto()
    IN = auto()
    IS = auto()
    LAMBDA = auto()

    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()

class Token:
    __slots__ = ('type', 'value', 'line', 'column')
    def __init__(self, type, value, line=1, column=1):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"

KEYWORDS = {
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "for": TokenType.FOR,
    "while": TokenType.WHILE,
    "fun": TokenType.FUN,
    "return": TokenType.RETURN,
    "class": TokenType.CLASS,
    "import": TokenType.IMPORT,
    "from": TokenType.FROM,
    "try": TokenType.TRY,
    "catch": TokenType.CATCH,
    "raise": TokenType.RAISE,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "async": TokenType.ASYNC,
    "await": TokenType.AWAIT,
    "pass": TokenType.PASS,
    "in": TokenType.IN,
    "is": TokenType.IS,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "true": TokenType.BOOLEAN,
    "false": TokenType.BOOLEAN,
    "none": TokenType.NONE,
    "lambda": TokenType.LAMBDA,
}
