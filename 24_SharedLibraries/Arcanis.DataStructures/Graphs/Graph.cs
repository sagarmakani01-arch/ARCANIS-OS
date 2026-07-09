namespace Arcanis.DataStructures.Graphs;

/// <summary>
/// Represents the type of graph (directed or undirected).
/// </summary>
public enum GraphType
{
    /// <summary>Directed graph where edges have direction.</summary>
    Directed,
    /// <summary>Undirected graph where edges are bidirectional.</summary>
    Undirected
}

/// <summary>
/// A generic graph implementation supporting both directed and undirected graphs.
/// Uses adjacency list representation for efficient memory usage.
/// </summary>
/// <typeparam name="T">The type of vertex labels.</typeparam>
public class Graph<T> where T : notnull
{
    private readonly Dictionary<T, List<(T neighbor, double weight)>> _adjacencyList;
    private readonly GraphType _graphType;

    /// <summary>
    /// Gets the number of vertices in the graph.
    /// </summary>
    public int VertexCount => _adjacencyList.Count;

    /// <summary>
    /// Gets the total number of edges in the graph.
    /// </summary>
    public int EdgeCount
    {
        get
        {
            int count = _adjacencyList.Values.Sum(edges => edges.Count);
            return _graphType == GraphType.Undirected ? count / 2 : count;
        }
    }

    /// <summary>
    /// Gets all vertices in the graph.
    /// </summary>
    public IEnumerable<T> Vertices => _adjacencyList.Keys;

    /// <summary>
    /// Initializes a new instance of the Graph class.
    /// </summary>
    /// <param name="graphType">The type of graph (directed or undirected).</param>
    public Graph(GraphType graphType = GraphType.Undirected)
    {
        _adjacencyList = new Dictionary<T, List<(T, double)>>();
        _graphType = graphType;
    }

    /// <summary>
    /// Adds a vertex to the graph.
    /// </summary>
    /// <param name="vertex">The vertex to add.</param>
    public void AddVertex(T vertex)
    {
        if (!_adjacencyList.ContainsKey(vertex))
        {
            _adjacencyList[vertex] = new List<(T, double)>();
        }
    }

    /// <summary>
    /// Adds an edge between two vertices.
    /// </summary>
    /// <param name="from">The source vertex.</param>
    /// <param name="to">The destination vertex.</param>
    /// <param name="weight">The edge weight (default: 1.0).</param>
    public void AddEdge(T from, T to, double weight = 1.0)
    {
        AddVertex(from);
        AddVertex(to);

        _adjacencyList[from].Add((to, weight));

        if (_graphType == GraphType.Undirected)
        {
            _adjacencyList[to].Add((from, weight));
        }
    }

    /// <summary>
    /// Removes a vertex and all its edges from the graph.
    /// </summary>
    /// <param name="vertex">The vertex to remove.</param>
    /// <returns>True if the vertex was found and removed; otherwise, false.</returns>
    public bool RemoveVertex(T vertex)
    {
        if (!_adjacencyList.ContainsKey(vertex))
            return false;

        _adjacencyList.Remove(vertex);

        foreach (var edges in _adjacencyList.Values)
        {
            edges.RemoveAll(e => e.neighbor.Equals(vertex));
        }

        return true;
    }

    /// <summary>
    /// Gets the neighbors of a vertex.
    /// </summary>
    /// <param name="vertex">The vertex to get neighbors for.</param>
    /// <returns>An enumerable of neighboring vertices with their edge weights.</returns>
    public IEnumerable<(T neighbor, double weight)> GetNeighbors(T vertex)
    {
        if (_adjacencyList.TryGetValue(vertex, out var neighbors))
        {
            return neighbors;
        }
        return Enumerable.Empty<(T, double)>();
    }

    /// <summary>
    /// Gets the edge weight between two vertices.
    /// </summary>
    /// <param name="from">The source vertex.</param>
    /// <param name="to">The destination vertex.</param>
    /// <returns>The edge weight if the edge exists; otherwise, null.</returns>
    public double? GetEdgeWeight(T from, T to)
    {
        if (_adjacencyList.TryGetValue(from, out var neighbors))
        {
            var edge = neighbors.FirstOrDefault(e => e.neighbor.Equals(to));
            if (edge.neighbor != null)
                return edge.weight;
        }
        return null;
    }

    /// <summary>
    /// Checks if the graph contains a vertex.
    /// </summary>
    /// <param name="vertex">The vertex to check.</param>
    /// <returns>True if the vertex exists; otherwise, false.</returns>
    public bool ContainsVertex(T vertex) => _adjacencyList.ContainsKey(vertex);

    /// <summary>
    /// Checks if an edge exists between two vertices.
    /// </summary>
    /// <param name="from">The source vertex.</param>
    /// <param name="to">The destination vertex.</param>
    /// <returns>True if the edge exists; otherwise, false.</returns>
    public bool HasEdge(T from, T to)
    {
        if (_adjacencyList.TryGetValue(from, out var neighbors))
        {
            return neighbors.Any(e => e.neighbor.Equals(to));
        }
        return false;
    }

    /// <summary>
    /// Performs a breadth-first search starting from a vertex.
    /// </summary>
    /// <param name="startVertex">The starting vertex.</param>
    /// <returns>An enumerable of vertices in BFS order.</returns>
    public IEnumerable<T> BFS(T startVertex)
    {
        if (!ContainsVertex(startVertex))
            throw new ArgumentException("Vertex not found in graph.", nameof(startVertex));

        var visited = new HashSet<T>();
        var queue = new Queue<T>();
        var result = new List<T>();

        queue.Enqueue(startVertex);
        visited.Add(startVertex);

        while (queue.Count > 0)
        {
            var current = queue.Dequeue();
            result.Add(current);

            foreach (var (neighbor, _) in GetNeighbors(current))
            {
                if (!visited.Contains(neighbor))
                {
                    visited.Add(neighbor);
                    queue.Enqueue(neighbor);
                }
            }
        }

        return result;
    }

    /// <summary>
    /// Performs a depth-first search starting from a vertex.
    /// </summary>
    /// <param name="startVertex">The starting vertex.</param>
    /// <returns>An enumerable of vertices in DFS order.</returns>
    public IEnumerable<T> DFS(T startVertex)
    {
        if (!ContainsVertex(startVertex))
            throw new ArgumentException("Vertex not found in graph.", nameof(startVertex));

        var visited = new HashSet<T>();
        var result = new List<T>();

        DFSRecursive(startVertex, visited, result);

        return result;
    }

    private void DFSRecursive(T vertex, HashSet<T> visited, List<T> result)
    {
        visited.Add(vertex);
        result.Add(vertex);

        foreach (var (neighbor, _) in GetNeighbors(vertex))
        {
            if (!visited.Contains(neighbor))
            {
                DFSRecursive(neighbor, visited, result);
            }
        }
    }
}
