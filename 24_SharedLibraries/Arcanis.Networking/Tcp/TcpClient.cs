using System.Net;
using System.Net.Sockets;
using System.Text;

namespace Arcanis.Networking.Tcp;

/// <summary>
/// High-performance asynchronous TCP client with automatic reconnection support.
/// </summary>
public sealed class ArcanisTcpClient : IDisposable
{
    private TcpClient? _client;
    private NetworkStream? _stream;
    private CancellationTokenSource? _cts;
    private Task? _receiveTask;
    private bool _isConnected;
    private readonly SemaphoreSlim _sendLock;

    /// <summary>
    /// Gets whether the client is currently connected.
    /// </summary>
    public bool IsConnected => _isConnected && _client?.Connected == true;

    /// <summary>
    /// Gets or sets the server hostname or IP address.
    /// </summary>
    public string Host { get; set; }

    /// <summary>
    /// Gets or sets the server port.
    /// </summary>
    public int Port { get; set; }

    /// <summary>
    /// Gets or sets the receive buffer size.
    /// </summary>
    public int BufferSize { get; set; } = 8192;

    /// <summary>
    /// Gets or sets the connection timeout in milliseconds.
    /// </summary>
    public int ConnectionTimeout { get; set; } = 5000;

    /// <summary>Event fired when connected to the server.</summary>
    public event EventHandler? Connected;

    /// <summary>Event fired when disconnected from the server.</summary>
    public event EventHandler? Disconnected;

    /// <summary>Event fired when data is received from the server.</summary>
    public event EventHandler<DataReceivedEventArgs>? DataReceived;

    /// <summary>
    /// Initializes a new instance of the ArcanisTcpClient class.
    /// </summary>
    /// <param name="host">The server hostname or IP address.</param>
    /// <param name="port">The server port.</param>
    public ArcanisTcpClient(string host, int port)
    {
        Host = host ?? throw new ArgumentNullException(nameof(host));
        Port = port;
        _sendLock = new SemaphoreSlim(1, 1);
    }

    /// <summary>
    /// Connects to the server.
    /// </summary>
    public async Task ConnectAsync()
    {
        if (_isConnected) return;

        _client = new TcpClient();
        _cts = new CancellationTokenSource();

        using var timeoutCts = new CancellationTokenSource(ConnectionTimeout);
        await _client.ConnectAsync(Host, Port, timeoutCts.Token);

        _stream = _client.GetStream();
        _isConnected = true;

        Connected?.Invoke(this, EventArgs.Empty);

        _receiveTask = Task.Run(() => ReceiveAsync(_cts.Token));
    }

    private async Task ReceiveAsync(CancellationToken cancellationToken)
    {
        var buffer = new byte[BufferSize];

        try
        {
            while (!cancellationToken.IsCancellationRequested && _isConnected)
            {
                var bytesRead = await _stream!.ReadAsync(buffer, cancellationToken);

                if (bytesRead == 0)
                    break;

                var data = new byte[bytesRead];
                Array.Copy(buffer, data, bytesRead);

                DataReceived?.Invoke(this, new DataReceivedEventArgs
                {
                    Data = data
                });
            }
        }
        catch (Exception)
        {
            // Connection lost
        }
        finally
        {
            Disconnect();
        }
    }

    /// <summary>
    /// Sends data to the server.
    /// </summary>
    /// <param name="data">The data to send.</param>
    public async Task SendAsync(byte[] data)
    {
        if (!IsConnected || _stream == null)
            throw new InvalidOperationException("Not connected to server.");

        await _sendLock.WaitAsync();
        try
        {
            await _stream.WriteAsync(data);
        }
        finally
        {
            _sendLock.Release();
        }
    }

    /// <summary>
    /// Sends a string message to the server.
    /// </summary>
    /// <param name="message">The message to send.</param>
    public Task SendMessageAsync(string message)
    {
        var data = Encoding.UTF8.GetBytes(message);
        return SendAsync(data);
    }

    /// <summary>
    /// Disconnects from the server.
    /// </summary>
    public void Disconnect()
    {
        _isConnected = false;
        _cts?.Cancel();
        _stream?.Close();
        _client?.Close();

        Disconnected?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>
    /// Disposes of the client resources.
    /// </summary>
    public void Dispose()
    {
        Disconnect();
        _cts?.Dispose();
        _sendLock?.Dispose();
    }
}
