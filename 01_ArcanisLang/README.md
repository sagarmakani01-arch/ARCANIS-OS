# ArcanisLang

A beginner-friendly, AI-native programming language that is easier to learn than Python while remaining powerful.

## Quick Start

```bash
# Install
pip install -e .

# Run a file
python -m src.cli examples/hello_world.arc

# Start the REPL
python -m src.cli
```

## Features

- **Human-readable syntax** - Clean, indentation-based blocks
- **Minimal complexity** - Fewer concepts to learn
- **Dynamic typing** - No type declarations needed
- **Clear error messages** - Designed for beginners
- **Cross-platform** - Pure Python, runs anywhere

## Examples

```arcanis
# Hello World
print("Hello, World!")

# Variables
name = "Arcanis"
version = 1.0

# Functions
fun greet(name):
    return "Hello, " + name + "!"

# Loops
for i in range(5):
    print(i)

# Classes
class Person:
    fun init(self, name):
        self.name = name

    fun greet(self):
        return "Hi, I'm " + self.name
```

## Documentation

- [Getting Started](docs/getting_started.md)
- [Syntax Reference](docs/syntax.md)
- [Examples](docs/examples.md)

## Tutorials

Start with `tutorials/01_hello_world.md` and work through them in order.

## Testing

```bash
python -m tests.run_tests
```

## License

MIT
