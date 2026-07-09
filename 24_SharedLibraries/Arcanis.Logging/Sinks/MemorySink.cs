using System.Collections.Concurrent;

namespace Arcanis.Logging.Sinks;

/// <summary>
/// Log sink that stores entries in memory. Useful for testing and debugging.
/// </summary>
public class MemorySink : ILogSink
{
    private readonly ConcurrentQueue<LogEntry> _entries;
    private readonly int _maxEntries;

    /// <inheritdoc/>
    public LogLevel MinimumLevel { get; set; }

    /// <summary>
    /// Gets the number of stored entries.
    /// </summary>
    public int EntryCount => _entries.Count;

    /// <summary>
    /// Initializes a new MemorySink.
    /// </summary>
    /// <param name="minimumLevel">Minimum log level to store.</param>
    /// <param name="maxEntries">Maximum entries to keep (0 for unlimited).</param>
    public MemorySink(LogLevel minimumLevel = LogLevel.Debug, int maxEntries = 10000)
    {
        MinimumLevel = minimumLevel;
        _maxEntries = maxEntries;
        _entries = new ConcurrentQueue<LogEntry>();
    }

    /// <inheritdoc/>
    public void Write(LogEntry entry)
    {
        if (entry.Level < MinimumLevel) return;

        _entries.Enqueue(entry);

        // Remove oldest entries if over limit
        while (_maxEntries > 0 && _entries.Count > _maxEntries)
        {
            _entries.TryDequeue(out _);
        }
    }

    /// <inheritdoc/>
    public Task FlushAsync() => Task.CompletedTask;

    /// <summary>
    /// Gets all stored log entries.
    /// </summary>
    /// <returns>A list of log entries.</returns>
    public List<LogEntry> GetAllEntries()
    {
        return _entries.ToList();
    }

    /// <summary>
    /// Gets entries filtered by level.
    /// </summary>
    /// <param name="level">The minimum log level.</param>
    /// <returns>Filtered entries.</returns>
    public List<LogEntry> GetEntriesByLevel(LogLevel level)
    {
        return _entries.Where(e => e.Level >= level).ToList();
    }

    /// <summary>
    /// Gets entries filtered by category.
    /// </summary>
    /// <param name="category">The category name.</param>
    /// <returns>Filtered entries.</returns>
    public List<LogEntry> GetEntriesByCategory(string category)
    {
        return _entries.Where(e => e.Category == category).ToList();
    }

    /// <summary>
    /// Searches entries by message content.
    /// </summary>
    /// <param name="searchText">The text to search for.</param>
    /// <returns>Matching entries.</returns>
    public List<LogEntry> Search(string searchText)
    {
        return _entries.Where(e => e.Message.Contains(searchText, StringComparison.OrdinalIgnoreCase)).ToList();
    }

    /// <summary>
    /// Clears all stored entries.
    /// </summary>
    public void Clear()
    {
        while (_entries.TryDequeue(out _)) { }
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        Clear();
    }
}
