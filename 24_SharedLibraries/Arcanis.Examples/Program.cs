using Arcanis.DataStructures.Collections;
using Arcanis.DataStructures.Trees;
using Arcanis.DataStructures.Graphs;
using Arcanis.AI.Pathfinding;
using Arcanis.AI.StateMachine;
using Arcanis.FileSystem;
using Arcanis.Mathematics;
using Arcanis.Logging;
using Arcanis.Logging.Sinks;

namespace Arcanis.Examples;

class Program
{
    static async Task Main(string[] args)
    {
        Console.WriteLine("========================================");
        Console.WriteLine("  Arcanis Shared Libraries - Examples");
        Console.WriteLine("========================================\n");

        await RunDataStructuresExamples();
        await RunMathExamples();
        await RunAIExamples();
        await RunFileSystemExamples();
        await RunLoggingExamples();

        Console.WriteLine("\n========================================");
        Console.WriteLine("  All examples completed!");
        Console.WriteLine("========================================");
    }

    static async Task RunDataStructuresExamples()
    {
        Console.WriteLine("--- Data Structures Examples ---\n");

        // Object Pool
        Console.WriteLine("1. Object Pool:");
        var pool = new ObjectPool<List<int>>(
            factory: () => new List<int>(),
            reset: list => list.Clear(),
            initialSize: 5);

        var list1 = pool.Rent();
        list1.Add(1);
        list1.Add(2);
        Console.WriteLine($"   Rented list with {list1.Count} items");

        pool.Return(list1);
        Console.WriteLine($"   Pool available: {pool.AvailableCount} objects");

        // Fixed Size Queue
        Console.WriteLine("\n2. Fixed Size Queue:");
        var queue = new FixedSizeQueue<int>(capacity: 5);
        for (int i = 0; i < 8; i++)
        {
            bool overwritten = queue.Enqueue(i);
            Console.WriteLine($"   Enqueued {i}, overwritten: {overwritten}, count: {queue.Count}");
        }

        // Binary Search Tree
        Console.WriteLine("\n3. Binary Search Tree:");
        var bst = new BinarySearchTree<int>();
        foreach (var num in new[] { 5, 3, 7, 1, 4, 6, 8 })
        {
            bst.Insert(num);
        }
        Console.WriteLine($"   Tree count: {bst.Count}");
        Console.WriteLine($"   In-order: {string.Join(", ", bst.InOrderTraversal())}");
        Console.WriteLine($"   Min: {bst.GetMin()}, Max: {bst.GetMax()}");

        // Graph
        Console.WriteLine("\n4. Graph:");
        var graph = new Graph<string>(GraphType.Undirected);
        graph.AddEdge("A", "B");
        graph.AddEdge("A", "C");
        graph.AddEdge("B", "D");
        graph.AddEdge("C", "D");
        graph.AddEdge("D", "E");
        Console.WriteLine($"   Vertices: {graph.VertexCount}, Edges: {graph.EdgeCount}");
        Console.WriteLine($"   BFS from A: {string.Join(" -> ", graph.BFS("A"))}");
        Console.WriteLine($"   DFS from A: {string.Join(" -> ", graph.DFS("A"))}");

        Console.WriteLine();
    }

    static async Task RunMathExamples()
    {
        Console.WriteLine("--- Mathematics Examples ---\n");

        // Vector2D
        Console.WriteLine("1. Vector2D:");
        var v1 = new Arcanis.Mathematics.Vector2(3, 4);
        var v2 = new Arcanis.Mathematics.Vector2(1, 2);
        Console.WriteLine($"   v1: {v1}, Magnitude: {v1.Magnitude:F2}");
        Console.WriteLine($"   v2: {v2}");
        Console.WriteLine($"   v1 + v2: {v1 + v2}");
        Console.WriteLine($"   Dot: {Arcanis.Mathematics.Vector2.Dot(v1, v2)}");
        Console.WriteLine($"   Distance: {Arcanis.Mathematics.Vector2.Distance(v1, v2):F2}");

        // Vector3D
        Console.WriteLine("\n2. Vector3D:");
        var v3 = new Arcanis.Mathematics.Vector3D(1, 2, 3);
        var v4 = new Arcanis.Mathematics.Vector3D(4, 5, 6);
        Console.WriteLine($"   v3: {v3}");
        Console.WriteLine($"   v4: {v4}");
        Console.WriteLine($"   Cross: {Arcanis.Mathematics.Vector3D.Cross(v3, v4)}");

        // Matrix
        Console.WriteLine("\n3. Matrix4x4:");
        var translation = Matrix4x4.CreateTranslation(5, 3, 2);
        Console.WriteLine($"   Translation matrix created");
        Console.WriteLine($"   Determinant: {translation.Determinant}");

        // Statistics
        Console.WriteLine("\n4. Statistics:");
        var data = new[] { 2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0 };
        Console.WriteLine($"   Data: {string.Join(", ", data)}");
        Console.WriteLine($"   Mean: {Statistics.Mean(data):F2}");
        Console.WriteLine($"   Median: {Statistics.Median(data):F2}");
        Console.WriteLine($"   Variance: {Statistics.Variance(data):F2}");
        Console.WriteLine($"   Std Dev: {Statistics.StandardDeviation(data):F2}");
        Console.WriteLine($"   Q1: {Statistics.Percentile(data, 25):F2}, Q3: {Statistics.Percentile(data, 75):F2}");

        Console.WriteLine();
    }

    static async Task RunAIExamples()
    {
        Console.WriteLine("--- AI Examples ---\n");

        // A* Pathfinding
        Console.WriteLine("1. A* Pathfinding:");
        var grid = new GridCell[10, 10];
        for (int x = 0; x < 10; x++)
            for (int y = 0; y < 10; y++)
                grid[x, y] = new GridCell(x, y, true);

        // Add some obstacles
        grid[3, 3].IsWalkable = false;
        grid[3, 4].IsWalkable = false;
        grid[3, 5].IsWalkable = false;

        var pathfinder = new AStarPathfinder(grid);
        var path = pathfinder.FindPath(0, 0, 9, 9);
        Console.WriteLine($"   Path found: {path.Count} steps");
        Console.WriteLine($"   Path: {string.Join(" -> ", path.Take(5).Select(p => $"({p.x},{p.y})"))}...");

        // State Machine
        Console.WriteLine("\n2. State Machine:");
        var sm = new StateMachine<object>();

        var idleState = new IdleState();
        var walkState = new WalkState();
        var attackState = new AttackState();

        sm.AddState(idleState);
        sm.AddState(walkState);
        sm.AddState(attackState);

        sm.AddTransition("Idle", "Walk", ctx => true);
        sm.AddTransition("Walk", "Attack", ctx => true);
        sm.AddTransition("Attack", "Idle", ctx => true);

        await sm.SetInitialStateAsync("Idle", new object());
        Console.WriteLine($"   Current state: {sm.CurrentState?.Name}");

        for (int i = 0; i < 3; i++)
        {
            await sm.UpdateAsync(new object());
            Console.WriteLine($"   After update: {sm.CurrentState?.Name}");
        }

        Console.WriteLine();
    }

    static async Task RunFileSystemExamples()
    {
        Console.WriteLine("--- File System Examples ---\n");

        // Virtual File System
        Console.WriteLine("1. Virtual File System:");
        var vfs = new VirtualFileSystem();

        vfs.CreateDirectory("assets");
        vfs.CreateDirectory("assets/textures");
        vfs.CreateFile("assets/config.json", "{\"version\": \"1.0\"}");
        vfs.CreateFile("assets/textures/player.png", new byte[] { 0x89, 0x50, 0x4E, 0x47 });

        Console.WriteLine($"   Files: {vfs.Files.Count()}");
        Console.WriteLine($"   Directories: {vfs.Directories.Count()}");
        Console.WriteLine($"   Config exists: {vfs.Exists("assets/config.json")}");
        Console.WriteLine($"   Config content: {vfs.ReadFileAsText("assets/config.json")}");

        // Asset Manager
        Console.WriteLine("\n2. Asset Manager:");
        var assetManager = new AssetManager(vfs);

        var configAsset = assetManager.LoadAsset("config", "assets/config.json", AssetType.Json);
        var textureAsset = assetManager.LoadAsset("player", "assets/textures/player.png", AssetType.Image);

        Console.WriteLine($"   Loaded assets: {assetManager.LoadedAssetCount}");
        Console.WriteLine($"   Total memory: {assetManager.TotalMemoryUsed} bytes");

        var stats = assetManager.GetMemoryStats();
        Console.WriteLine($"   Assets by type: {string.Join(", ", stats.AssetsByType.Select(kvp => $"{kvp.Key}: {kvp.Value}"))}");

        assetManager.Dispose();

        Console.WriteLine();
    }

    static async Task RunLoggingExamples()
    {
        Console.WriteLine("--- Logging Examples ---\n");

        // Logger with multiple sinks
        Console.WriteLine("1. Logger with Console Sink:");
        using var logger = new Logger("App");
        logger.AddSink(new ConsoleSink(LogLevel.Debug));

        logger.Debug("Application starting");
        logger.Information("Server started on port 8080");
        logger.Warning("High memory usage detected");

        try
        {
            throw new InvalidOperationException("Test exception");
        }
        catch (Exception ex)
        {
            logger.Error("An error occurred", ex);
        }

        logger.Critical("System failure!");

        // Memory Sink
        Console.WriteLine("\n2. Memory Sink:");
        using var memoryLogger = new Logger("Test");
        var memorySink = new MemorySink();
        memoryLogger.AddSink(memorySink);

        for (int i = 0; i < 5; i++)
        {
            memoryLogger.Information($"Test message {i}");
        }

        Console.WriteLine($"   Stored entries: {memorySink.EntryCount}");
        var entries = memorySink.GetEntriesByLevel(LogLevel.Information);
        Console.WriteLine($"   Info entries: {entries.Count}");

        Console.WriteLine();
    }
}

// Helper states for State Machine example
class IdleState : IState<object>
{
    public string Name => "Idle";
    public StateStatus Status { get; set; } = StateStatus.Inactive;

    public Task EnterAsync(object context)
    {
        Console.WriteLine("   -> Entered Idle state");
        return Task.CompletedTask;
    }

    public Task UpdateAsync(object context) => Task.CompletedTask;

    public Task ExitAsync(object context)
    {
        Console.WriteLine("   -> Exiting Idle state");
        return Task.CompletedTask;
    }
}

class WalkState : IState<object>
{
    public string Name => "Walk";
    public StateStatus Status { get; set; } = StateStatus.Inactive;

    public Task EnterAsync(object context)
    {
        Console.WriteLine("   -> Entered Walk state");
        return Task.CompletedTask;
    }

    public Task UpdateAsync(object context) => Task.CompletedTask;

    public Task ExitAsync(object context)
    {
        Console.WriteLine("   -> Exiting Walk state");
        return Task.CompletedTask;
    }
}

class AttackState : IState<object>
{
    public string Name => "Attack";
    public StateStatus Status { get; set; } = StateStatus.Inactive;

    public Task EnterAsync(object context)
    {
        Console.WriteLine("   -> Entered Attack state");
        return Task.CompletedTask;
    }

    public Task UpdateAsync(object context) => Task.CompletedTask;

    public Task ExitAsync(object context)
    {
        Console.WriteLine("   -> Exiting Attack state");
        return Task.CompletedTask;
    }
}
