# Tutorial 7: Modules

Modules help organize code into separate files.

## Creating a Module

Create a file `math_helpers.arc`:

```arcanis
fun square(x):
    return x * x

fun cube(x):
    return x * x * x

pi = 3.14159
```

## Importing a Module

In another file:

```arcanis
import math_helpers
print(math_helpers.square(5))
print(math_helpers.pi)
```

## From-Import

```arcanis
from math_helpers import square, pi
print(square(5))
print(pi)
```

## Key Points
- Module names match filenames (without .arc)
- Use `import` for full module access
- Use `from ... import` for specific names
