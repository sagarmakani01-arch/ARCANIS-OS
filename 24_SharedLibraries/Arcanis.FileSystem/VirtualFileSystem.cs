using System.Text;

namespace Arcanis.FileSystem;

/// <summary>
/// Represents a virtual file system entry.
/// </summary>
public class VirtualFileSystemEntry
{
    /// <summary>The entry name.</summary>
    public string Name { get; set; } = string.Empty;
    /// <summary>The full path.</summary>
    public string Path { get; set; } = string.Empty;
    /// <summary>Whether this is a directory.</summary>
    public bool IsDirectory { get; set; }
    /// <summary>The entry content (null for directories).</summary>
    public byte[]? Content { get; set; }
    /// <summary>Creation time.</summary>
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    /// <summary>Last modification time.</summary>
    public DateTime ModifiedAt { get; set; } = DateTime.UtcNow;
    /// <summary>File attributes.</summary>
    public Dictionary<string, object> Attributes { get; set; } = new();

    /// <summary>
    /// Gets the file size in bytes.
    /// </summary>
    public long Size => Content?.Length ?? 0;
}

/// <summary>
/// High-performance virtual file system for in-memory file operations.
/// Supports directories, file operations, and file watching.
/// </summary>
public class VirtualFileSystem
{
    private readonly Dictionary<string, VirtualFileSystemEntry> _entries;
    private readonly object _lock;

    /// <summary>
    /// Gets the number of entries in the file system.
    /// </summary>
    public int EntryCount => _entries.Count;

    /// <summary>
    /// Gets all file paths.
    /// </summary>
    public IEnumerable<string> Files => _entries.Values
        .Where(e => !e.IsDirectory)
        .Select(e => e.Path);

    /// <summary>
    /// Gets all directory paths.
    /// </summary>
    public IEnumerable<string> Directories => _entries.Values
        .Where(e => e.IsDirectory)
        .Select(e => e.Path);

    /// <summary>Event fired when a file is created.</summary>
    public event EventHandler<VirtualFileSystemEventArgs>? FileCreated;
    /// <summary>Event fired when a file is modified.</summary>
    public event EventHandler<VirtualFileSystemEventArgs>? FileModified;
    /// <summary>Event fired when a file is deleted.</summary>
    public event EventHandler<VirtualFileSystemEventArgs>? FileDeleted;

    /// <summary>
    /// Initializes a new VirtualFileSystem.
    /// </summary>
    public VirtualFileSystem()
    {
        _entries = new Dictionary<string, VirtualFileSystemEntry>();
        _lock = new object();
    }

    /// <summary>
    /// Normalizes a path (replaces backslashes, removes trailing slashes).
    /// </summary>
    /// <param name="path">The path to normalize.</param>
    /// <returns>The normalized path.</returns>
    public static string NormalizePath(string path)
    {
        return path.Replace('\\', '/').TrimEnd('/');
    }

    /// <summary>
    /// Creates a directory.
    /// </summary>
    /// <param name="path">The directory path.</param>
    public void CreateDirectory(string path)
    {
        path = NormalizePath(path);

        lock (_lock)
        {
            if (_entries.ContainsKey(path))
                throw new InvalidOperationException($"Path '{path}' already exists.");

            _entries[path] = new VirtualFileSystemEntry
            {
                Name = path.Split('/').Last(),
                Path = path,
                IsDirectory = true
            };
        }
    }

    /// <summary>
    /// Creates or overwrites a file with content.
    /// </summary>
    /// <param name="path">The file path.</param>
    /// <param name="content">The file content.</param>
    public void CreateFile(string path, byte[] content)
    {
        path = NormalizePath(path);

        lock (_lock)
        {
            var entry = new VirtualFileSystemEntry
            {
                Name = path.Split('/').Last(),
                Path = path,
                IsDirectory = false,
                Content = content,
                ModifiedAt = DateTime.UtcNow
            };

            bool isNew = !_entries.ContainsKey(path);
            _entries[path] = entry;

            if (isNew)
                FileCreated?.Invoke(this, new VirtualFileSystemEventArgs { Path = path });
            else
                FileModified?.Invoke(this, new VirtualFileSystemEventArgs { Path = path });
        }
    }

    /// <summary>
    /// Creates or overwrites a file with text content.
    /// </summary>
    /// <param name="path">The file path.</param>
    /// <param name="content">The text content.</param>
    /// <param name="encoding">Optional encoding (default: UTF8).</param>
    public void CreateFile(string path, string content, Encoding? encoding = null)
    {
        encoding ??= Encoding.UTF8;
        CreateFile(path, encoding.GetBytes(content));
    }

    /// <summary>
    /// Reads a file's content.
    /// </summary>
    /// <param name="path">The file path.</param>
    /// <returns>The file content.</returns>
    public byte[] ReadFile(string path)
    {
        path = NormalizePath(path);

        lock (_lock)
        {
            if (!_entries.TryGetValue(path, out var entry))
                throw new FileNotFoundException($"File '{path}' not found.");

            if (entry.IsDirectory)
                throw new InvalidOperationException($"'{path}' is a directory.");

            return entry.Content ?? Array.Empty<byte>();
        }
    }

    /// <summary>
    /// Reads a file as text.
    /// </summary>
    /// <param name="path">The file path.</param>
    /// <param name="encoding">Optional encoding (default: UTF8).</param>
    /// <returns>The file content as text.</returns>
    public string ReadFileAsText(string path, Encoding? encoding = null)
    {
        encoding ??= Encoding.UTF8;
        return encoding.GetString(ReadFile(path));
    }

    /// <summary>
    /// Deletes a file or directory.
    /// </summary>
    /// <param name="path">The path to delete.</param>
    /// <returns>True if deleted; false if not found.</returns>
    public bool Delete(string path)
    {
        path = NormalizePath(path);

        lock (_lock)
        {
            if (_entries.Remove(path))
            {
                FileDeleted?.Invoke(this, new VirtualFileSystemEventArgs { Path = path });
                return true;
            }
            return false;
        }
    }

    /// <summary>
    /// Checks if a path exists.
    /// </summary>
    /// <param name="path">The path to check.</param>
    /// <returns>True if the path exists; otherwise, false.</returns>
    public bool Exists(string path)
    {
        path = NormalizePath(path);
        lock (_lock)
        {
            return _entries.ContainsKey(path);
        }
    }

    /// <summary>
    /// Checks if a path is a directory.
    /// </summary>
    /// <param name="path">The path to check.</param>
    /// <returns>True if the path is a directory; otherwise, false.</returns>
    public bool IsDirectory(string path)
    {
        path = NormalizePath(path);
        lock (_lock)
        {
            return _entries.TryGetValue(path, out var entry) && entry.IsDirectory;
        }
    }

    /// <summary>
    /// Lists files in a directory.
    /// </summary>
    /// <param name="directoryPath">The directory path (empty for root).</param>
    /// <returns>A list of file entries in the directory.</returns>
    public List<VirtualFileSystemEntry> ListFiles(string directoryPath = "")
    {
        directoryPath = NormalizePath(directoryPath);

        lock (_lock)
        {
            return _entries.Values
                .Where(e => !e.IsDirectory && GetParentPath(e.Path) == directoryPath)
                .ToList();
        }
    }

    /// <summary>
    /// Lists subdirectories in a directory.
    /// </summary>
    /// <param name="directoryPath">The directory path (empty for root).</param>
    /// <returns>A list of directory entries.</returns>
    public List<VirtualFileSystemEntry> ListDirectories(string directoryPath = "")
    {
        directoryPath = NormalizePath(directoryPath);

        lock (_lock)
        {
            return _entries.Values
                .Where(e => e.IsDirectory && GetParentPath(e.Path) == directoryPath)
                .ToList();
        }
    }

    /// <summary>
    /// Gets file information.
    /// </summary>
    /// <param name="path">The file path.</param>
    /// <returns>The file entry if found; otherwise, null.</returns>
    public VirtualFileSystemEntry? GetEntry(string path)
    {
        path = NormalizePath(path);
        lock (_lock)
        {
            return _entries.TryGetValue(path, out var entry) ? entry : null;
        }
    }

    /// <summary>
    /// Moves a file or directory.
    /// </summary>
    /// <param name="sourcePath">The source path.</param>
    /// <param name="destinationPath">The destination path.</param>
    public void Move(string sourcePath, string destinationPath)
    {
        sourcePath = NormalizePath(sourcePath);
        destinationPath = NormalizePath(destinationPath);

        lock (_lock)
        {
            if (!_entries.TryGetValue(sourcePath, out var entry))
                throw new FileNotFoundException($"Source '{sourcePath}' not found.");

            if (_entries.ContainsKey(destinationPath))
                throw new InvalidOperationException($"Destination '{destinationPath}' already exists.");

            _entries.Remove(sourcePath);
            entry.Path = destinationPath;
            entry.Name = destinationPath.Split('/').Last();
            entry.ModifiedAt = DateTime.UtcNow;
            _entries[destinationPath] = entry;
        }
    }

    /// <summary>
    /// Copies a file.
    /// </summary>
    /// <param name="sourcePath">The source path.</param>
    /// <param name="destinationPath">The destination path.</param>
    public void Copy(string sourcePath, string destinationPath)
    {
        sourcePath = NormalizePath(sourcePath);
        destinationPath = NormalizePath(destinationPath);

        lock (_lock)
        {
            if (!_entries.TryGetValue(sourcePath, out var source))
                throw new FileNotFoundException($"Source '{sourcePath}' not found.");

            if (source.IsDirectory)
                throw new InvalidOperationException("Cannot copy a directory.");

            var copy = new VirtualFileSystemEntry
            {
                Name = destinationPath.Split('/').Last(),
                Path = destinationPath,
                IsDirectory = false,
                Content = source.Content?.ToArray(),
                CreatedAt = DateTime.UtcNow,
                ModifiedAt = DateTime.UtcNow
            };

            _entries[destinationPath] = copy;
        }
    }

    /// <summary>
    /// Gets all entries matching a pattern.
    /// </summary>
    /// <param name="pattern">The search pattern (supports * and ?).</param>
    /// <returns>Matching entries.</returns>
    public IEnumerable<VirtualFileSystemEntry> Search(string pattern)
    {
        lock (_lock)
        {
            var regex = new System.Text.RegularExpressions.Regex(
                "^" + System.Text.RegularExpressions.Regex.Escape(pattern)
                    .Replace("\\*", ".*")
                    .Replace("\\?", ".") + "$",
                System.Text.RegularExpressions.RegexOptions.IgnoreCase);

            return _entries.Values.Where(e => regex.IsMatch(e.Name)).ToList();
        }
    }

    private string GetParentPath(string path)
    {
        var lastSlash = path.LastIndexOf('/');
        return lastSlash >= 0 ? path.Substring(0, lastSlash) : string.Empty;
    }
}

/// <summary>
/// Event args for virtual file system events.
/// </summary>
public class VirtualFileSystemEventArgs : EventArgs
{
    /// <summary>The affected path.</summary>
    public string Path { get; set; } = string.Empty;
}
