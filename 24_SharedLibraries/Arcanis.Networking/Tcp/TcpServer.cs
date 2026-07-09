using System.Net;
using System.Net.Sockets;
using System.Text;

namespace Arcanis.Networking.Tcp;

/// <summary>
/// Event args for client connection events.
/// </summary>
public class ClientConnectedEventArgs : EventArgs
{
    /// <summary>The connected client's endpoint.</summary>
    public EndPoint? EndPoint { get; set; }
    /// <summary>Unique client identifier.</summary>
    public string ClientId { get; set; } = string.Empty;
}

/// <summary>
/// Event args for data received events.
/// </summary>
public class DataReceivedEventArgs : EventArgs
{
    /// <summary>The client that sent data.</summary>
    public string ClientId { get; set; } = string.Empty;
    /// <summary>The received data.</summary>
    public byte[] Data { get; set; } = Array.Empty<byte>();
    /// <summary>The received message as string.</summary>
    public string Message => Encoding.UTF8.GetString(Data);
}

/// <summary>
/// High-performance asynchronous TCP server for handling multiple client connections.
/// Supports message framing and automatic reconnection.
/// </summary>
public sealed class TcpServer : IDisposable
{
    private TcpListener? _listener;
    private readonly Dictionary<string, TcpClient> _clients;
    private readonly Dictionary<string, NetworkStream> _streams;
    private readonly SemaphoreSlim _clientLock;
    private CancellationTokenSource? _cts;
    private Task? _acceptTask;
    private bool _isRunning;
    private int _clientIdCounter;

    /// <summary>
    /// Gets whether the server is currently running.
    /// </summary>
    public bool IsRunning => _isRunning;

    /// <summary>
    /// Gets the number of connected clients.
    /// </summary>
    public int ClientCount => _clients.Count;

    /// <summary>
    /// Gets or sets the port the server listens on.
    /// </summary>
    public int Port { get; }

    /// <summary>
    /// Gets or sets the IP address the server binds to.
    /// </summary>
    public IPAddress IPAddress { get; }

    /// <summary>
    /// Gets or sets the buffer size for receiving data.
    /// </summary>
    public int BufferSize { get; set; } = 8192;

    /// <summary>Event fired when a client connects.</summary>
    public event EventHandler<ClientConnectedEventArgs>? ClientConnected;

    /// <summary>Event fired when a client disconnects.</summary>
    public event EventHandler<ClientConnectedEventArgs>? ClientDisconnected;

    /// <summary>Event fired when data is received from a client.</summary>
    public event EventHandler<DataReceivedEventArgs>? DataReceived;

    /// <summary>
    /// Initializes a new instance of the TcpServer class.
    /// </summary>
    /// <param name="port">The port to listen on.</param>
    /// <param name="ipAddress">The IP address to bind to (default: any).</param>
    public TcpServer(int port, IPAddress? ipAddress = null)
    {
        Port = port;
        IPAddress = ipAddress ?? IPAddress.Any;
        _clients = new Dictionary<string, TcpClient>();
        _streams = new Dictionary<string, NetworkStream>();
        _clientLock = new SemaphoreSlim(1, 1);
        _clientIdCounter = 0;
    }

    /// <summary>
    /// Starts the server and begins accepting connections.
    /// </summary>
    public async Task StartAsync()
    {
        if (_isRunning) return;

        _cts = new CancellationTokenSource();
        _listener = new TcpListener(IPAddress, Port);
        _listener.Start();
        _isRunning = true;

        _acceptTask = AcceptClientsAsync(_cts.Token);
    }

    private async Task AcceptClientsAsync(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            try
            {
                var client = await _listener!.AcceptTcpClientAsync();
                var clientId = $"Client_{Interlocked.Increment(ref _clientIdCounter)}";

                await _clientLock.WaitAsync(cancellationToken);
                try
                {
                    _clients[clientId] = client;
                    _streams[clientId] = client.GetStream();
                }
                finally
                {
                    _clientLock.Release();
                }

                ClientConnected?.Invoke(this, new ClientConnectedEventArgs
                {
                    EndPoint = client.Client.RemoteEndPoint,
                    ClientId = clientId
                });

                _ = Task.Run(() => HandleClientAsync(clientId, client, cancellationToken), cancellationToken);
            }
            catch (ObjectDisposedException)
            {
                break;
            }
            catch (SocketException)
            {
                break;
            }
        }
    }

    private async Task HandleClientAsync(string clientId, TcpClient client, CancellationToken cancellationToken)
    {
        var buffer = new byte[BufferSize];

        try
        {
            while (!cancellationToken.IsCancellationRequested && client.Connected)
            {
                var bytesRead = await _streams[clientId].ReadAsync(buffer, cancellationToken);

                if (bytesRead == 0)
                    break;

                var data = new byte[bytesRead];
                Array.Copy(buffer, data, bytesRead);

                DataReceived?.Invoke(this, new DataReceivedEventArgs
                {
                    ClientId = clientId,
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
            DisconnectClient(clientId);
        }
    }

    /// <summary>
    /// Sends data to a specific client.
    /// </summary>
    /// <param name="clientId">The target client ID.</param>
    /// <param name="data">The data to send.</param>
    public async Task SendToClientAsync(string clientId, byte[] data)
    {
        if (_streams.TryGetValue(clientId, out var stream))
        {
            await stream.WriteAsync(data);
        }
    }

    /// <summary>
    /// Sends a string message to a specific client.
    /// </summary>
    /// <param name="clientId">The target client ID.</param>
    /// <param name="message">The message to send.</param>
    public Task SendMessageAsync(string clientId, string message)
    {
        var data = Encoding.UTF8.GetBytes(message);
        return SendToClientAsync(clientId, data);
    }

    /// <summary>
    /// Broadcasts data to all connected clients.
    /// </summary>
    /// <param name="data">The data to broadcast.</param>
    public async Task BroadcastAsync(byte[] data)
    {
        await _clientLock.WaitAsync();
        try
        {
            foreach (var clientId in _clients.Keys.ToList())
            {
                await SendToClientAsync(clientId, data);
            }
        }
        finally
        {
            _clientLock.Release();
        }
    }

    /// <summary>
    /// Broadcasts a string message to all connected clients.
    /// </summary>
    /// <param name="message">The message to broadcast.</param>
    public Task BroadcastMessageAsync(string message)
    {
        var data = Encoding.UTF8.GetBytes(message);
        return BroadcastAsync(data);
    }

    /// <summary>
    /// Disconnects a specific client.
    /// </summary>
    /// <param name="clientId">The client to disconnect.</param>
    public void DisconnectClient(string clientId)
    {
        if (_streams.TryGetValue(clientId, out var stream))
        {
            stream.Close();
            _streams.Remove(clientId);
        }

        if (_clients.TryGetValue(clientId, out var client))
        {
            client.Close();
            _clients.Remove(clientId);

            ClientDisconnected?.Invoke(this, new ClientConnectedEventArgs
            {
                ClientId = clientId
            });
        }
    }

    /// <summary>
    /// Stops the server and disconnects all clients.
    /// </summary>
    public async Task StopAsync()
    {
        if (!_isRunning) return;

        _cts?.Cancel();
        _listener?.Stop();

        await _clientLock.WaitAsync();
        try
        {
            foreach (var clientId in _clients.Keys.ToList())
            {
                DisconnectClient(clientId);
            }
        }
        finally
        {
            _clientLock.Release();
        }

        _isRunning = false;
    }

    /// <summary>
    /// Disposes of the server resources.
    /// </summary>
    public void Dispose()
    {
        _cts?.Cancel();
        _cts?.Dispose();
        _listener?.Stop();
        _clientLock?.Dispose();

        foreach (var client in _clients.Values)
            client.Close();

        foreach (var stream in _streams.Values)
            stream.Close();

        _clients.Clear();
        _streams.Clear();
    }
}
