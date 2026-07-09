namespace Arcanis.AI.Pathfinding;

/// <summary>
/// Represents a 2D grid cell for pathfinding.
/// </summary>
public struct GridCell
{
    /// <summary>The X coordinate.</summary>
    public int X { get; set; }
    /// <summary>The Y coordinate.</summary>
    public int Y { get; set; }
    /// <summary>Whether this cell is walkable.</summary>
    public bool IsWalkable { get; set; }
    /// <summary>The movement cost of this cell.</summary>
    public float Cost { get; set; }

    /// <summary>
    /// Initializes a new GridCell.
    /// </summary>
    public GridCell(int x, int y, bool isWalkable = true, float cost = 1.0f)
    {
        X = x;
        Y = y;
        IsWalkable = isWalkable;
        Cost = cost;
    }
}

/// <summary>
/// A* pathfinding algorithm implementation for 2D grids.
/// High-performance implementation with priority queue.
/// </summary>
public class AStarPathfinder
{
    private GridCell[,] _grid;
    private int _width;
    private int _height;

    /// <summary>
    /// Gets the width of the grid.
    /// </summary>
    public int Width => _width;

    /// <summary>
    /// Gets the height of the grid.
    /// </summary>
    public int Height => _height;

    /// <summary>
    /// Whether to allow diagonal movement.
    /// </summary>
    public bool AllowDiagonalMovement { get; set; } = true;

    /// <summary>
    /// Initializes a new AStarPathfinder with a grid.
    /// </summary>
    /// <param name="grid">The 2D grid of cells.</param>
    public AStarPathfinder(GridCell[,] grid)
    {
        _grid = grid;
        _width = grid.GetLength(0);
        _height = grid.GetLength(1);
    }

    /// <summary>
    /// Initializes a new AStarPathfinder with width and height.
    /// All cells are walkable by default.
    /// </summary>
    /// <param name="width">Grid width.</param>
    /// <param name="height">Grid height.</param>
    public AStarPathfinder(int width, int height)
    {
        _width = width;
        _height = height;
        _grid = new GridCell[width, height];

        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                _grid[x, y] = new GridCell(x, y);
            }
        }
    }

    /// <summary>
    /// Sets a cell's walkable state.
    /// </summary>
    /// <param name="x">The X coordinate.</param>
    /// <param name="y">The Y coordinate.</param>
    /// <param name="walkable">Whether the cell is walkable.</param>
    public void SetCellWalkable(int x, int y, bool walkable)
    {
        if (IsValidPosition(x, y))
        {
            _grid[x, y].IsWalkable = walkable;
        }
    }

    /// <summary>
    /// Sets a cell's movement cost.
    /// </summary>
    /// <param name="x">The X coordinate.</param>
    /// <param name="y">The Y coordinate.</param>
    /// <param name="cost">The movement cost.</param>
    public void SetCellCost(int x, int y, float cost)
    {
        if (IsValidPosition(x, y))
        {
            _grid[x, y].Cost = cost;
        }
    }

    /// <summary>
    /// Finds the shortest path between two points using A* algorithm.
    /// </summary>
    /// <param name="startX">Start X coordinate.</param>
    /// <param name="startY">Start Y coordinate.</param>
    /// <param name="endX">End X coordinate.</param>
    /// <param name="endY">End Y coordinate.</param>
    /// <returns>The path as a list of points, or empty if no path exists.</returns>
    public List<(int x, int y)> FindPath(int startX, int startY, int endX, int endY)
    {
        if (!IsValidPosition(startX, startY) || !IsValidPosition(endX, endY))
            return new List<(int, int)>();

        if (!_grid[startX, startY].IsWalkable || !_grid[endX, endY].IsWalkable)
            return new List<(int, int)>();

        var openSet = new SortedSet<PathNode>(new PathNodeComparer());
        var closedSet = new HashSet<(int, int)>();
        var cameFrom = new Dictionary<(int, int), (int, int)>();
        var gScore = new Dictionary<(int, int), float>();
        var fScore = new Dictionary<(int, int), float>();

        var start = (startX, startY);
        var end = (endX, endY);

        gScore[start] = 0;
        fScore[start] = Heuristic(start, end);
        openSet.Add(new PathNode(startX, startY, fScore[start]));

        while (openSet.Count > 0)
        {
            var current = openSet.Min;
            openSet.Remove(current);
            var currentPos = (current.X, current.Y);

            if (currentPos == end)
            {
                return ReconstructPath(cameFrom, currentPos);
            }

            closedSet.Add(currentPos);

            foreach (var neighbor in GetNeighbors(current.X, current.Y))
            {
                if (closedSet.Contains(neighbor))
                    continue;

                float tentativeG = gScore[currentPos] + GetMovementCost(currentPos, neighbor);

                if (!gScore.ContainsKey(neighbor) || tentativeG < gScore[neighbor])
                {
                    cameFrom[neighbor] = currentPos;
                    gScore[neighbor] = tentativeG;
                    fScore[neighbor] = tentativeG + Heuristic(neighbor, end);

                    var neighborNode = new PathNode(neighbor.x, neighbor.y, fScore[neighbor]);
                    if (!openSet.Contains(neighborNode))
                    {
                        openSet.Add(neighborNode);
                    }
                }
            }
        }

        return new List<(int, int)>();
    }

    private List<(int x, int y)> GetNeighbors(int x, int y)
    {
        var neighbors = new List<(int, int)>();

        // Cardinal directions
        int[] dx = { 0, 1, 0, -1 };
        int[] dy = { -1, 0, 1, 0 };

        for (int i = 0; i < 4; i++)
        {
            int nx = x + dx[i];
            int ny = y + dy[i];

            if (IsValidPosition(nx, ny) && _grid[nx, ny].IsWalkable)
            {
                neighbors.Add((nx, ny));
            }
        }

        if (AllowDiagonalMovement)
        {
            int[] ddx = { 1, 1, -1, -1 };
            int[] ddy = { -1, 1, 1, -1 };

            for (int i = 0; i < 4; i++)
            {
                int nx = x + ddx[i];
                int ny = y + ddy[i];

                if (IsValidPosition(nx, ny) && _grid[nx, ny].IsWalkable)
                {
                    // Check if cardinal neighbors are walkable for smooth diagonal movement
                    if (_grid[x + ddx[i], y].IsWalkable && _grid[x, y + ddy[i]].IsWalkable)
                    {
                        neighbors.Add((nx, ny));
                    }
                }
            }
        }

        return neighbors;
    }

    private float Heuristic((int x, int y) a, (int x, int y) b)
    {
        if (AllowDiagonalMovement)
        {
            // Octile distance
            int dx = Math.Abs(a.x - b.x);
            int dy = Math.Abs(a.y - b.y);
            return Math.Max(dx, dy) + (1.414f - 1) * Math.Min(dx, dy);
        }
        else
        {
            // Manhattan distance
            return Math.Abs(a.x - b.x) + Math.Abs(a.y - b.y);
        }
    }

    private float GetMovementCost((int x, int y) from, (int x, int y) to)
    {
        float baseCost = _grid[to.x, to.y].Cost;

        // Diagonal movement costs more
        if (from.x != to.x && from.y != to.y)
        {
            baseCost *= 1.414f;
        }

        return baseCost;
    }

    private bool IsValidPosition(int x, int y)
    {
        return x >= 0 && x < _width && y >= 0 && y < _height;
    }

    private List<(int x, int y)> ReconstructPath(Dictionary<(int, int), (int, int)> cameFrom, (int, int) current)
    {
        var path = new List<(int, int)> { current };
        while (cameFrom.ContainsKey(current))
        {
            current = cameFrom[current];
            path.Add(current);
        }
        path.Reverse();
        return path;
    }

    private struct PathNode
    {
        public int X { get; }
        public int Y { get; }
        public float FScore { get; }

        public PathNode(int x, int y, float fScore)
        {
            X = x;
            Y = y;
            FScore = fScore;
        }
    }

    private class PathNodeComparer : IComparer<PathNode>
    {
        public int Compare(PathNode a, PathNode b)
        {
            int compare = a.FScore.CompareTo(b.FScore);
            if (compare != 0) return compare;
            compare = a.X.CompareTo(b.X);
            if (compare != 0) return compare;
            return a.Y.CompareTo(b.Y);
        }
    }
}
