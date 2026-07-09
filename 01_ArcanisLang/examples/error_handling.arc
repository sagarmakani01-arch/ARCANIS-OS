# Error handling in ArcanisLang

fun safe_divide(a, b):
    try:
        result = a / b
        return result
    catch error:
        return "Error: " + error

print(safe_divide(10, 2))
print(safe_divide(10, 0))

# Raise errors
fun validate_age(age):
    if age < 0:
        raise "Age cannot be negative"
    if age > 150:
        raise "Age seems too high"
    return "Age " + str(age) + " is valid"

print(validate_age(25))
print(validate_age(-5))
print(validate_age(200))
