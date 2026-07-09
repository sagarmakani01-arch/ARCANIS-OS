using System.Net.Http;
using System.Text;
using System.Text.Json;

namespace Arcanis.Networking.Http;

/// <summary>
/// HTTP response wrapper with status code, headers, and content.
/// </summary>
public class HttpResponse
{
    /// <summary>Gets or sets the HTTP status code.</summary>
    public int StatusCode { get; set; }
    /// <summary>Gets or sets the response headers.</summary>
    public Dictionary<string, string> Headers { get; set; } = new();
    /// <summary>Gets or sets the response content as bytes.</summary>
    public byte[] Content { get; set; } = Array.Empty<byte>();
    /// <summary>Gets whether the request was successful.</summary>
    public bool IsSuccessStatusCode => StatusCode >= 200 && StatusCode < 300;
    /// <summary>Gets the response content as a string.</summary>
    public string ContentAsString => Encoding.UTF8.GetString(Content);
}

/// <summary>
/// High-performance HTTP client wrapper with JSON serialization support.
/// Provides simplified API for common HTTP operations.
/// </summary>
public sealed class ArcanisHttpClient : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly bool _ownsClient;

    /// <summary>
    /// Gets or sets the default timeout for requests.
    /// </summary>
    public TimeSpan Timeout
    {
        get => _httpClient.Timeout;
        set => _httpClient.Timeout = value;
    }

    /// <summary>
    /// Gets the underlying HttpClient instance.
    /// </summary>
    public HttpClient Client => _httpClient;

    /// <summary>
    /// Initializes a new instance of the ArcanisHttpClient class.
    /// </summary>
    /// <param name="baseUrl">Optional base URL for all requests.</param>
    public ArcanisHttpClient(string? baseUrl = null)
    {
        _httpClient = new HttpClient();
        _ownsClient = true;

        if (!string.IsNullOrEmpty(baseUrl))
        {
            _httpClient.BaseAddress = new Uri(baseUrl);
        }
    }

    /// <summary>
    /// Initializes a new instance with an existing HttpClient.
    /// </summary>
    /// <param name="httpClient">The existing HttpClient to use.</param>
    public ArcanisHttpClient(HttpClient httpClient)
    {
        _httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));
        _ownsClient = false;
    }

    /// <summary>
    /// Sends a GET request.
    /// </summary>
    /// <param name="url">The request URL.</param>
    /// <returns>The HTTP response.</returns>
    public async Task<HttpResponse> GetAsync(string url)
    {
        var response = await _httpClient.GetAsync(url);
        return await CreateResponseAsync(response);
    }

    /// <summary>
    /// Sends a GET request and deserializes the response.
    /// </summary>
    /// <typeparam name="T">The type to deserialize to.</typeparam>
    /// <param name="url">The request URL.</param>
    /// <returns>The deserialized response.</returns>
    public async Task<T?> GetAsync<T>(string url)
    {
        var response = await _httpClient.GetAsync(url);
        var content = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<T>(content);
    }

    /// <summary>
    /// Sends a POST request with JSON content.
    /// </summary>
    /// <param name="url">The request URL.</param>
    /// <param name="data">The data to serialize and send.</param>
    /// <returns>The HTTP response.</returns>
    public async Task<HttpResponse> PostAsync<T>(string url, T data)
    {
        var json = JsonSerializer.Serialize(data);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        var response = await _httpClient.PostAsync(url, content);
        return await CreateResponseAsync(response);
    }

    /// <summary>
    /// Sends a POST request and deserializes the response.
    /// </summary>
    /// <typeparam name="TResponse">The type to deserialize the response to.</typeparam>
    /// <param name="url">The request URL.</param>
    /// <param name="data">The data to serialize and send.</param>
    /// <returns>The deserialized response.</returns>
    public async Task<TResponse?> PostAsync<TRequest, TResponse>(string url, TRequest data)
    {
        var json = JsonSerializer.Serialize(data);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        var response = await _httpClient.PostAsync(url, content);
        var responseContent = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<TResponse>(responseContent);
    }

    /// <summary>
    /// Sends a PUT request with JSON content.
    /// </summary>
    /// <param name="url">The request URL.</param>
    /// <param name="data">The data to serialize and send.</param>
    /// <returns>The HTTP response.</returns>
    public async Task<HttpResponse> PutAsync<T>(string url, T data)
    {
        var json = JsonSerializer.Serialize(data);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        var response = await _httpClient.PutAsync(url, content);
        return await CreateResponseAsync(response);
    }

    /// <summary>
    /// Sends a DELETE request.
    /// </summary>
    /// <param name="url">The request URL.</param>
    /// <returns>The HTTP response.</returns>
    public async Task<HttpResponse> DeleteAsync(string url)
    {
        var response = await _httpClient.DeleteAsync(url);
        return await CreateResponseAsync(response);
    }

    private async Task<HttpResponse> CreateResponseAsync(HttpResponseMessage response)
    {
        var httpResponse = new HttpResponse
        {
            StatusCode = (int)response.StatusCode
        };

        foreach (var header in response.Headers)
        {
            httpResponse.Headers[string.Join(",", header.Key)] = string.Join(",", header.Value);
        }

        httpResponse.Content = await response.Content.ReadAsByteArrayAsync();

        return httpResponse;
    }

    /// <summary>
    /// Disposes of the HTTP client.
    /// </summary>
    public void Dispose()
    {
        if (_ownsClient)
        {
            _httpClient?.Dispose();
        }
    }
}
