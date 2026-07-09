# ArcanisVM Bytecode Reference

## Instruction Format

Each instruction is a 32-bit word:
- Bits 0-7: Opcode (256 max)
- Bits 8-31: Argument (24-bit, 16M max)

## Opcode Table

| Code | Mnemonic           | Arg      | Stack Effect         | Description                    |
|------|--------------------|----------|----------------------|--------------------------------|
| 0    | HALT               | -        | -                    | Stop execution                 |
| 1    | NOP                | -        | -                    | No operation                   |
| 2    | LOAD_CONST         | idx      | => val               | Load constant                  |
| 3    | LOAD_NIL           | -        | => nil               | Push nil                       |
| 4    | LOAD_TRUE          | -        | => true              | Push true                      |
| 5    | LOAD_FALSE         | -        | => false             | Push false                     |
| 6    | LOAD_INT_0         | -        | => 0                 | Push integer 0                 |
| 7    | LOAD_INT_1         | -        | => 1                 | Push integer 1                 |
| 8    | LOAD_LOCAL         | slot     | => val               | Load local variable            |
| 9    | STORE_LOCAL        | slot     | val =>               | Store local variable           |
| 10   | LOAD_GLOBAL        | idx      | => val               | Load global variable           |
| 11   | STORE_GLOBAL       | idx      | val =>               | Store global variable          |
| 12   | LOAD_UPVALUE       | idx      | => val               | Load upvalue (closure)         |
| 13   | STORE_UPVALUE      | idx      | val =>               | Store upvalue                  |
| 14   | LOAD_MODULE        | idx      | => val               | Load module value              |
| 15   | STORE_MODULE       | idx      | val =>               | Store module value             |
| 16   | ADD                | -        | a b => a+b           | Add (int/float/string)         |
| 17   | SUB                | -        | a b => a-b           | Subtract                       |
| 18   | MUL                | -        | a b => a*b           | Multiply                       |
| 19   | DIV                | -        | a b => a/b           | Divide                         |
| 20   | MOD                | -        | a b => a%b           | Modulo                         |
| 21   | NEG                | -        | a => -a              | Negate                         |
| 22   | EQ                 | -        | a b => a==b          | Equal                          |
| 23   | NE                 | -        | a b => a!=b          | Not equal                      |
| 24   | LT                 | -        | a b => a<b           | Less than                      |
| 25   | GT                 | -        | a b => a>b           | Greater than                   |
| 26   | LE                 | -        | a b => a<=b          | Less or equal                  |
| 27   | GE                 | -        | a b => a>=b          | Greater or equal               |
| 28   | AND                | -        | a b => a&&b          | Logical AND                    |
| 29   | OR                 | -        | a b => a\|\|b        | Logical OR                     |
| 30   | NOT                | -        | a => !a              | Logical NOT                    |
| 31   | JMP                | offset   | -                    | Unconditional jump             |
| 32   | JMP_IF_FALSE       | offset   | val =>               | Jump if false (keep val)       |
| 33   | JMP_IF_TRUE        | offset   | val =>               | Jump if true (keep val)        |
| 34   | JMP_IF_FALSE_POP   | offset   | val =>               | Jump if false (pop val)        |
| 35   | LOOP               | offset   | -                    | Loop backward                   |
| 36   | CALL               | argc     | fn args... => result | Call function                   |
| 37   | CALL_TAIL          | argc     | fn args... => result | Tail call                       |
| 38   | RETURN             | -        | => nil               | Return nil                      |
| 39   | RETURN_VALUE       | -        | val =>               | Return value                    |
| 40   | CLOSURE            | fn_idx   | => closure           | Create closure                  |
| 41   | CLOSE_UPVALUE      | -        | val =>               | Close upvalue                   |
| 42   | NEW_ARRAY          | count    | items... => array    | Create array                    |
| 43   | NEW_MAP            | count    | k1 v1... => map      | Create map                      |
| 44   | INDEX_GET          | -        | obj idx => val       | Index access                    |
| 45   | INDEX_SET          | -        | obj idx val => val   | Index assignment                |
| 46   | NEW_OBJECT         | cls_idx  | => instance          | Create class instance           |
| 47   | PROP_GET           | name_idx | obj => val           | Property access                 |
| 48   | PROP_SET           | name_idx | obj val =>           | Property assignment             |
| 49   | METHOD             | name_idx | class method =>      | Define method                   |
| 50   | INVOKE             | name_idx | obj args... => val   | Call method                     |
| 51   | INHERIT            | -        | super sub =>         | Set up inheritance              |
| 52   | GET_SUPER          | name_idx | super obj => method  | Get superclass method           |
| 53   | SCOPE_ENTER        | -        | -                    | Enter scope                     |
| 54   | SCOPE_EXIT         | -        | -                    | Exit scope                      |
| 55   | DEFINE_GLOBAL      | idx      | val =>               | Define global variable          |
| 56   | POP                | -        | val =>               | Discard top of stack            |
| 57   | DUP                | -        | a => a a             | Duplicate top of stack          |
| 58   | SWAP               | -        | a b => b a           | Swap top two values             |
| 59   | BUILD_STRING       | count    | parts... => str      | Build string from parts         |
| 60   | IMPORT             | mod_idx  | => module            | Import module                   |
| 61   | EXPORT             | val_idx  | val =>               | Export value                    |
| 62   | DEBUG_BREAK        | -        | -                    | Debugger breakpoint             |
| 63   | PROFILE_START      | -        | -                    | Start profiling                 |
| 64   | PROFILE_END        | -        | -                    | Stop profiling                  |
| 65   | SANDBOX_ENTER      | -        | -                    | Enter sandbox mode              |
| 66   | SANDBOX_EXIT       | -        | -                    | Exit sandbox mode               |

## Value Encoding

Values are 16-byte tagged unions:
- Type tag (8 bytes, enum ValueType)
- Value payload (8 bytes): integer, double, or pointer

## Call Frame Layout

Each call frame on the call stack:
- closure: ObjClosure pointer
- ip: instruction pointer (bytecode offset)
- slots: base pointer into operand stack
- depth: frame nesting depth
