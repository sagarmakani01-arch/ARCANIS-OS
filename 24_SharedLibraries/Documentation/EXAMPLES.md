# Arcanis Shared Libraries - Usage Examples

## Table of Contents

1. [Data Structures](#data-structures)
2. [Networking](#networking)
3. [Security](#security)
4. [AI](#ai)
5. [File System](#file-system)
6. [Mathematics](#mathematics)
7. [Logging](#logging)

---

## Data Structures

### Object Pool for Game Objects

```csharp
// Pool for bullet objects to avoid GC spikes
var bulletPool = new ObjectPool<Bullet>(
    factory: () => new Bullet(),
    reset: bullet => { bullet.Position = Vector2.Zero; bullet.Velocity = Vector2.Zero; },
    initialSize: 100,
    maxSize: 1000);

// Spawn a bullet
var bullet = bulletPool.Rent();
bullet.Position = playerPosition;
bullet.Velocity = direction * speed;

// When bullet goes off-screen, return to pool
bulletPool.Return(bullet);
```

### Fixed Queue for Input Buffer

```csharp
// Buffer last 16 inputs for rollback netcode
var inputBuffer = new FixedSizeQueue<InputState>(16);

// Each frame, enqueue current input
inputBuffer.Enqueue(currentInput);

// To rollback, get older input
var rollbackInput = inputBuffer.ToArray()[framesToRollback];
```

### Graph for Navigation Mesh

```csharp
var navMesh = new Graph<Vector3>(GraphType.Undirected);

// Add navigation points
navMesh.AddVertex(new Vector3(0, 0, 0));
navMesh.AddVertex(new Vector3(10, 0, 0));
navMesh.AddVertex(new Vector3(5, 0, 10));

// Connect navigation points
navMesh.AddEdge(new Vector3(0, 0, 0), new Vector3(10, 0, 0));
navMesh.AddEdge(new Vector3(10, 0, 0), new Vector3(5, 0, 10));

// Find path
var path = navMesh.BFS(startPosition);
```

---

## Networking

### Game Server with TCP

```csharp
var server = new TcpServer(port: 7777);

server.ClientConnected += async (sender, e) =>
{
    Console.WriteLine($"Player joined: {e.ClientId}");
    await server.SendMessageAsync(e.ClientId, "Welcome!");
};

server.DataReceived += async (sender, e) =>
{
    var packet = JsonSerializer.Deserialize<GamePacket>(e.Message);
    await HandlePacket(e.ClientId, packet);
};

await server.StartAsync();
```

### HTTP API Client

```csharp
using var api = new ArcanisHttpClient("https://api.mygame.com");

// Get player data
var player = await api.GetAsync<Player>("/players/12345");

// Update player
var update = new { Score = player.Score + 100 };
await api.PostAsync($"/players/12345/score", update);

// Delete session
await api.DeleteAsync($"/sessions/{sessionId}");
```

---

## Security

### Encrypt Save Data

```csharp
// Generate key (store securely!)
byte[] key = AesEncryption.GenerateKey(256);

// Encrypt save data
string saveJson = JsonSerializer.Serialize(gameState);
byte[] encrypted = AesEncryption.EncryptAesCbcAutoIV(
    Encoding.UTF8.GetBytes(saveJson), key);

// Save to file
await File.WriteAllBytesAsync("save.dat", encrypted);
```

### User Authentication

```csharp
// Hash password during registration
var (hash, salt) = Hashing.ComputePasswordHash(userPassword);
await SaveUserCredentials(userId, hash, salt);

// Verify during login
var storedHash = await GetStoredHash(userId);
var storedSalt = await GetStoredSalt(userId);
bool isValid = Hashing.VerifyPassword(inputPassword, storedHash, storedSalt);
```

### JWT Tokens

```csharp
var jwtManager = new JwtTokenManager(new JwtOptions
{
    SecretKey = Environment.GetEnvironmentVariable("JWT_SECRET"),
    Issuer = "MyGame",
    Audience = "MyGamePlayers",
    Expiration = TimeSpan.FromHours(1)
});

// Login
string token = jwtManager.GenerateAccessToken(
    userId: user.Id,
    username: user.Username,
    roles: new[] { "player", "premium" });

// Validate API request
var principal = jwtManager.ValidateToken(requestToken);
if (principal == null)
    return Unauthorized();
```

---

## AI

### A* Pathfinding

```csharp
// Create game map
var grid = new GridCell[50, 50];
for (int x = 0; x < 50; x++)
    for (int y = 0; y < 50; y++)
        grid[x, y] = new GridCell(x, y, IsWalkable: !IsWall(x, y));

var pathfinder = new AStarPathfinder(grid);
pathfinder.AllowDiagonalMovement = true;

// Find path for AI
var path = pathfinder.FindPath(
    enemy.GridX, enemy.GridY,
    player.GridX, player.GridY);

// Move enemy along path
foreach (var step in path)
{
    await MoveToAsync(enemy, step.x, step.y);
}
```

### Enemy State Machine

```csharp
var enemyAI = new StateMachine<EnemyContext>();

enemyAI.AddState(new PatrolState());
enemyAI.AddState(new ChaseState());
enemyAI.AddState(new AttackState());
enemyAI.AddState(new FleeState());

enemyAI.AddTransition("Patrol", "Chase",
    ctx => ctx.DistanceToPlayer < 10f);

enemyAI.AddTransition("Chase", "Attack",
    ctx => ctx.DistanceToPlayer < 2f);

enemyAI.AddTransition("Chase", "Flee",
    ctx => ctx.HealthPercent < 0.2f);

enemyAI.AddTransition("Attack", "Chase",
    ctx => ctx.DistanceToPlayer > 3f);

await enemyAI.SetInitialStateAsync("Patrol", enemyContext);

// Game loop
while (game.IsRunning)
{
    await enemyAI.UpdateAsync(enemyContext);
    await Task.Delay(16); // ~60 FPS
}
```

---

## File System

### Virtual File System

```csharp
var vfs = new VirtualFileSystem();

// Build content structure
vfs.CreateDirectory("content");
vfs.CreateDirectory("content/textures");
vfs.CreateDirectory("content/audio");

// Load content
vfs.CreateFile("content/textures/hero.png", textureData);
vfs.CreateFile("content/audio/music.mp3", audioData);

// Watch for changes
vfs.FileCreated += (s, e) => Console.WriteLine($"New: {e.Path}");
vfs.FileModified += (s, e) => Console.WriteLine($"Updated: {e.Path}");

// Read content
byte[] texture = vfs.ReadFile("content/textures/hero.png");
string config = vfs.ReadFileAsText("content/settings.json");
```

### Asset Manager

```csharp
var assetManager = new AssetManager(vfs);

// Load assets with reference counting
var texture = assetManager.LoadAsset("hero_texture", "hero.png", AssetType.Image);
var config = await assetManager.LoadAssetAsync("game_config", "config.json");

// Get asset (increments reference count)
var sameTexture = assetManager.GetAsset("hero_texture");

// Unload when done
assetManager.UnloadAsset("hero_texture");

// Monitor memory
var stats = assetManager.GetMemoryStats();
Console.WriteLine($"Memory: {stats.TotalSizeBytes / 1024}KB");
Console.WriteLine($"Textures: {stats.AssetsByType[AssetType.Image]}");
```

---

## Mathematics

### 2D Physics

```csharp
// Calculate collision response
var normal = Vector2.Reflect(velocity, collisionNormal);
var newVelocity = normal * bounceFactor;

// Smooth movement
var targetPosition = new Vector2(targetX, targetY);
var currentPos = Vector2.Lerp(currentPos, targetPosition, Time.deltaTime * smoothFactor);

// Rotate towards target
float angle = MathF.Atan2(target.Y - current.Y, target.X - current.X);
var direction = new Vector2(MathF.Cos(angle), MathF.Sin(angle));
```

### 3D Camera

```csharp
// Create view matrix
var cameraPosition = new Vector3D(0, 5, -10);
var lookAtTarget = new Vector3D(0, 0, 0);
var upVector = Vector3D.Up;

var viewMatrix = Matrix4x4.CreateLookAt(cameraPosition, lookAtTarget, upVector);

// Create projection matrix
float fov = MathF.PI / 4; // 45 degrees
float aspect = screenWidth / screenHeight;
float near = 0.1f;
float far = 1000f;

var projectionMatrix = Matrix4x4.CreatePerspectiveFieldOfView(fov, aspect, near, far);
```

### Analytics

```csharp
// Analyze player performance
var scores = new List<double> { 100, 150, 120, 180, 200, 170, 190 };

double average = Statistics.Mean(scores);
double median = Statistics.Median(scores);
double stdDev = Statistics.StandardDeviation(scores);

// Detect outliers (cheaters?)
var outliers = Statistics.DetectOutliers(scores);
foreach (var outlier in outliers)
{
    Console.WriteLine($"Suspicious score: {outlier}");
}

// Normalize scores for comparison
var normalized = Statistics.Normalize(scores).ToList();
```

---

## Logging

### Production Logging

```csharp
using var logger = new Logger("GameServer");

// Console output with colors
logger.AddSink(new ConsoleSink(LogLevel.Information));

// File logging with rotation
logger.AddSink(new FileSink(
    directory: "logs",
    filePrefix: "server",
    maxFileSize: 50 * 1024 * 1024)); // 50MB

// Memory logging for recent entries
var memorySink = new MemorySink(maxEntries: 1000);
logger.AddSink(memorySink);

// Usage
logger.Information("Server started on port 7777");
logger.Warning($"Player {player.Id} disconnected unexpectedly");

try
{
    await ProcessGamePacket(packet);
}
catch (Exception ex)
{
    logger.Error($"Failed to process packet from {player.Id}", ex);
}

// Query logs
var errors = memorySink.GetEntriesByLevel(LogLevel.Error);
var recentLogs = memorySink.Search("player");
```

### Structured Logging

```csharp
logger.Log(LogLevel.Information, "Player joined game",
    properties: new Dictionary<string, object>
    {
        ["PlayerId"] = player.Id,
        ["Username"] = player.Username,
        ["IPAddress"] = player.IPAddress,
        ["Region"] = player.Region
    });
```
