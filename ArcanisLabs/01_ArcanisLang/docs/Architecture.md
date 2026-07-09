# ArcanisLang Architecture

## Compiler Pipeline

The ArcanisLang implementation will follow a classic compiler pipeline:

```
Source Code
    │
    ▼
┌─────────────┐
│   Lexer     │  Tokenizes source into tokens
└─────────────┘
    │
    ▼
┌─────────────┐
│   Parser    │  Builds AST from tokens
└─────────────┘
    │
    ▼
┌─────────────┐
│  Semantic   │  Type checking, name resolution
│  Analyzer   │
└─────────────┘
    │
    ▼
┌─────────────┐
│  Optimizer  │  AST-level optimizations
└─────────────┘
    │
    ▼
┌─────────────┐
│   CodeGen   │  Outputs bytecode for ArcanisVM
└─────────────┘
    │
    ▼
  Bytecode
```

## Implementation Phases

### Phase 1: Core (Weeks 1-4)
- Lexer: full token set
- Parser: expressions, statements, declarations
- AST: complete node types
- REPL: interactive evaluation

### Phase 2: Type System (Weeks 3-6)
- Type checker: inference, validation
- Generics: parametric polymorphism
- Traits: interface system

### Phase 3: AI Constructs (Weeks 5-8)
- Prompt/embed/model expressions
- Agent definitions
- Memory blocks

### Phase 4: Standard Library (Weeks 7-10)
- Core modules: io, collections, math
- AI modules: ai, embeddings
- HTTP, JSON, time

## Language Reference

See `spec/` directory for the full language specification, grammar, and standard library API.
