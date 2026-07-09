using System.Net;
using System.Net.Sockets;
using System.Text;

namespace Arcanis.Networking.Udp;

/// <summary>
/// Event args for UDP data received events.
/// </summary>
public class UdpDataReceivedEventArgs : EventArgs
{
    /// <summary>The sender's endpoint.</summary>
    public EndPoint? SenderEndPoint { get; set; }
    /// <summary>The received data.</summary>
    public byte[] Data { get; set; } = Array.Empty<byte>();
    /// <summary>The received message as string.</summary>
    public string Message => Encoding.UTF8.GetString(Data);
}

/// <summary>
/// High-performance asynchronous UDP server for connectionless communication.
/// Ideal for game servers, real-time applications, and broadcasting.
/// </summary>
public sealed class UdpServer : IDisposable
{
    private UdpClient? _udpClient;
    private CancellationTokenSource? _cts;
    private Task? _receiveTask;
    private bool _isRunning;

    /// <summary>
    /// Gets whether the server is currently running.
    /// </summary>
    public bool IsRunning => _isRunning;

    /// <summary>
    /// Gets or sets the port the server listens on.
    /// </summary>
    public int Port { get; }

    /// <summary>
    /// Gets or sets the IP address the server binds to.
    /// </summary>
    public IPAddress IPAddress { get; }

    /// <summary>
    /// Gets or sets the receive buffer size.
    /// </summary>
    public int BufferSize { get; set; } = 65507; // Max UDP packet size

    /// <summary>Event fired when data is received.</summary>
    public event EventHandler<UdpDataReceivedEventArgs>? DataReceived;

    /// <summary>Event fired when an error occurs.</summary>
    public event EventHandler<Exception>? ErrorOccurred;

    /// <summary>
    /// Initializes a new instance of the UdpServer class.
    /// </summary>
    /// <param name="port">The port to listen on.</param>
    /// <param name="ipAddress">The IP address to bind to (default: any).</param>
    public UdpServer(int port, IPAddress? ipAddress = null)
    {
        Port = port;
        IPAddress = ipAddress ?? IPAddress.Any;
    }

    /// <summary>
    /// Starts the server and begins receiving data.
    /// </summary>
    public async Task StartAsync()
    {
        if (_isRunning) return;

        _cts = new CancellationTokenSource();
        _udpClient = new UdpClient(new IPEndPoint(IPAddress, Port));
        _isRunning = true;

        _receiveTask = Task.Run(() => ReceiveAsync(_cts.Token));
    }

    private async Task ReceiveAsync(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested && _isRunning)
        {
            try
            {
                var result = await _udpClient!.ReceiveAsync();

                DataReceived?.Invoke(this, new UdpDataReceivedEventArgs
                {
                    SenderEndPoint = result.RemoteEndPoint,
                    Data = result.Buffer
                });
            }
            catch (ObjectDisposedException)
            {
                break;
            }
            catch (SocketException ex)
            {
                ErrorOccurred?.Invoke(this, ex);
                break;
            }
            catch (Exception ex)
            {
                ErrorOccurred?.Invoke(this, ex);
            }
        }
    }

    /// <summary>
    /// Sends data to a specific endpoint.
    /// </summary>
    /// <param name="data">The data to send.</param>
    /// <param name="endpoint">The target endpoint.</param>
    public async Task SendAsync(byte[] data, EndPoint endpoint)
    {
        if (!_isRunning || _udpClient == null)
            throw new InvalidOperationException("Server is not running.");

        await _udpClient.SendAsync(data, data.Length, (IPEndPoint)endpoint);
    }

    /// <summary>
    /// Sends a string message to a specific endpoint.
    /// </summary>
    /// <param name="message">The message to send.</param>
    /// <param name="endpoint">The target endpoint.</param>
    public Task SendMessageAsync(string message, EndPoint endpoint)
    {
        var data = Encoding.UTF8.GetBytes(message);
        return SendAsync(data, endpoint);
    }

    /// <summary>
    /// Broadcasts data to all clients on a specific port.
    /// </summary>
    /// <param name="data">The data to broadcast.</param>
    /// <param name="port">The broadcast port.</param>
    public async Task BroadcastAsync(byte[] data, int port)
    {
        if (!_isRunning || _udpClient == null)
            throw new InvalidOperationException("Server is not running.");

        using var broadcastClient = new UdpClient();
        broadcastClient.EnableBroadcast = true;
        var broadcastEndpoint = new IPEndPoint(IPAddress.Broadcast, port);
        await broadcastClient.SendAsync(data, data.Length, broadcastEndpoint);
    }

    /// <summary>
    /// Broadcasts a string message to all clients on a specific port.
    /// </summary>
    /// <param name="message">The message to broadcast.</param>
    /// <param name="port">The broadcast port.</param>
    public Task BroadcastMessageAsync(string message, int port)
    {
        var data = Encoding.UTF8.GetBytes(message);
        return BroadcastAsync(data, port);
    }

    /// <summary>
    /// Stops the server.
    /// </summary>
    public void Stop()
    {
        _isRunning = false;
        _cts?.Cancel();
        _udpClient?.Close();
    }

    /// <summary>
    /// Disposes of the server resources.
    /// </summary>
    public void Dispose()
    {
        Stop();
        _cts?.Dispose();
    }
}
