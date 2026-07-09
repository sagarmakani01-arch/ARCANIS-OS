# Function definitions and calls

fun greet(name):
    return "Hello, " + name + "!"

fun add(a, b):
    return a + b

fun factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

fun is_even(n):
    return n % 2 == 0

# Calling functions
print(greet("Arcanis"))
print("5 + 3 = " + str(add(5, 3)))
print("factorial(5) = " + str(factorial(5)))
print("Is 10 even? " + str(is_even(10)))
