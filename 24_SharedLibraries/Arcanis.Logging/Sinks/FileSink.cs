using System.Text;

namespace Arcanis.Logging.Sinks;

/// <summary>
/// Log sink that writes to files with automatic rotation.
/// </summary>
public class FileSink : ILogSink
{
    private readonly string _directory;
    private readonly string _filePrefix;
    private readonly object _lock;
    private StreamWriter? _writer;
    private DateTime _currentDate;
    private long _currentFileSize;
    private readonly long _maxFileSize;
    private readonly bool _appendMode;

    /// <inheritdoc/>
    public LogLevel MinimumLevel { get; set; }

    /// <summary>
    /// Gets or sets the maximum file size in bytes before rotation.
    /// </summary>
    public long MaxFileSize
    {
        get => _maxFileSize;
    }

    /// <summary>
    /// Initializes a new FileSink.
    /// </summary>
    /// <param name="directory">The log directory.</param>
    /// <param name="filePrefix">The log file prefix.</param>
    /// <param name="minimumLevel">Minimum log level to write.</param>
    /// <param name="maxFileSize">Maximum file size before rotation.</param>
    /// <param name="appendMode">Whether to append to existing files.</param>
    public FileSink(string directory, string filePrefix = "log", LogLevel minimumLevel = LogLevel.Information,
        long maxFileSize = 10 * 1024 * 1024, bool appendMode = true)
    {
        _directory = directory;
        _filePrefix = filePrefix;
        MinimumLevel = minimumLevel;
        _maxFileSize = maxFileSize;
        _appendMode = appendMode;
        _lock = new object();
        _currentDate = DateTime.Today;
        _currentFileSize = 0;

        if (!Directory.Exists(_directory))
        {
            Directory.CreateDirectory(_directory);
        }

        OpenLogFile();
    }

    private void OpenLogFile()
    {
        var fileName = $"{_filePrefix}_{_currentDate:yyyyMMdd}.log";
        var filePath = Path.Combine(_directory, fileName);

        var stream = new FileStream(filePath, _appendMode ? FileMode.Append : FileMode.Create, FileAccess.Write, FileShare.Read);
        _writer = new StreamWriter(stream, Encoding.UTF8) { AutoFlush = true };

        if (_appendMode)
        {
            _currentFileSize = new FileInfo(filePath).Length;
        }
    }

    private void RotateFileIfNeeded()
    {
        if (_currentFileSize >= _maxFileSize || DateTime.Today != _currentDate)
        {
            _writer?.Flush();
            _writer?.Dispose();

            _currentDate = DateTime.Today;
            _currentFileSize = 0;

            OpenLogFile();
        }
    }

    /// <inheritdoc/>
    public void Write(LogEntry entry)
    {
        lock (_lock)
        {
            if (entry.Level < MinimumLevel) return;

            RotateFileIfNeeded();

            var timestamp = entry.Timestamp.ToString("yyyy-MM-dd HH:mm:ss.fff");
            var category = string.IsNullOrEmpty(entry.Category) ? "" : $" [{entry.Category}]";
            var line = $"{timestamp} [{entry.Level.ToString().ToUpper().PadRight(8)}]{category} {entry.Message}";

            if (entry.Exception != null)
            {
                line += $"\n  Exception: {entry.Exception.GetType().Name}: {entry.Exception.Message}";
                if (entry.Exception.StackTrace != null)
                {
                    line += $"\n  Stack Trace:\n{entry.Exception.StackTrace}";
                }
            }

            if (entry.Properties.Count > 0)
            {
                line += $"\n  Properties: {string.Join(", ", entry.Properties.Select(p => $"{p.Key}={p.Value}"))}";
            }

            _writer?.WriteLine(line);
            _currentFileSize += Encoding.UTF8.GetByteCount(line) + 1;
        }
    }

    /// <inheritdoc/>
    public Task FlushAsync()
    {
        lock (_lock)
        {
            _writer?.Flush();
        }
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        lock (_lock)
        {
            _writer?.Flush();
            _writer?.Dispose();
        }
    }
}
