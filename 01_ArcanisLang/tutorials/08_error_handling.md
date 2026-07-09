# Tutorial 8: Error Handling

Handle errors gracefully with try/catch.

## Basic Try/Catch

```arcanis
try:
    result = 10 / 0
    print(result)
catch error:
    print("Oops: " + error)
```

## Raising Errors

```arcanis
fun divide(a, b):
    if b == 0:
        raise "Cannot divide by zero"
    return a / b

try:
    print(divide(10, 0))
catch error:
    print("Error: " + error)
```

## Practical Example

```arcanis
fun parse_number(text):
    if text == "":
        raise "Empty string"
    result = int(text)
    return result

fun safe_parse(text):
    try:
        value = parse_number(text)
        return "Parsed: " + str(value)
    catch error:
        return "Failed: " + error

print(safe_parse("42"))
print(safe_parse(""))
print(safe_parse("hello"))
```

## Key Points
- `try` contains code that might fail
- `catch` handles the error
- `raise` creates an error
- Errors are strings by default
