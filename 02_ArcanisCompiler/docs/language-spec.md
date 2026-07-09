# ArcanisLang Language Specification

## Overview

ArcanisLang is a statically-typed, compiled programming language designed for clarity and safety. It features a C-like syntax with strong type inference and modern language features.

## Lexical Structure

### Comments
- Line comments: `// ...`
- Block comments: `/* ... */` (nestable)

### Keywords
`let`, `fun`, `if`, `else`, `while`, `return`, `true`, `false`, `print`, `println`, `readInt`, `readString`

### Literals
- Integer: `[0-9]+`
- Float: `[0-9]+\.[0-9]+`
- String: `"[^"]*"`
- Boolean: `true`, `false`
- Unit: `()`

### Operators
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Logical: `&&`, `||`, `!`
- Assignment: `=`
- Arrow: `->`

## Syntax

### Program
A program consists of optional function declarations followed by optional statements.

### Function Declaration
```
fun identifier(param1: Type1, param2: Type2): ReturnType {
  statements
}
```

### Variable Declaration
```
let identifier: Type = expression;
let identifier = expression;  // type inference
```

### Statements
- Block: `{ statements }`
- Expression: `expression;`
- If: `if (expression) statement else statement`
- While: `while (expression) statement`
- Return: `return expression;`

### Expressions
- Primary: literals, identifiers, `(expression)`
- Unary: `-expression`, `!expression`
- Binary: `expression op expression`
  - Multiplicative: `*`, `/`, `%`
  - Additive: `+`, `-`
  - Comparison: `<`, `>`, `<=`, `>=`
  - Equality: `==`, `!=`
  - Logical AND: `&&`
  - Logical OR: `||`
  - Assignment: `=`
- Call: `identifier(args)`

## Type System

### Primitive Types
- `Int`: 64-bit signed integer
- `Float`: 64-bit IEEE 754 floating point
- `Bool`: Boolean (true/false)
- `String`: Immutable UTF-8 string
- `Unit`: Unit type (no value)

### Type Rules

#### Arithmetic
- `Int op Int -> Int`
- `Float op Float -> Float`
- `String + String -> String` (concatenation)
- Mixed types are type errors

#### Comparison
- `Int cmp Int -> Bool`
- `Float cmp Float -> Bool`
- `Bool == Bool -> Bool`
- `Bool != Bool -> Bool`

#### Logical
- `Bool && Bool -> Bool`
- `Bool || Bool -> Bool`
- `!Bool -> Bool`

## Built-in Functions

| Function       | Signature                  | Description                    |
|---------------|---------------------------|--------------------------------|
| `print`       | `(String) -> Unit`        | Print string to stdout         |
| `println`     | `(String) -> Unit`        | Print string with newline      |
| `printlnInt`  | `(Int) -> Unit`           | Print integer with newline     |
| `readInt`     | `() -> Int`               | Read integer from stdin        |
| `readString`  | `() -> String`            | Read line from stdin           |
| `intToString` | `(Int) -> String`         | Convert integer to string      |
| `floatToString`| `(Float) -> String`      | Convert float to string        |
