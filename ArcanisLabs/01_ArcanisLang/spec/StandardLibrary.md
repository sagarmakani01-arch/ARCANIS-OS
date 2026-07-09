# ArcanisLang Standard Library v0.1

---

## `std/io` — Input and Output

```arcanis
fn print(values: ...any)                   # Print values to stdout
fn println(values: ...any)                  # Print with newline
fn read_line() -> String                    # Read line from stdin
fn read_file(path: String) -> Result<String, Error>
fn write_file(path: String, content: String) -> Result<nil, Error>
fn append_file(path: String, content: String) -> Result<nil, Error>
fn exists(path: String) -> bool
```

## `std/ai` — AI Primitives

```arcanis
fn prompt(text: String) -> Prompt           # Create a prompt
fn embed(text: String) -> Embedding         # Create an embedding
fn model(name: String) -> Model              # Reference a model
fn cosine_similarity(a: Embedding, b: Embedding) -> f64
fn semantic_search(query: String, corpus: [String], top_k: i32) -> [(String, f64)]
fn token_count(text: String) -> i32
```

## `std/collections` — Data Structures

```arcanis
struct List<T>                              # Dynamic array
    fn push(item: T)
    fn pop() -> Option<T>
    fn get(index: i32) -> Option<T>
    fn len() -> i32
    fn sort(compare: fn(T, T) -> i32)
    fn map<U>(transform: fn(T) -> U) -> List<U>
    fn filter(predicate: fn(T) -> bool) -> List<T>

struct Map<K, V>                            # Hash map
    fn insert(key: K, value: V)
    fn get(key: K) -> Option<V>
    fn remove(key: K) -> Option<V>
    fn keys() -> List<K>
    fn len() -> i32

struct Set<T>                               # Hash set
    fn insert(value: T)
    fn contains(value: T) -> bool
    fn remove(value: T)
    fn union(other: Set<T>) -> Set<T>
    fn intersect(other: Set<T>) -> Set<T>

struct Queue<T>                             # FIFO queue
    fn enqueue(item: T)
    fn dequeue() -> Option<T>
    fn peek() -> Option<T>
    fn len() -> i32

struct Stack<T>                             # LIFO stack
    fn push(item: T)
    fn pop() -> Option<T>
    fn peek() -> Option<T>
    fn len() -> i32
```

## `std/http` — HTTP Client

```arcanis
struct Request
    fn url(path: String) -> Request
    fn method(m: String) -> Request
    fn header(key: String, value: String) -> Request
    fn body(data: String) -> Request
    fn json(data: any) -> Request

struct Response
    status: i32
    headers: Map<String, String>
    body: String

async fn get(url: String) -> Result<Response, Error>
async fn post(url: String, body: String) -> Result<Response, Error>
async fn send(request: Request) -> Result<Response, Error>
```

## `std/json` — JSON Processing

```arcanis
fn parse(text: String) -> Result<any, Error>
fn stringify(value: any) -> Result<String, Error>
fn pretty(value: any, indent: i32) -> Result<String, Error>
```

## `std/time` — Time Utilities

```arcanis
struct Duration
    millis: i64

struct DateTime
    year: i32, month: i32, day: i32
    hour: i32, minute: i32, second: i32

fn now() -> DateTime
fn sleep(duration: Duration)
fn duration(millis: i64) -> Duration
fn timer() -> Timer

struct Timer
    fn elapsed() -> Duration
    fn reset()
```

## `std/math` — Mathematics

```arcanis
const pi: f64 = 3.141592653589793
const e: f64 = 2.718281828459045

fn sin(x: f64) -> f64
fn cos(x: f64) -> f64
fn tan(x: f64) -> f64
fn sqrt(x: f64) -> f64
fn abs(x: f64) -> f64
fn floor(x: f64) -> f64
fn ceil(x: f64) -> f64
fn round(x: f64) -> f64
fn min(a: f64, b: f64) -> f64
fn max(a: f64, b: f64) -> f64
fn clamp(value: f64, min: f64, max: f64) -> f64
fn random() -> f64
fn random_range(min: f64, max: f64) -> f64
```

## `std/net` — Networking

```arcanis
struct TcpStream
struct TcpListener
struct UdpSocket

fn connect(host: String, port: i32) -> Result<TcpStream, Error>
fn bind(addr: String) -> Result<TcpListener, Error>
fn listen(addr: String) -> Result<UdpSocket, Error>
```

## `std/os` — Operating System

*(Designed for future ArcanisOS integration)*

```arcanis
fn get_env(key: String) -> Option<String>
fn set_env(key: String, value: String)
fn execute(command: String) -> Result<String, Error>
fn pid() -> i32
fn exit(code: i32)
```

## `std/testing` — Test Framework

```arcanis
fn test(name: String, block: fn())             # Define test
fn assert(condition: bool)                     # Assert true
fn assert_eq<T>(actual: T, expected: T)        # Assert equal
fn assert_ne<T>(actual: T, expected: T)        # Assert not equal
fn bench(name: String, iterations: i32, block: fn())
```
