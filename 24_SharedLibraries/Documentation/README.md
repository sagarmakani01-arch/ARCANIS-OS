# Arcanis Shared Libraries

A collection of high-performance, reusable C# libraries for all Arcanis projects.

## Libraries

### Arcanis.DataStructures
High-performance data structures optimized for game development and real-time applications.

- **ObjectPool<T>** - Reduce garbage collection pressure with object reuse
- **FixedSizeQueue<T>** - Circular queue with fixed capacity
- **BinarySearchTree<T>** - Self-balancing BST with O(log n) operations
- **Graph<T>** - Adjacency list graph with BFS/DFS traversal

### Arcanis.Networking
Asynchronous networking utilities for client-server communication.

- **TcpServer** - High-performance multi-client TCP server
- **TcpClient** - Async TCP client with auto-reconnection
- **UdpServer** - Connectionless UDP for real-time games
- **ArcanisHttpClient** - HTTP client with JSON serialization
- **BinarySerializer** - Fast binary serialization utilities

### Arcanis.Security
Cryptographic utilities for encryption, hashing, and authentication.

- **AesEncryption** - AES-256-CBC/GCM encryption/decryption
- **Hashing** - SHA-256, SHA-512, HMAC, MurmurHash3
- **JwtTokenManager** - JWT token generation and validation

### Arcanis.AI
AI utilities for game development and intelligent systems.

- **AStarPathfinder** - A* pathfinding for 2D grids
- **StateMachine<T>** - Finite state machine with async support

### Arcanis.FileSystem
File handling and virtual file system for asset management.

- **VirtualFileSystem** - In-memory file system with events
- **AssetManager** - Asset loading with caching and reference counting

### Arcanis.Mathematics
High-performance math utilities with SIMD support.

- **Vector2** - 2D vector operations
- **Vector3D** - 3D vector operations
- **Matrix4x4** - 4x4 transformation matrices
- **Statistics** - Statistical analysis functions

### Arcanis.Logging
Structured logging with multiple sinks and filtering.

- **Logger** - Main logger with sink/filter support
- **ConsoleSink** - Color-coded console output
- **FileSink** - File logging with rotation
- **MemorySink** - In-memory logging for testing

## Quick Start

```csharp
// Add reference to desired library
// Install-Package Arcanis.DataStructures

using Arcanis.DataStructures.Collections;
using Arcanis.Logging;
using Arcanis.Logging.Sinks;

// Create a logger
using var logger = new Logger("MyApp");
logger.AddSink(new ConsoleSink(LogLevel.Debug));
logger.Information("Hello Arcanis!");

// Use object pool
var pool = new ObjectPool<List<int>>(() => new List<int>(), l => l.Clear());
var list = pool.Rent();
// ... use list ...
pool.Return(list);
```

## Requirements

- .NET 8.0 or later
- C# 12.0 or later

## Building

```bash
dotnet build ArcanisSharedLibraries.sln
```

## Running Examples

```bash
dotnet run --project Arcanis.Examples
```

## Architecture

```
ArcanisSharedLibraries/
├── Arcanis.DataStructures/    # Collections, Trees, Graphs
├── Arcanis.Networking/        # TCP, UDP, HTTP, Serialization
├── Arcanis.Security/          # Encryption, Hashing, Auth
├── Arcanis.AI/                # Pathfinding, State Machines
├── Arcanis.FileSystem/        # VFS, Asset Management
├── Arcanis.Mathematics/       # Vectors, Matrices, Stats
├── Arcanis.Logging/           # Logging Framework
├── Arcanis.Examples/          # Example Applications
└── Documentation/             # Documentation
```

## License

Proprietary - Arcanis Lab
