# ArcanisLang Syntax Reference

## Comments

```arcanis
# This is a comment
```

## Variables

```arcanis
name = "value"
count = 42
pi = 3.14
is_valid = true
nothing = none
```

## Data Types

- Integers: `42`, `-5`, `0`
- Floats: `3.14`, `-0.5`
- Strings: `"hello"`, `'world'`
- Booleans: `true`, `false`
- None: `none`
- Lists: `[1, 2, 3]`
- Maps: `{"key": "value"}`

## Operators

### Arithmetic
`+`, `-`, `*`, `/`, `%`, `**`

### Comparison
`==`, `!=`, `<`, `>`, `<=`, `>=`

### Logical
`and`, `or`, `not`

### Assignment
`=`, `+=`, `-=`

## Control Flow

### If-Elif-Else
```arcanis
if condition:
    # body
elif other_condition:
    # body
else:
    # body
```

### While Loop
```arcanis
while condition:
    # body
```

### For Loop
```arcanis
for item in iterable:
    # body
```

## Functions

```arcanis
fun function_name(param1, param2):
    # body
    return value
```

## Classes

```arcanis
class ClassName:
    fun init(self, param):
        self.attr = param

    fun method(self):
        return self.attr
```

## Error Handling

```arcanis
try:
    # risky code
catch error:
    # handle error
```

## Modules

```arcanis
import module_name
from module import name
```

## Async

```arcanis
async fun fetch(url):
    result = await async_operation()
    return result
```
