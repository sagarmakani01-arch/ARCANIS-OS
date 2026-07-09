# Getting Started with ArcanisLang

## Installation

ArcanisLang requires Python 3.8 or later. No external dependencies needed.

```bash
# Clone or download ArcanisLang
# Then install in development mode
pip install -e .
```

## Your First Program

Create a file called `hello.arc`:

```arcanis
print("Hello, World!")
print("Welcome to ArcanisLang!")
```

Run it:

```bash
python -m src.cli hello.arc
```

## The REPL

Start the interactive shell:

```bash
python -m src.cli
```

Try typing:

```
>>> name = "Arcanis"
>>> print("Hello, " + name)
Hello, Arcanis
>>> exit
```

## Next Steps

1. Work through the tutorials in order
2. Check the examples directory
3. Read the syntax reference
