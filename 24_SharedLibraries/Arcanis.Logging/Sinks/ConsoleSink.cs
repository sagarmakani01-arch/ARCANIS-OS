namespace Arcanis.Logging.Sinks;

/// <summary>
/// Log sink that writes to the console with color coding.
/// </summary>
public class ConsoleSink : ILogSink
{
    private readonly bool _useColors;
    private readonly bool _useTimestamps;
    private readonly object _lock;

    /// <inheritdoc/>
    public LogLevel MinimumLevel { get; set; }

    /// <summary>
    /// Initializes a new ConsoleSink.
    /// </summary>
    /// <param name="minimumLevel">Minimum log level to output.</param>
    /// <param name="useColors">Whether to use color coding.</param>
    /// <param name="useTimestamps">Whether to include timestamps.</param>
    public ConsoleSink(LogLevel minimumLevel = LogLevel.Information, bool useColors = true, bool useTimestamps = true)
    {
        MinimumLevel = minimumLevel;
        _useColors = useColors;
        _useTimestamps = useTimestamps;
        _lock = new object();
    }

    /// <inheritdoc/>
    public void Write(LogEntry entry)
    {
        lock (_lock)
        {
            if (_useColors)
            {
                var originalColor = Console.ForegroundColor;
                Console.ForegroundColor = GetColorForLevel(entry.Level);

                try
                {
                    WriteEntry(entry);
                }
                finally
                {
                    Console.ForegroundColor = originalColor;
                }
            }
            else
            {
                WriteEntry(entry);
            }
        }
    }

    private void WriteEntry(LogEntry entry)
    {
        var timestamp = _useTimestamps ? $"{entry.Timestamp:HH:mm:ss.fff} " : "";
        var category = string.IsNullOrEmpty(entry.Category) ? "" : $"[{entry.Category}] ";
        var level = $"[{entry.Level.ToString().ToUpper()}] ";

        Console.WriteLine($"{timestamp}{category}{level}{entry.Message}");

        if (entry.Exception != null)
        {
            Console.WriteLine($"  Exception: {entry.Exception.Message}");
        }
    }

    private ConsoleColor GetColorForLevel(LogLevel level)
    {
        return level switch
        {
            LogLevel.Debug => ConsoleColor.Gray,
            LogLevel.Information => ConsoleColor.White,
            LogLevel.Warning => ConsoleColor.Yellow,
            LogLevel.Error => ConsoleColor.Red,
            LogLevel.Critical => ConsoleColor.DarkRed,
            _ => ConsoleColor.White
        };
    }

    /// <inheritdoc/>
    public Task FlushAsync() => Task.CompletedTask;

    /// <inheritdoc/>
    public void Dispose() { }
}
