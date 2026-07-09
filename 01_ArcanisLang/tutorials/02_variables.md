# Tutorial 2: Variables

Variables store data that you can use and change later.

## Basic Variables

```arcanis
name = "Alice"
age = 25
height = 1.68
is_student = true
```

## Printing Variables

```arcanis
name = "ArcanisLang"
print("Hello, " + name)
```

## Changing Variables

```arcanis
count = 10
print(count)  # 10
count = count + 1
print(count)  # 11
count += 5
print(count)  # 16
```

## Variable Names

- Can contain letters, numbers, and underscores
- Must start with a letter or underscore
- Names are case-sensitive

## Try It

```arcanis
language = "ArcanisLang"
version = 0.1
year = 2026

print(language + " v" + str(version))
print("Created in " + str(year))
```

## Key Points
- No type declaration needed
- Use `=` for assignment
- Use `str()` to convert numbers to strings
