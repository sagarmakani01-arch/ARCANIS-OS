namespace Arcanis.Logging;

/// <summary>
/// Interface for log sinks that output log entries to various destinations.
/// </summary>
public interface ILogSink : IDisposable
{
    /// <summary>Gets the minimum log level for this sink.</summary>
    LogLevel MinimumLevel { get; }

    /// <summary>Writes a log entry.</summary>
    /// <param name="entry">The log entry to write.</param>
    void Write(LogEntry entry);

    /// <summary>Flushes any buffered log entries.</summary>
    Task FlushAsync();
}

/// <summary>
/// Interface for log filters that determine which entries are logged.
/// </summary>
public interface ILogFilter
{
    /// <summary>Determines if a log entry should be logged.</summary>
    /// <param name="entry">The log entry.</param>
    /// <returns>True if the entry should be logged; otherwise, false.</returns>
    bool ShouldLog(LogEntry entry);
}

/// <summary>
/// High-performance logger with multiple sinks, filtering, and structured logging.
/// Thread-safe implementation using lock-free operations where possible.
/// </summary>
public sealed class Logger : IDisposable
{
    private readonly List<ILogSink> _sinks;
    private readonly List<ILogFilter> _filters;
    private readonly string _category;
    private readonly object _lock;
    private bool _disposed;

    /// <summary>
    /// Gets the category name for this logger.
    /// </summary>
    public string Category => _category;

    /// <summary>Event fired when a log entry is written.</summary>
    public event EventHandler<LogEntry>? EntryWritten;

    /// <summary>
    /// Initializes a new Logger.
    /// </summary>
    /// <param name="category">The logger category name.</param>
    public Logger(string category = "")
    {
        _category = category;
        _sinks = new List<ILogSink>();
        _filters = new List<ILogFilter>();
        _lock = new object();
    }

    /// <summary>
    /// Initializes a new Logger with sinks.
    /// </summary>
    /// <param name="category">The logger category name.</param>
    /// <param name="sinks">The log sinks.</param>
    public Logger(string category, params ILogSink[] sinks) : this(category)
    {
        _sinks.AddRange(sinks);
    }

    /// <summary>
    /// Adds a log sink.
    /// </summary>
    /// <param name="sink">The sink to add.</param>
    /// <returns>This logger for chaining.</returns>
    public Logger AddSink(ILogSink sink)
    {
        lock (_lock)
        {
            _sinks.Add(sink);
        }
        return this;
    }

    /// <summary>
    /// Removes a log sink.
    /// </summary>
    /// <param name="sink">The sink to remove.</param>
    /// <returns>This logger for chaining.</returns>
    public Logger RemoveSink(ILogSink sink)
    {
        lock (_lock)
        {
            _sinks.Remove(sink);
        }
        return this;
    }

    /// <summary>
    /// Adds a log filter.
    /// </summary>
    /// <param name="filter">The filter to add.</param>
    /// <returns>This logger for chaining.</returns>
    public Logger AddFilter(ILogFilter filter)
    {
        lock (_lock)
        {
            _filters.Add(filter);
        }
        return this;
    }

    /// <summary>
    /// Writes a debug log entry.
    /// </summary>
    /// <param name="message">The log message.</param>
    public void Debug(string message) => Log(LogLevel.Debug, message);

    /// <summary>
    /// Writes an informational log entry.
    /// </summary>
    /// <param name="message">The log message.</param>
    public void Information(string message) => Log(LogLevel.Information, message);

    /// <summary>
    /// Writes a warning log entry.
    /// </summary>
    /// <param name="message">The log message.</param>
    public void Warning(string message) => Log(LogLevel.Warning, message);

    /// <summary>
    /// Writes an error log entry.
    /// </summary>
    /// <param name="message">The log message.</param>
    /// <param name="exception">Optional exception.</param>
    public void Error(string message, Exception? exception = null) => Log(LogLevel.Error, message, exception);

    /// <summary>
    /// Writes a critical log entry.
    /// </summary>
    /// <param name="message">The log message.</param>
    /// <param name="exception">Optional exception.</param>
    public void Critical(string message, Exception? exception = null) => Log(LogLevel.Critical, message, exception);

    /// <summary>
    /// Writes a log entry.
    /// </summary>
    /// <param name="level">The log level.</param>
    /// <param name="message">The log message.</param>
    /// <param name="exception">Optional exception.</param>
    /// <param name="properties">Optional properties.</param>
    public void Log(LogLevel level, string message, Exception? exception = null, Dictionary<string, object>? properties = null)
    {
        var entry = new LogEntry(level, message, _category)
        {
            Exception = exception
        };

        if (properties != null)
        {
            foreach (var kvp in properties)
            {
                entry.Properties[kvp.Key] = kvp.Value;
            }
        }

        WriteEntry(entry);
    }

    /// <summary>
    /// Writes a log entry with the specified level.
    /// </summary>
    /// <param name="entry">The log entry.</param>
    public void WriteEntry(LogEntry entry)
    {
        if (_disposed) return;

        // Apply filters
        lock (_lock)
        {
            foreach (var filter in _filters)
            {
                if (!filter.ShouldLog(entry))
                    return;
            }
        }

        // Write to sinks
        lock (_lock)
        {
            foreach (var sink in _sinks)
            {
                if (entry.Level >= sink.MinimumLevel)
                {
                    try
                    {
                        sink.Write(entry);
                    }
                    catch (Exception)
                    {
                        // Silently ignore sink errors to prevent cascade failures
                    }
                }
            }
        }

        EntryWritten?.Invoke(this, entry);
    }

    /// <summary>
    /// Flushes all sinks asynchronously.
    /// </summary>
    public async Task FlushAsync()
    {
        lock (_lock)
        {
            foreach (var sink in _sinks)
            {
                try
                {
                    sink.FlushAsync();
                }
                catch (Exception)
                {
                    // Ignore flush errors
                }
            }
        }
    }

    /// <summary>
    /// Disposes of the logger and all its sinks.
    /// </summary>
    public void Dispose()
    {
        if (_disposed) return;

        lock (_lock)
        {
            foreach (var sink in _sinks)
            {
                try
                {
                    sink.Dispose();
                }
                catch (Exception)
                {
                    // Ignore disposal errors
                }
            }
            _sinks.Clear();
        }

        _disposed = true;
        GC.SuppressFinalize(this);
    }
}
