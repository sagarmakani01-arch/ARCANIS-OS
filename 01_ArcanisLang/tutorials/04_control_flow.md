# Tutorial 4: Control Flow

Make decisions and repeat actions.

## If Statements

```arcanis
age = 18

if age >= 18:
    print("You are an adult")
```

## If-Elif-Else

```arcanis
score = 85

if score >= 90:
    print("A")
elif score >= 80:
    print("B")
elif score >= 70:
    print("C")
else:
    print("F")
```

## While Loops

```arcanis
count = 3
while count > 0:
    print(count)
    count = count - 1
print("Go!")
```

## For Loops

```arcanis
for i in range(5):
    print(i)
```

## Break and Continue

```arcanis
for i in range(10):
    if i == 3:
        continue  # skip 3
    if i == 7:
        break     # stop at 7
    print(i)
```

## Practice: FizzBuzz

```arcanis
for i in range(1, 16):
    if i % 15 == 0:
        print("FizzBuzz")
    elif i % 3 == 0:
        print("Fizz")
    elif i % 5 == 0:
        print("Buzz")
    else:
        print(i)
```
