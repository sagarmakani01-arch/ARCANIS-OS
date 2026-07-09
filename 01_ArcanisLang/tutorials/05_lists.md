# Tutorial 5: Lists

Lists store multiple values in order.

## Creating Lists

```arcanis
fruits = ["apple", "banana", "cherry"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", true]
```

## Accessing Elements

```arcanis
fruits = ["apple", "banana", "cherry"]
print(fruits[0])  # apple
print(fruits[1])  # banana
print(fruits[2])  # cherry
```

## List Length

```arcanis
print(len(fruits))  # 3
```

## Modifying Lists

```arcanis
fruits[1] = "blueberry"
print(fruits)  # [apple, blueberry, cherry]
```

## Useful Functions

```arcanis
numbers = [3, 1, 4, 1, 5]
print(sum(numbers))  # 14
print(max(numbers))  # 5
print(min(numbers))  # 1
```

## Practice

```arcanis
scores = [85, 92, 78, 95, 88]
total = sum(scores)
average = total / len(scores)
print("Average score: " + str(average))
```
