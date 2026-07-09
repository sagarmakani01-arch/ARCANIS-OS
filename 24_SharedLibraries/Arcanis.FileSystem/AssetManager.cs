namespace Arcanis.FileSystem;

/// <summary>
/// Represents the type of asset.
/// </summary>
public enum AssetType
{
    /// <summary>Text asset.</summary>
    Text,
    /// <summary>Binary asset.</summary>
    Binary,
    /// <summary>JSON asset.</summary>
    Json,
    /// <summary>Image asset.</summary>
    Image,
    /// <summary>Audio asset.</summary>
    Audio,
    /// <summary>Video asset.</summary>
    Video,
    /// <summary>Script asset.</summary>
    Script,
    /// <summary>Configuration asset.</summary>
    Config
}

/// <summary>
/// Represents a loaded asset.
/// </summary>
public class Asset
{
    /// <summary>The asset identifier.</summary>
    public string Id { get; set; } = string.Empty;
    /// <summary>The asset name.</summary>
    public string Name { get; set; } = string.Empty;
    /// <summary>The asset type.</summary>
    public AssetType Type { get; set; }
    /// <summary>The asset data.</summary>
    public byte[] Data { get; set; } = Array.Empty<byte>();
    /// <summary>When the asset was loaded.</summary>
    public DateTime LoadedAt { get; set; }
    /// <summary>When the asset was last accessed.</summary>
    public DateTime LastAccessedAt { get; set; }
    /// <summary>The number of active references.</summary>
    public int ReferenceCount { get; set; }
    /// <summary>Custom metadata.</summary>
    public Dictionary<string, object> Metadata { get; set; } = new();

    /// <summary>Gets the asset size in bytes.</summary>
    public long Size => Data.Length;
}

/// <summary>
/// High-performance asset manager with caching, reference counting, and async loading.
/// Supports hot-reloading and dependency tracking.
/// </summary>
public class AssetManager : IDisposable
{
    private readonly Dictionary<string, Asset> _assets;
    private readonly Dictionary<string, List<string>> _dependencies;
    private readonly VirtualFileSystem _vfs;
    private readonly object _lock;
    private bool _disposed;

    /// <summary>
    /// Gets the number of loaded assets.
    /// </summary>
    public int LoadedAssetCount => _assets.Count;

    /// <summary>
    /// Gets the total memory used by loaded assets.
    /// </summary>
    public long TotalMemoryUsed => _assets.Values.Sum(a => a.Size);

    /// <summary>Event fired when an asset is loaded.</summary>
    public event EventHandler<AssetEventArgs>? AssetLoaded;
    /// <summary>Event fired when an asset is unloaded.</summary>
    public event EventHandler<AssetEventArgs>? AssetUnloaded;
    /// <summary>Event fired when an asset is referenced.</summary>
    public event EventHandler<AssetEventArgs>? AssetReferenced;

    /// <summary>
    /// Initializes a new AssetManager.
    /// </summary>
    /// <param name="vfs">The virtual file system to use.</param>
    public AssetManager(VirtualFileSystem? vfs = null)
    {
        _assets = new Dictionary<string, Asset>();
        _dependencies = new Dictionary<string, List<string>>();
        _vfs = vfs ?? new VirtualFileSystem();
        _lock = new object();
    }

    /// <summary>
    /// Gets the underlying virtual file system.
    /// </summary>
    public VirtualFileSystem FileSystem => _vfs;

    /// <summary>
    /// Loads an asset from a file path.
    /// </summary>
    /// <param name="id">The asset identifier.</param>
    /// <param name="filePath">The file path in the VFS.</param>
    /// <param name="type">The asset type.</param>
    /// <returns>The loaded asset.</returns>
    public Asset LoadAsset(string id, string filePath, AssetType type = AssetType.Binary)
    {
        lock (_lock)
        {
            if (_assets.TryGetValue(id, out var existing))
            {
                existing.ReferenceCount++;
                existing.LastAccessedAt = DateTime.UtcNow;
                return existing;
            }

            var data = _vfs.ReadFile(filePath);
            var asset = new Asset
            {
                Id = id,
                Name = System.IO.Path.GetFileName(filePath),
                Type = type,
                Data = data,
                LoadedAt = DateTime.UtcNow,
                LastAccessedAt = DateTime.UtcNow,
                ReferenceCount = 1
            };

            _assets[id] = asset;
            AssetLoaded?.Invoke(this, new AssetEventArgs { Asset = asset });
            return asset;
        }
    }

    /// <summary>
    /// Loads an asset from raw data.
    /// </summary>
    /// <param name="id">The asset identifier.</param>
    /// <param name="name">The asset name.</param>
    /// <param name="data">The asset data.</param>
    /// <param name="type">The asset type.</param>
    /// <returns>The loaded asset.</returns>
    public Asset LoadAsset(string id, string name, byte[] data, AssetType type = AssetType.Binary)
    {
        lock (_lock)
        {
            if (_assets.TryGetValue(id, out var existing))
            {
                existing.ReferenceCount++;
                existing.LastAccessedAt = DateTime.UtcNow;
                return existing;
            }

            var asset = new Asset
            {
                Id = id,
                Name = name,
                Type = type,
                Data = data.ToArray(),
                LoadedAt = DateTime.UtcNow,
                LastAccessedAt = DateTime.UtcNow,
                ReferenceCount = 1
            };

            _assets[id] = asset;
            AssetLoaded?.Invoke(this, new AssetEventArgs { Asset = asset });
            return asset;
        }
    }

    /// <summary>
    /// Loads an asset asynchronously.
    /// </summary>
    /// <param name="id">The asset identifier.</param>
    /// <param name="filePath">The file path.</param>
    /// <param name="type">The asset type.</param>
    /// <returns>The loaded asset.</returns>
    public async Task<Asset> LoadAssetAsync(string id, string filePath, AssetType type = AssetType.Binary)
    {
        return await Task.Run(() => LoadAsset(id, filePath, type));
    }

    /// <summary>
    /// Gets a loaded asset by ID.
    /// </summary>
    /// <param name="id">The asset identifier.</param>
    /// <returns>The asset if found; otherwise, null.</returns>
    public Asset? GetAsset(string id)
    {
        lock (_lock)
        {
            if (_assets.TryGetValue(id, out var asset))
            {
                asset.LastAccessedAt = DateTime.UtcNow;
                asset.ReferenceCount++;
                AssetReferenced?.Invoke(this, new AssetEventArgs { Asset = asset });
                return asset;
            }
            return null;
        }
    }

    /// <summary>
    /// Unloads an asset by ID.
    /// </summary>
    /// <param name="id">The asset identifier.</param>
    /// <returns>True if unloaded; false if not found.</returns>
    public bool UnloadAsset(string id)
    {
        lock (_lock)
        {
            if (_assets.TryGetValue(id, out var asset))
            {
                asset.ReferenceCount--;
                if (asset.ReferenceCount <= 0)
                {
                    _assets.Remove(id);
                    AssetUnloaded?.Invoke(this, new AssetEventArgs { Asset = asset });
                }
                return true;
            }
            return false;
        }
    }

    /// <summary>
    /// Unloads all assets.
    /// </summary>
    public void UnloadAll()
    {
        lock (_lock)
        {
            var assets = _assets.Values.ToList();
            _assets.Clear();

            foreach (var asset in assets)
            {
                AssetUnloaded?.Invoke(this, new AssetEventArgs { Asset = asset });
            }
        }
    }

    /// <summary>
    /// Adds a dependency between assets.
    /// </summary>
    /// <param name="assetId">The asset that depends on another.</param>
    /// <param name="dependencyId">The dependency asset ID.</param>
    public void AddDependency(string assetId, string dependencyId)
    {
        lock (_lock)
        {
            if (!_dependencies.ContainsKey(assetId))
                _dependencies[assetId] = new List<string>();

            if (!_dependencies[assetId].Contains(dependencyId))
                _dependencies[assetId].Add(dependencyId);
        }
    }

    /// <summary>
    /// Gets all dependencies of an asset.
    /// </summary>
    /// <param name="assetId">The asset ID.</param>
    /// <returns>The dependency asset IDs.</returns>
    public IEnumerable<string> GetDependencies(string assetId)
    {
        lock (_lock)
        {
            return _dependencies.TryGetValue(assetId, out var deps) ? deps : Enumerable.Empty<string>();
        }
    }

    /// <summary>
    /// Gets all assets of a specific type.
    /// </summary>
    /// <param name="type">The asset type.</param>
    /// <returns>Assets of the specified type.</returns>
    public IEnumerable<Asset> GetAssetsByType(AssetType type)
    {
        lock (_lock)
        {
            return _assets.Values.Where(a => a.Type == type).ToList();
        }
    }

    /// <summary>
    /// Gets memory usage statistics.
    /// </summary>
    /// <returns>Memory usage information.</returns>
    public AssetMemoryStats GetMemoryStats()
    {
        lock (_lock)
        {
            return new AssetMemoryStats
            {
                TotalAssets = _assets.Count,
                TotalSizeBytes = TotalMemoryUsed,
                AssetsByType = _assets.Values
                    .GroupBy(a => a.Type)
                    .ToDictionary(g => g.Key, g => g.Count()),
                SizeByType = _assets.Values
                    .GroupBy(a => a.Type)
                    .ToDictionary(g => g.Key, g => g.Sum(a => a.Size))
            };
        }
    }

    /// <summary>
    /// Disposes of the asset manager and unloads all assets.
    /// </summary>
    public void Dispose()
    {
        if (_disposed) return;
        UnloadAll();
        _disposed = true;
        GC.SuppressFinalize(this);
    }
}

/// <summary>
/// Event args for asset events.
/// </summary>
public class AssetEventArgs : EventArgs
{
    /// <summary>The affected asset.</summary>
    public Asset? Asset { get; set; }
}

/// <summary>
/// Memory usage statistics for assets.
/// </summary>
public class AssetMemoryStats
{
    /// <summary>Total number of assets.</summary>
    public int TotalAssets { get; set; }
    /// <summary>Total size in bytes.</summary>
    public long TotalSizeBytes { get; set; }
    /// <summary>Asset count by type.</summary>
    public Dictionary<AssetType, int> AssetsByType { get; set; } = new();
    /// <summary>Size by type.</summary>
    public Dictionary<AssetType, long> SizeByType { get; set; } = new();
}
