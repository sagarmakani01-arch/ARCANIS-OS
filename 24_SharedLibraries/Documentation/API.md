# Arcanis Shared Libraries - API Reference

## Arcanis.DataStructures

### ObjectPool<T>
A thread-safe object pool that reduces garbage collection pressure.

```csharp
var pool = new ObjectPool<List<int>>(
    factory: () => new List<int>(),
    reset: list => list.Clear(),
    initialSize: 16,
    maxSize: 1024);

var item = pool.Rent();
pool.Return(item);
```

### FixedSizeQueue<T>
A circular queue that overwrites old elements when full.

```csharp
var queue = new FixedSizeQueue<int>(capacity: 100);
queue.Enqueue(42);
int value = queue.Dequeue();
```

### BinarySearchTree<T>
A generic BST with O(log n) average operations.

```csharp
var tree = new BinarySearchTree<int>();
tree.Insert(5);
tree.Insert(3);
tree.Insert(7);
bool found = tree.Search(5);
IEnumerable<int> sorted = tree.InOrderTraversal();
```

### Graph<T>
Adjacency list graph supporting directed and undirected graphs.

```csharp
var graph = new Graph<string>(GraphType.Undirected);
graph.AddEdge("A", "B");
graph.AddEdge("B", "C");
IEnumerable<string> bfs = graph.BFS("A");
IEnumerable<string> dfs = graph.DFS("A");
```

---

## Arcanis.Networking

### TcpServer
High-performance async TCP server.

```csharp
var server = new TcpServer(port: 8080);
server.ClientConnected += (s, e) => Console.WriteLine($"Client: {e.ClientId}");
server.DataReceived += (s, e) => Console.WriteLine(e.Message);
await server.StartAsync();
await server.BroadcastMessageAsync("Hello all clients!");
await server.StopAsync();
```

### ArcanisTcpClient
Async TCP client with auto-reconnection.

```csharp
var client = new ArcanisTcpClient("localhost", 8080);
client.DataReceived += (s, e) => Console.WriteLine(e.Message);
await client.ConnectAsync();
await client.SendMessageAsync("Hello server!");
```

### UdpServer
Connectionless UDP server for real-time games.

```csharp
var udpServer = new UdpServer(port: 9000);
udpServer.DataReceived += (s, e) => Console.WriteLine(e.Message);
await udpServer.StartAsync();
```

### ArcanisHttpClient
HTTP client with JSON serialization.

```csharp
using var httpClient = new ArcanisHttpClient("https://api.example.com");
var user = await httpClient.GetAsync<User>("/users/1");
var result = await httpClient.PostAsync("/users", newUser);
```

### BinarySerializer
Fast binary serialization utilities.

```csharp
byte[] bytes = BinarySerializer.Serialize(42);
int value = BinarySerializer.Deserialize<int>(bytes);
byte[] strBytes = BinarySerializer.SerializeString("Hello");
```

---

## Arcanis.Security

### AesEncryption
AES-256 encryption/decryption.

```csharp
byte[] key = AesEncryption.GenerateKey(256);
byte[] iv = AesEncryption.GenerateIV();
byte[] encrypted = AesEncryption.EncryptAesCbc(plainText, key, iv);
byte[] decrypted = AesEncryption.DecryptAesCbc(encrypted, key, iv);

// String encryption
string enc = AesEncryption.EncryptStringAesCbc("secret", key, iv);
string dec = AesEncryption.DecryptStringAesCbc(enc, key, iv);
```

### Hashing
Cryptographic and non-cryptographic hashing.

```csharp
string hash = Hashing.ComputeSha256Hex("password");
byte[] hmac = Hashing.ComputeHmacSha256(data, key);
uint murmur = Hashing.MurmurHash3(data);

// Password hashing
var (hash, salt) = Hashing.ComputePasswordHash("password");
bool valid = Hashing.VerifyPassword("password", hash, salt);
```

### JwtTokenManager
JWT token generation and validation.

```csharp
var jwtManager = new JwtTokenManager(new JwtOptions
{
    SecretKey = "your-secret-key-at-least-32-chars",
    Expiration = TimeSpan.FromHours(1)
});

string token = jwtManager.GenerateAccessToken(userId, username, roles);
ClaimsPrincipal? principal = jwtManager.ValidateToken(token);
```

---

## Arcanis.AI

### AStarPathfinder
A* pathfinding for 2D grids.

```csharp
var grid = new GridCell[20, 20];
// Initialize grid...
var pathfinder = new AStarPathfinder(grid);
pathfinder.AllowDiagonalMovement = true;
var path = pathfinder.FindPath(0, 0, 19, 19);
```

### StateMachine<T>
Finite state machine with async support.

```csharp
var sm = new StateMachine<GameContext>();
sm.AddState(new IdleState());
sm.AddState(new WalkState());
sm.AddTransition("Idle", "Walk", ctx => ctx.ShouldWalk);
await sm.SetInitialStateAsync("Idle", context);
await sm.UpdateAsync(context);
```

---

## Arcanis.FileSystem

### VirtualFileSystem
In-memory file system with events.

```csharp
var vfs = new VirtualFileSystem();
vfs.CreateDirectory("assets");
vfs.CreateFile("assets/config.json", jsonContent);
byte[] data = vfs.ReadFile("assets/config.json");
string text = vfs.ReadFileAsText("assets/config.json");
vfs.FileCreated += (s, e) => Console.WriteLine($"Created: {e.Path}");
```

### AssetManager
Asset loading with caching and reference counting.

```csharp
var assetManager = new AssetManager(vfs);
var texture = assetManager.LoadAsset("player", "player.png", AssetType.Image);
var config = await assetManager.LoadAssetAsync("config", "config.json");
var stats = assetManager.GetMemoryStats();
assetManager.UnloadAsset("player");
```

---

## Arcanis.Mathematics

### Vector2
2D vector operations with SIMD support.

```csharp
var v1 = new Vector2(3, 4);
var v2 = new Vector2(1, 2);
float dot = Vector2.Dot(v1, v2);
float dist = Vector2.Distance(v1, v2);
Vector2 rotated = Vector2.Rotate(v1, MathF.PI / 4);
```

### Vector3D
3D vector operations.

```csharp
var v1 = new Vector3D(1, 2, 3);
var v2 = new Vector3D(4, 5, 6);
Vector3D cross = Vector3D.Cross(v1, v2);
Vector3D reflected = Vector3D.Reflect(v1, Vector3D.Up);
```

### Matrix4x4
4x4 transformation matrices.

```csharp
var translation = Matrix4x4.CreateTranslation(5, 3, 2);
var rotation = Matrix4x4.CreateRotationY(MathF.PI / 2);
var scale = Matrix4x4.CreateScale(2, 2, 2);
var view = Matrix4x4.CreateLookAt(eye, target, up);
var projection = Matrix4x4.CreatePerspectiveFieldOfView(fov, aspect, near, far);
```

### Statistics
Statistical analysis functions.

```csharp
double mean = Statistics.Mean(data);
double median = Statistics.Median(data);
double stdDev = Statistics.StandardDeviation(data);
double corr = Statistics.Correlation(x, y);
var outliers = Statistics.DetectOutliers(data);
```

---

## Arcanis.Logging

### Logger
Main logger with multiple sinks.

```csharp
using var logger = new Logger("MyApp");
logger.AddSink(new ConsoleSink(LogLevel.Debug));
logger.AddSink(new FileSink("logs"));

logger.Information("Server started");
logger.Error("Connection failed", exception);
```

### ConsoleSink
Color-coded console output.

```csharp
var sink = new ConsoleSink(
    minimumLevel: LogLevel.Information,
    useColors: true,
    useTimestamps: true);
```

### FileSink
File logging with automatic rotation.

```csharp
var sink = new FileSink(
    directory: "logs",
    filePrefix: "app",
    maxFileSize: 10 * 1024 * 1024); // 10MB
```

### MemorySink
In-memory logging for testing.

```csharp
var sink = new MemorySink(maxEntries: 1000);
logger.AddSink(sink);
// Later...
var entries = sink.GetEntriesByLevel(LogLevel.Error);
```
