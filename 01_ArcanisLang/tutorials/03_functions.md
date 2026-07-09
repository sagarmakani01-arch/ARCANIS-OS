# Tutorial 3: Functions

Functions are reusable blocks of code.

## Defining a Function

Use the `fun` keyword:

```arcanis
fun greet():
    print("Hello!")
```

## Calling a Function

```arcanis
greet()  # Hello!
```

## Parameters

```arcanis
fun greet(name):
    print("Hello, " + name + "!")

greet("Alice")  # Hello, Alice!
```

## Return Values

```arcanis
fun add(a, b):
    return a + b

result = add(5, 3)
print(result)  # 8
```

## Multiple Parameters

```arcanis
fun describe(name, age, city):
    return name + " is " + str(age) + " from " + city

print(describe("Alice", 30, "New York"))
```

## Practice

Write a function that converts Celsius to Fahrenheit:

```arcanis
fun celsius_to_fahrenheit(c):
    return (c * 9 / 5) + 32

print(celsius_to_fahrenheit(0))   # 32
print(celsius_to_fahrenheit(100)) # 212
```

## Key Points
- Functions are defined with `fun`
- Use `return` to give back a value
- Parameters go inside parentheses
