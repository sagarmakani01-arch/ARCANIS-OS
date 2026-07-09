# ArcanisLang Language Specification v0.1

## Overview

ArcanisLang is a statically typed, AI-native programming language designed for clarity, safety, and intelligent computing.

## Philosophy

- **Readability matters** — Syntax should be clean and obvious.
- **AI is a first-class citizen** — Prompts, embeddings, and models are built-in types.
- **Safety by default** — Memory safe, type safe, and concurrency safe.
- **Progressive** — Simple for beginners, powerful for experts.

## Syntax

### Comments

```
// Single-line comment
/* Multi-line comment */
```

### Literals

```
42              // Int
3.14            // Float
true            // Bool
"hello"         // String
'c'             // Char
```

### Variables

```
let x = 42                  // Immutable, type inferred
let y: String = "hello"     // Immutable, explicit type
mut z = 10                  // Mutable variable
```

### Functions

```
fn add(a: Int, b: Int) -> Int {
    return a + b
}

fn greet(name: String) => "Hello, {name}"  // Expression body

// Higher-order function
fn map(list: List[Int], f: (Int) -> Int) -> List[Int] {
    // ...
}
```

### Control Flow

```
if x > 0 {
    print("positive")
} elif x == 0 {
    print("zero")
} else {
    print("negative")
}

while condition {
    // loop body
}

for item in list {
    // iteration
}
```

### Pattern Matching

```
match value {
    Ok(result) => process(result),
    Err(msg) => log(msg),
    _ => fallback(),
}
```

### Data Types

```
struct Point {
    x: Float
    y: Float
}

enum Result[T, E] {
    Ok(T)
    Err(E)
}
```

### AI-Native Constructs

```
// String interpolation with AI context
let greeting = "Hello, {name}"

// Prompt literal — sends a prompt to the default AI model
let answer = prompt "What is the capital of France?"

// Prompt with parameters
let answer = prompt("Translate to French: {text}", model: "gpt-4")

// Embedding — converts text to vector embedding
let vec = embed "This is some text to vectorize"

// Model invocation
let result = model("gpt-4").call("What is AI?")

// AI agent definition
agent MathAssistant {
    role: "You are a math tutor"
    tools: [calculate, graph]
}
```

### Modules

```
module math {
    fn abs(x: Int) -> Int {
        if x < 0 { -x } else { x }
    }
}

import math
import "vector" as vec
```

## Type System

### Primitive Types
- `Int` — Integer (platform-dependent size)
- `Float` — IEEE 754 double-precision
- `Bool` — Boolean (true/false)
- `String` — UTF-8 string
- `Char` — Unicode character

### AI Types
- `Prompt` — A prompt template with parameters
- `Embedding` — A vector embedding
- `Model` — An AI model reference
- `Agent` — An AI agent definition

### Compound Types
- `List[T]` — Homogeneous list
- `Map[K, V]` — Key-value map
- `Option[T]` — Optional value (Some/None)
- `Result[T, E]` — Success or error

## Memory Model

- Values are owned by default (Rust-inspired ownership)
- Borrowing via `&` references
- Automatic reference counting for shared ownership
- No manual memory management

## Concurrency

- `async`/`await` for asynchronous operations
- Lightweight tasks (not OS threads)
- Channels for communication between tasks
- AI operations are async by default
