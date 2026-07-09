# ArcanisLang Grammar Reference v0.1

> Formal EBNF grammar for ArcanisLang.

---

## Notation

- `"..."` — Terminal string
- `[...]` — Optional
- `{...}` — Zero or more repetitions
- `(...)` — Grouping
- `|` — Alternative
- `a*` — Zero or more of `a`
- `a+` — One or more of `a`

---

## Lexical Grammar

```
letter         = "A".."Z" | "a".."z" | "_"
digit          = "0".."9"
hex_digit      = digit | "A".."F" | "a".."f"
bin_digit      = "0" | "1"

identifier     = (letter) { letter | digit }
integer        = dec_integer | hex_integer | bin_integer
dec_integer    = digit { digit | "_" }
hex_integer    = "0x" hex_digit { hex_digit | "_" }
bin_integer    = "0b" bin_digit { bin_digit | "_" }
float          = digit { digit | "_" } "." digit { digit | "_" }
               [ ("e" | "E") ["+" | "-"] digit { digit | "_" } ]

string         = '"' { char | escape | interpolation } '"'
string_block   = '"""' { char } '"""'
char           = ? any Unicode character except '"' or '\' or '{' ?
escape         = "\\" ("n" | "t" | "r" | '"' | "\\" | "{" | "}")
interpolation  = "{" expression "}"

comment        = "#" { char } newline
comment_block  = "/*" { char } "*/"
doc_comment    = "/**" { char } "*/"
```

## Syntax Grammar

### Program Structure

```
program        = { statement }

statement      = let_decl
               | const_decl
               | fn_decl
               | struct_decl
               | enum_decl
               | trait_decl
               | impl_decl
               | agent_decl
               | import_decl
               | export_decl
               | type_alias
               | use_decl
               | expression_stmt
               | return_stmt
               | throw_stmt
               | defer_stmt
               | block

expression_stmt = expression newline
return_stmt    = "return" [expression] newline
throw_stmt     = "throw" expression newline
defer_stmt     = "defer" expression newline
```

### Declarations

```
let_decl       = "let" ["mut"] identifier [":" type] "=" expression
const_decl     = "const" identifier ":" type "=" expression
type_alias     = "type" identifier "=" type

fn_decl        = "fn" identifier [generic_params] "(" [fn_params] ")" 
                 ["->" return_type] (block | "=" expression)
fn_params      = fn_param { "," fn_param }
fn_param       = identifier ":" type ["=" expression]
return_type    = type | "(" [ type { "," type } ] ")"

struct_decl    = "struct" identifier [generic_params] "{" { field } "}"
field          = identifier ":" type

enum_decl      = "enum" identifier [generic_params] "{" { variant } "}"
variant        = identifier ["(" [ type { "," type } ] ")"]

trait_decl     = "trait" identifier [generic_params] "{" { trait_item } "}"
trait_item     = fn_signature | type_decl

fn_signature   = "fn" identifier "(" [fn_params] ")" ["->" return_type]

impl_decl      = "impl" [generic_params] type ["for" type] block

agent_decl     = "agent" identifier "{" { agent_item } "}"
agent_item     = role_decl | model_decl | tool_decl | fn_decl | memory_decl
role_decl      = "role" ":" expression
model_decl     = "model" ":" expression
tool_decl      = "tool" identifier "(" [fn_params] ")" ["->" return_type]
memory_decl    = "memory" ":" boolean

import_decl    = "import" string ["{" import_items "}"] ["as" identifier]
export_decl    = "pub" (fn_decl | struct_decl | enum_decl | const_decl | type_alias)

use_decl       = "use" identifier_path ["as" identifier]
identifier_path = identifier {"." identifier}
```

### Expressions

```
expression     = assignment_expr
assignment_expr = ternary_expr [("=" | "+=" | "-=" | "*=" | "/=") assignment_expr]

ternary_expr   = or_expr ["?" expression ":" expression]

or_expr        = and_expr { "or" and_expr }
and_expr       = compare_expr { "and" compare_expr }
compare_expr   = range_expr { ("==" | "!=" | "<" | ">" | "<=" | ">=") range_expr }

range_expr     = add_expr [(".." | "..=") add_expr]

add_expr       = mul_expr { ("+" | "-") mul_expr }
mul_expr       = prefix_expr { ("*" | "/" | "%") prefix_expr }

prefix_expr    = ["-" | "!" | "~"] postfix_expr

postfix_expr   = primary_expr { postfix_op }
postfix_op     = "." identifier
               | "[" expression "]"
               | "(" [expression {"," expression}] ")"
               | "?"               # nil-aware
               | "!"              # force-unwrap

primary_expr   = literal
               | identifier
               | "(" expression ")"
               | block
               | if_expr
               | match_expr
               | ai_expr
               | prompt_expr
               | embed_expr
               | model_expr
               | memory_expr
               | async_expr
               | await_expr
               | try_expr
               | list_expr
               | map_expr
               | set_expr
               | closure_expr
               | struct_expr
               | fn_reference
```

### AI-Specific Expressions

```
ai_expr        = "ai" prompt_expr [model_clause] [ai_options] [system_clause]
prompt_expr    = "prompt" "(" expression ")"
embed_expr     = "embed" "(" expression ")"
model_expr     = "model" "(" expression ")" [model_options]
memory_expr    = "memory" "(" [expression] ")" [memory_options]

model_clause   = "model" "(" expression ")"
system_clause  = "system" "(" expression ")"

ai_options     = { ai_option }
ai_option      = temperature_clause | max_tokens_clause | top_p_clause
temperature_clause = "temperature" "(" expression ")"
max_tokens_clause  = "max_tokens" "(" expression ")"
top_p_clause       = "top_p" "(" expression ")"

model_options  = { model_option }
model_option   = temperature_clause | max_tokens_clause | top_p_clause
```

### Control Flow

```
if_expr        = "if" expression block { "else" "if" expression block } ["else" (block | if_expr)]

match_expr     = "match" expression "{" { match_arm } "}"
match_arm      = pattern "=>" expression [","]
pattern        = literal | identifier | wildcard_pattern | destructure_pattern
wildcard_pattern = "_"
destructure_pattern = type_name "(" [pattern {"," pattern}] ")"

for_stmt       = "for" pattern "in" expression block
while_stmt     = "while" expression block
break_stmt     = "break"
continue_stmt  = "continue"

closure_expr   = "fn" "(" [fn_params] ")" block
               | "|" [identifier {"," identifier}] "|" expression

async_expr     = "async" expression
await_expr     = "await" expression

try_expr       = "try" ["!"] expression
```

### Collections

```
list_expr      = "[" [expression {"," expression}] "]"
map_expr       = "{" expression ":" expression {"," expression ":" expression} "}"
set_expr       = "{" expression {"," expression} "}"

struct_expr    = type_name "{" [field_init {"," field_init}] "}"
field_init     = identifier ":" expression
```

### Types

```
type           = primitive_type
               | identifier                               # named type
               | "[" type [":" expression] "]"             # array type
               | "(" [type {"," type}] ")"                # tuple type
               | type "->" type                           # function type
               | type "?"                                 # optional
               | type "!"                                 # result
               | "own" "[" type "]"                       # owned
               | "&" type                                 # borrowed
               | "&" "mut" type                           # mutable borrowed

primitive_type = "i8" | "i16" | "i32" | "i64"
               | "u8" | "u16" | "u32" | "u64"
               | "f32" | "f64"
               | "bool" | "String" | "char"
               | "nil" | "never"

generic_params = "<" identifier {"," identifier} ">"
```

### Literals

```
literal        = integer | float | string | string_block | bool_literal
               | nil_literal
bool_literal   = "true" | "false"
nil_literal    = "nil"
```
