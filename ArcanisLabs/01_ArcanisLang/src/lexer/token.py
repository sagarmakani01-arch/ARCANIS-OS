from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    STRING_BLOCK = auto()

    # Identifiers
    IDENTIFIER = auto()

    # Keywords
    LET = auto()
    CONST = auto()
    FN = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()
    IMPORT = auto()
    FROM = auto()
    AS = auto()
    STRUCT = auto()
    ENUM = auto()
    TRAIT = auto()
    IMPL = auto()
    MATCH = auto()
    PUB = auto()
    MUT = auto()
    ASYNC = auto()
    AWAIT = auto()
    TRY = auto()
    THROW = auto()
    DEFER = auto()
    AI = auto()
    PROMPT = auto()
    EMBED = auto()
    MODEL = auto()
    AGENT = auto()
    ROLE = auto()
    TOOL = auto()
    MEMORY = auto()
    SYSTEM = auto()
    TEMPERATURE = auto()
    MAX_TOKENS = auto()
    TOP_P = auto()
    AND = auto()
    OR = auto()
    IN = auto()
    SELF = auto()
    SUPER = auto()
    TYPE = auto()
    USE = auto()
    MOD = auto()
    PASS = auto()
    PROMPT_KW = auto()
    ALL = auto()

    # Punctuation
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    COMMA = auto()        # ,
    DOT = auto()          # .
    COLON = auto()        # :
    SEMICOLON = auto()    # ;
    ARROW = auto()        # ->
    FAT_ARROW = auto()    # =>
    DOTDOT = auto()       # ..
    DOTDOT_EQ = auto()    # ..=
    PIPE = auto()         # |
    AMPERSAND = auto()    # &
    UNDERSCORE = auto()   # _
    HASH = auto()         # #
    AT = auto()           # @

    # Operators
    PLUS = auto()         # +
    MINUS = auto()        # -
    STAR = auto()         # *
    SLASH = auto()        # /
    PERCENT = auto()      # %
    EQ = auto()           # =
    EQ_EQ = auto()        # ==
    BANG = auto()         # !
    BANG_EQ = auto()      # !=
    LT = auto()           # <
    GT = auto()           # >
    LT_EQ = auto()        # <=
    GT_EQ = auto()        # >=
    PLUS_EQ = auto()      # +=
    MINUS_EQ = auto()     # -=
    STAR_EQ = auto()      # *=
    SLASH_EQ = auto()     # /=
    QUESTION = auto()     # ?
    QUESTION_QUESTION = auto()  # ??
    PLUS_PLUS = auto()    # ++

    # Special
    INDENT = auto()
    DEDENT = auto()
    NEWLINE = auto()
    EOF = auto()
    ERROR = auto()


KEYWORDS = {
    "let": TokenType.LET,
    "const": TokenType.CONST,
    "fn": TokenType.FN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "for": TokenType.FOR,
    "while": TokenType.WHILE,
    "return": TokenType.RETURN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "nil": TokenType.NIL,
    "import": TokenType.IMPORT,
    "from": TokenType.FROM,
    "as": TokenType.AS,
    "struct": TokenType.STRUCT,
    "enum": TokenType.ENUM,
    "trait": TokenType.TRAIT,
    "impl": TokenType.IMPL,
    "match": TokenType.MATCH,
    "pub": TokenType.PUB,
    "mut": TokenType.MUT,
    "async": TokenType.ASYNC,
    "await": TokenType.AWAIT,
    "try": TokenType.TRY,
    "throw": TokenType.THROW,
    "defer": TokenType.DEFER,
    "ai": TokenType.AI,
    "prompt": TokenType.PROMPT,
    "embed": TokenType.EMBED,
    "model": TokenType.MODEL,
    "agent": TokenType.AGENT,
    "role": TokenType.ROLE,
    "tool": TokenType.TOOL,
    "memory": TokenType.MEMORY,
    "system": TokenType.SYSTEM,
    "temperature": TokenType.TEMPERATURE,
    "max_tokens": TokenType.MAX_TOKENS,
    "top_p": TokenType.TOP_P,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "in": TokenType.IN,
    "self": TokenType.SELF,
    "super": TokenType.SUPER,
    "type": TokenType.TYPE,
    "use": TokenType.USE,
    "mod": TokenType.MOD,
    "pass": TokenType.PASS,
    "all": TokenType.ALL,
    "_": TokenType.UNDERSCORE,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"
