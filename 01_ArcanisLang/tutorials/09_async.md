# Tutorial 9: Async Programming

Async functions let you write non-blocking code.

## Defining an Async Function

```arcanis
async fun fetch_data(url):
    return "Data from " + url
```

## Using Await

```arcanis
async fun process():
    data = await fetch_data("https://api.example.com")
    print(data)
```

## Important Notes

Async support in ArcanisLang v0.1.0 is experimental. For most programs, regular functions are recommended.

## Sync Alternative

For simple programs, use regular functions:

```arcanis
fun fetch(url):
    sleep(1)
    return "Response from " + url

print(fetch("https://arcanis.dev"))
```

## Coming Soon
- Full async runtime
- Event loop
- Concurrent task execution
