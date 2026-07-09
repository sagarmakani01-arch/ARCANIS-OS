class ArcanisError(Exception):
    def __init__(self, message, line=None, column=None):
        self.line = line
        self.column = column
        if line is not None and column is not None:
            msg = f"[Line {line}:{column}] {message}"
        elif line is not None:
            msg = f"[Line {line}] {message}"
        else:
            msg = message
        super().__init__(msg)

class LexerError(ArcanisError):
    pass

class ParserError(ArcanisError):
    pass

class SemanticError(ArcanisError):
    pass

class RuntimeError_(ArcanisError):
    pass
