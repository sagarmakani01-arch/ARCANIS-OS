# Tutorial 1: Hello, World!

Welcome to ArcanisLang! Let's start with the classic first program.

## What You'll Learn
- How to run ArcanisLang code
- The `print` function
- Strings

## Step 1: Your First Program

Create a file called `hello.arc`:

```arcanis
print("Hello, World!")
```

Run it:

```bash
python -m src.cli hello.arc
```

You should see: `Hello, World!`

## Step 2: Print Multiple Things

```arcanis
print("Hello,")
print("World!")
```

Each `print` call adds a new line.

## Step 3: Using the REPL

Try typing directly:

```bash
python -m src.cli
>>> print("Hello from the REPL!")
Hello from the REPL!
>>> exit
```

## What's Next?

In the next tutorial, you'll learn about variables.
