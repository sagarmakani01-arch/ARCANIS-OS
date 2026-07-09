namespace Arcanis.Logging;

/// <summary>
/// Represents the severity level of a log message.
/// </summary>
public enum LogLevel
{
    /// <summary>Detailed debug information.</summary>
    Debug,
    /// <summary>General informational messages.</summary>
    Information,
    /// <summary>Potential issues that don't prevent execution.</summary>
    Warning,
    /// <summary>Errors that affect execution.</summary>
    Error,
    /// <summary>Critical failures requiring immediate attention.</summary>
    Critical,
    /// <summary>No logging.</summary>
    None
}

/// <summary>
/// Represents a structured log entry with metadata.
/// </summary>
public class LogEntry
{
    /// <summary>The unique log entry identifier.</summary>
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>When the log was created.</summary>
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;

    /// <summary>The log level.</summary>
    public LogLevel Level { get; set; }

    /// <summary>The log message.</summary>
    public string Message { get; set; } = string.Empty;

    /// <summary>The source category/logger name.</summary>
    public string Category { get; set; } = string.Empty;

    /// <summary>The exception information (if any).</summary>
    public Exception? Exception { get; set; }

    /// <summary>Additional properties.</summary>
    public Dictionary<string, object> Properties { get; set; } = new();

    /// <summary>The thread ID.</summary>
    public int ThreadId { get; set; } = Environment.CurrentManagedThreadId;

    /// <summary>The machine name.</summary>
    public string MachineName { get; set; } = Environment.MachineName;

    /// <summary>
    /// Creates a new log entry.
    /// </summary>
    public LogEntry() { }

    /// <summary>
    /// Creates a new log entry with level and message.
    /// </summary>
    public LogEntry(LogLevel level, string message, string category = "")
    {
        Level = level;
        Message = message;
        Category = category;
    }

    /// <summary>
    /// Adds a property to the log entry.
    /// </summary>
    /// <param name="key">The property key.</param>
    /// <param name="value">The property value.</param>
    /// <returns>This log entry for chaining.</returns>
    public LogEntry WithProperty(string key, object value)
    {
        Properties[key] = value;
        return this;
    }

    /// <summary>
    /// Returns a formatted string representation.
    /// </summary>
    public override string ToString()
    {
        var levelStr = Level.ToString().ToUpper().PadRight(8);
        var timestamp = Timestamp.ToString("yyyy-MM-dd HH:mm:ss.fff");
        var category = string.IsNullOrEmpty(Category) ? "" : $" [{Category}]";

        var result = $"{timestamp} {levelStr}{category} {Message}";

        if (Exception != null)
        {
            result += $"\n  Exception: {Exception.GetType().Name}: {Exception.Message}";
            if (Exception.StackTrace != null)
            {
                result += $"\n  Stack Trace: {Exception.StackTrace}";
            }
        }

        if (Properties.Count > 0)
        {
            result += $"\n  Properties: {string.Join(", ", Properties.Select(p => $"{p.Key}={p.Value}"))}";
        }

        return result;
    }
}
