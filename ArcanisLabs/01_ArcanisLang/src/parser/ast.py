from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class Position:
    line: int
    column: int


class Node:
    pass


# --- Expressions ---

class Expr(Node):
    pass

@dataclass
class LiteralExpr(Expr):
    value: Any
    pos: Position

@dataclass
class IdentifierExpr(Expr):
    name: str
    pos: Position

@dataclass
class BinaryExpr(Expr):
    left: Expr
    op: str
    right: Expr
    pos: Position

@dataclass
class UnaryExpr(Expr):
    op: str
    right: Expr
    pos: Position

@dataclass
class CallExpr(Expr):
    callee: Expr
    args: List[Expr]
    pos: Position

@dataclass
class IndexExpr(Expr):
    target: Expr
    index: Expr
    pos: Position

@dataclass
class AttributeExpr(Expr):
    target: Expr
    attr: str
    pos: Position

@dataclass
class IfExpr(Expr):
    condition: Expr
    then_branch: Expr
    else_branch: Optional[Expr]
    pos: Position

@dataclass
class MatchExpr(Expr):
    value: Expr
    arms: List["MatchArm"]
    pos: Position

@dataclass
class MatchArm(Node):
    pattern: Expr
    body: Expr
    pos: Position

@dataclass
class BlockExpr(Expr):
    statements: List["Stmt"]
    pos: Position

@dataclass
class ClosureExpr(Expr):
    params: List["Param"]
    body: Expr
    pos: Position

@dataclass
class ListExpr(Expr):
    elements: List[Expr]
    pos: Position

@dataclass
class MapExpr(Expr):
    entries: List[("Expr", "Expr")]
    pos: Position

@dataclass
class AIExpr(Expr):
    prompt: "PromptClause"
    model: Optional["ModelClause"]
    system: Optional["SystemClause"]
    pos: Position
    options: List["AIOption"] = field(default_factory=list)

@dataclass
class PromptClause(Node):
    expression: Expr
    pos: Position

@dataclass
class EmbedExpr(Expr):
    expression: Expr
    pos: Position

@dataclass
class ModelClause(Node):
    expression: Expr
    pos: Position

@dataclass
class SystemClause(Node):
    expression: Expr
    pos: Position

@dataclass
class AIOption(Node):
    name: str
    value: Expr
    pos: Position

@dataclass
class MemExpr(Expr):
    expression: Optional[Expr]
    pos: Position

@dataclass
class AsyncExpr(Expr):
    expression: Expr
    pos: Position

@dataclass
class AwaitExpr(Expr):
    expression: Expr
    pos: Position

@dataclass
class TryExpr(Expr):
    expression: Expr
    force: bool
    pos: Position

@dataclass
class RangeExpr(Expr):
    start: Expr
    end: Expr
    inclusive: bool
    pos: Position

@dataclass
class StructExpr(Expr):
    name: str
    fields: List[("str", "Expr")]
    pos: Position


# --- Statements ---

class Stmt(Node):
    pass

@dataclass
class ExpressionStmt(Stmt):
    expression: Expr
    pos: Position

@dataclass
class LetStmt(Stmt):
    name: str
    mutable: bool
    type_annotation: Optional["TypeRef"]
    value: Expr
    pos: Position

@dataclass
class ConstStmt(Stmt):
    name: str
    type_annotation: "TypeRef"
    value: Expr
    pos: Position

@dataclass
class ReturnStmt(Stmt):
    value: Optional[Expr]
    pos: Position

@dataclass
class BreakStmt(Stmt):
    pos: Position

@dataclass
class ContinueStmt(Stmt):
    pos: Position

@dataclass
class ThrowStmt(Stmt):
    value: Expr
    pos: Position

@dataclass
class PassStmt(Stmt):
    pos: Position

@dataclass
class DeferStmt(Stmt):
    call: Expr
    pos: Position

@dataclass
class ForStmt(Stmt):
    pattern: Expr
    iterable: Expr
    body: BlockExpr
    pos: Position

@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: BlockExpr
    pos: Position

@dataclass
class ImportStmt(Stmt):
    path: str
    names: Optional[List[str]]
    alias: Optional[str]
    pos: Position

@dataclass
class UseStmt(Stmt):
    path: List[str]
    alias: Optional[str]
    pos: Position

@dataclass
class Param(Node):
    name: str
    type_annotation: Optional["TypeRef"]
    default_value: Optional[Expr]
    pos: Position

@dataclass
class TypeRef(Node):
    name: str
    pos: Position
    generic_args: List["TypeRef"] = field(default_factory=list)


# --- Declarations ---

@dataclass
class FnDecl(Stmt):
    name: str
    params: List[Param]
    return_type: Optional[TypeRef]
    body: BlockExpr
    pub: bool
    async_: bool
    pos: Position

@dataclass
class StructDecl(Stmt):
    name: str
    fields: List[Param]
    pub: bool
    pos: Position

@dataclass
class EnumDecl(Stmt):
    name: str
    variants: List["EnumVariant"]
    pub: bool
    pos: Position

@dataclass
class EnumVariant(Node):
    name: str
    types: List[TypeRef]
    pos: Position

@dataclass
class TraitDecl(Stmt):
    name: str
    methods: List["TraitMethod"]
    pub: bool
    pos: Position

@dataclass
class TraitMethod(Node):
    name: str
    params: List[Param]
    return_type: Optional[TypeRef]
    pos: Position

@dataclass
class ImplDecl(Stmt):
    type_name: TypeRef
    trait_name: Optional[TypeRef]
    methods: List[FnDecl]
    pos: Position

@dataclass
class AgentDecl(Stmt):
    name: str
    role: Optional[Expr]
    model: Optional[Expr]
    memory: Optional[Expr]
    tools: List["AgentTool"]
    methods: List[FnDecl]
    pos: Position

@dataclass
class AgentTool(Node):
    name: str
    params: List[Param]
    return_type: Optional[TypeRef]
    pos: Position

@dataclass
class TypeAlias(Stmt):
    name: str
    target: TypeRef
    pos: Position

@dataclass
class ModDecl(Stmt):
    name: str
    pos: Position


# --- Top-level ---

@dataclass
class Program(Node):
    statements: List[Stmt]
    pos: Position
