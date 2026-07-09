# ArcanisLang Language Specification v0.1

> **Status:** Draft — Subject to change
> **Phase:** Design

---

## 1. Introduction

ArcanisLang is a statically typed, AI-native programming language designed as the foundation of the Arcanis ecosystem.

### Design Goals

1. **AI-native** — Prompts, embeddings, and model interactions are first-class language constructs.
2. **Beginner-friendly** — Clean syntax with gradual typing and helpful compiler messages.
3. **Safe by default** — Memory safety, type safety, and concurrency safety enforced at compile time.
4. **Self-hosting** — Designed to eventually compile itself.
5. **Cross-platform** — Targets ArcanisVM, with native compilation planned.

---

## 2. Syntax

### 2.1 Whitespace and Comments

ArcanisLang uses indentation-based blocks (like Python). Spaces and tabs are both valid but must be consistent within a file.

```arcanis
# Single-line comment

/*
 * Multi-line comment
 * Documentation comments use /** ... */
 */
```

### 2.2 Literals

```arcanis
# Numeric
42              # i32
42_000          # Underscore separators
3.14            # f64
0xFF            # Hex
0b1010          # Binary

# String
"Hello, World!"       # String
"Hello {name}!"       # Interpolation
"""Multi-line"""      # Block string

# Boolean
true
false

# Collection
[1, 2, 3]             # List
{"key": "value"}       # Map
{1, 2, 3}              # Set

# AI Literals
prompt("Explain AI")   # Prompt literal
embed("text")          # Embedding literal
```

### 2.3 Identifiers

```arcanis
# Standard identifiers
my_variable
myFunction
MyType
MY_CONSTANT

# Must start with a letter or underscore
# Case-sensitive
```

### 2.4 Keywords

```
let, const, fn, if, else, for, while, return, break, continue,
true, false, nil, import, from, as, struct, enum, trait, impl,
match, pub, mut, async, await, try, throw, ai, prompt, embed,
agent, model, role, tool, memory, self, super, type, use, mod
```

---

## 3. Type System

### 3.1 Primitive Types

| Type | Description | Size |
|------|-------------|------|
| `i8` / `i16` / `i32` / `i64` | Signed integers | 1-8 bytes |
| `u8` / `u16` / `u32` / `u64` | Unsigned integers | 1-8 bytes |
| `f32` / `f64` | Floating point | 4-8 bytes |
| `bool` | Boolean | 1 byte |
| `String` | UTF-8 string | Variable |
| `char` | Unicode code point | 4 bytes |
| `nil` | Null/absence of value | 0 bytes |

### 3.2 Compound Types

```arcanis
# Arrays
let arr: [i32] = [1, 2, 3]
let fixed: [i32; 3] = [1, 2, 3]   # Fixed-size

# Tuples
let pair: (i32, String) = (42, "hello")

# Option (nullable)
let maybe: Option<String> = nil
let value = maybe ?? "default"    # Nil-coalescing

# Result (error handling)
let result: Result<String, Error> = try risky_operation()
```

### 3.3 User-Defined Types

```arcanis
# Struct
struct Point {
    x: f64
    y: f64
}

# Enum
enum Status {
    Active
    Inactive
    Paused(String)
}

# Trait (like interfaces)
trait Drawable {
    fn draw(self)
}

# Implementing a trait
impl Drawable for Circle {
    fn draw(self) {
        # ...
    }
}
```

### 3.4 AI Types

```arcanis
# Prompt — represents a prompt to an AI model
let p: Prompt = prompt("Tell me a joke")

# Embedding — vector representation of text
let emb: Embedding = embed("Some text")

# Model — reference to an AI model
let m: Model = model("arcanis-default")

# Agent — AI agent definition
agent MathTutor {
    role: "Math tutor for beginners"
    
    fn explain(topic: String) -> String {
        ai prompt("Explain {topic} simply") model(self.model)
    }
}

# Memory — persistent AI memory block
let ctx: Memory = memory("session-123")
```

### 3.5 Type Inference

Types are inferred when possible but can be explicitly annotated:

```arcanis
let x = 42                    # inferred i32
let y: f64 = 42               # explicit f64
let z = add(1, 2)             # inferred from return type
```

---

## 4. Variables and Constants

```arcanis
# Immutable by default
let name = "Arcanis"

# Mutable
let mut counter = 0
counter += 1

# Constants (compile-time)
const MAX_SIZE: i32 = 1024

# Shadowing allowed
let value = "hello"
let value = value.len()        # shadows with new type
```

---

## 5. Functions

### 5.1 Function Definitions

```arcanis
# Basic function
fn greet(name: String) -> String {
    return "Hello, {name}!"
}

# Expression body
fn add(a: i32, b: i32) -> i32 = a + b

# Multiple return values
fn divide(a: i32, b: i32) -> (i32, i32) {
    return (a / b, a % b)
}

# Default parameters
fn connect(host: String = "localhost", port: i32 = 8080) {
    # ...
}
```

### 5.2 Higher-Order Functions

```arcanis
# Functions as values
let calc: fn(i32, i32) -> i32 = add

# Closures
let numbers = [1, 2, 3, 4, 5]
let doubled = numbers.map(fn(x) { x * 2 })
let filtered = numbers.filter(fn(x) { x > 2 })

# Shorthand closure
let tripled = numbers.map(|x| x * 3)
```

---

## 6. Control Flow

### 6.1 Conditionals

```arcanis
if score >= 90 {
    "A"
} else if score >= 80 {
    "B"
} else {
    "C"
}  # if expressions return values

# Pattern matching
match value {
    1 => "one"
    2 => "two"
    _ => "other"
}
```

### 6.2 Loops

```arcanis
# For loop
for i in 0..10 {
    print(i)
}

# For-each
for item in collection {
    print(item)
}

# While loop
let mut x = 0
while x < 10 {
    x += 1
}
```

---

## 7. AI-Native Constructs

### 7.1 AI Expressions

The core AI interaction primitive:

```arcanis
# Simple prompt
let answer = ai prompt("What is 2 + 2?")
# answer: String

# Prompt with system message
let response = ai 
    prompt("Explain quantum computing")
    system("You are a physicist")
    model("gpt-4")
    temperature(0.7)

# Prompt with context
let result = ai
    prompt("Summarize this")
    context(document)
    max_tokens(500)
```

### 7.2 Embedding Operations

```arcanis
# Create embedding
let emb = embed("Text to embed")

# Similarity operations
let sim = cosine_similarity(emb1, emb2)
let similar = semantic_search(query, document_set, top_k=5)

# Embedding math
let combined = emb1 + emb2      # Vector addition
let scaled = emb * 0.5          # Scaling
```

### 7.3 Agent Definitions

```arcanis
agent CustomerSupport {
    role: "Customer support representative"
    model: "arcanis-support-v1"
    memory: true                  # Enable conversation memory
    
    # Tools the agent can use
    tool lookup_order(id: String) -> Order
    tool refund_order(id: String) -> Result<String, Error>
    
    # Skills
    fn handle_inquiry(query: String) -> String {
        let intent = ai prompt("Classify: {query}") 
        
        match intent {
            "refund" => self.process_refund(query)
            "status" => self.check_status(query)
            _ => ai prompt("Respond to: {query}")
        }
    }
}

# Instantiate and use
let support = CustomerSupport()
let response = support.handle_inquiry("Where is my order?")
```

### 7.4 Model References

```arcanis
# Model as first-class value
let m: Model = model("gpt-4")
let models: [Model] = [model("gpt-4"), model("claude-3")]

# Model configuration
let configured = model("custom")
    .temperature(0.3)
    .max_tokens(2000)
    .top_p(0.9)
```

### 7.5 Memory Blocks

```arcanis
# Persistent memory
let mem = memory("user-123")
mem.store("preference", "dark mode")
let pref = mem.recall("preference")

# Session memory
let session = memory(ttl: 3600)    # Auto-expire after 1 hour
session.add_message({"role": "user", "content": "Hello"})
```

---

## 8. Modules and Imports

```arcanis
# Import
import "std/io"
import "std/ai"
import "http"

# Selective import
import "std/collections" { List, Map }

# Named import
import "math" as math_lib

# Module definition (one file = one module)
# File: math/add.arc
pub fn add(a: i32, b: i32) -> i32 = a + b

# Internal (private by default)
fn helper() { }
```

---

## 9. Error Handling

```arcanis
# Try expression
let result = try risky_operation()        # Returns Result
let value = try! risky_operation()        # Panics on error

# Throw errors
fn validate(age: i32) -> Result<i32, String> {
    if age < 0 {
        throw "Age cannot be negative"
    }
    return age
}

# Pattern match on errors
match divide(10, 0) {
    Ok(value) => print(value)
    Err(msg) => print("Error: {msg}")
}

# Defer (cleanup)
fn read_file(path: String) -> Result<String, Error> {
    let file = try open(path)
    defer file.close()
    return file.read_all()
}
```

---

## 10. Concurrency

```arcanis
# Async function
async fn fetch_data(url: String) -> Result<String, Error> {
    let response = await http.get(url)
    return response.body
}

# Concurrent execution
let result1 = async fetch_data("https://api.example.com/1")
let result2 = async fetch_data("https://api.example.com/2")
let (data1, data2) = await all(result1, result2)

# Channels for communication
let (tx, rx) = channel<String>()
async fn worker(tx: Sender<String>) {
    tx.send("Done!")
}
```

---

## 11. Memory Model

ArcanisLang uses automatic memory management (garbage collection) by default, with optional ownership annotations for performance-critical code.

```arcanis
# Default: garbage collected
let data = create_large_dataset()

# Ownership annotation for manual management
let buf: own[u8] = allocate_buffer(1024)
// buf is freed when it goes out of scope

# Borrowing
fn process(data: &String) {
    print(data)    # Read-only borrow
}

fn modify(data: &mut String) {
    data.push_str("!")    # Mutable borrow
}
```

---

## 12. Standard Library Overview

### `std/io` — Input/Output
- `print(...)`, `println(...)`
- `read_line()`, `read_file(path)`, `write_file(path, content)`

### `std/ai` — AI Primitives
- `prompt(text)`, `embed(text)`, `model(name)`
- `cosine_similarity(a, b)`, `semantic_search(query, corpus)`

### `std/collections` — Data Structures
- `List<T>`, `Map<K, V>`, `Set<T>`, `Queue<T>`, `Stack<T>`

### `std/http` — HTTP Client/Server
- `get(url)`, `post(url, body)`, `Server`, `Request`, `Response`

### `std/time` — Time Utilities
- `now()`, `sleep(ms)`, `Duration`, `Timer`

### `std/json` — JSON Processing
- `parse(text)`, `stringify(value)`

### `std/math` — Mathematics
- `sin`, `cos`, `sqrt`, `abs`, `random`, `pi`, `e`

### `std/net` — Networking
- `TcpStream`, `UdpSocket`, `TcpListener`

---

## 13. Formal Grammar (EBNF)

```
program        = { statement }
statement      = let_decl | const_decl | fn_decl | struct_decl 
               | enum_decl | trait_decl | impl_decl | agent_decl
               | import_stmt | expression_stmt | return_stmt
               | if_expr | match_expr | for_stmt | while_stmt
               | block

block          = "{" { statement } "}"
               | indented_block

let_decl       = "let" ["mut"] identifier [":" type] "=" expression
const_decl     = "const" identifier ":" type "=" expression
fn_decl        = "fn" identifier "(" [params] ")" ["->" type] block
struct_decl    = "struct" identifier "{" { field } "}"
enum_decl      = "enum" identifier "{" { variant } "}"
trait_decl     = "trait" identifier "{" { fn_signature } "}"
impl_decl      = "impl" type "for" type "{" { fn_decl } "}"
agent_decl     = "agent" identifier "{" { agent_field } "}"

expression     = literal | identifier | binary_op | unary_op
               | call_expr | if_expr | match_expr | ai_expr
               | prompt_expr | embed_expr | block | paren_expr

ai_expr        = "ai" prompt_expr [model_clause] [options]
prompt_expr    = "prompt" "(" expression ")"
embed_expr     = "embed" "(" expression ")"
model_clause   = "model" "(" expression ")"
```

---

## 14. Future Considerations

### Phase 2 Features
- Generics: `fn identity<T>(x: T) -> T = x`
- Macros: `macro name { ... }`
- Pattern matching on complex types
- Algebraic effects

### Phase 3 Features
- Self-hosting compiler
- Compile-time evaluation
- Dependent types for AI safety

---

*This specification is a living document and will evolve as ArcanisLang is implemented.*
