using System.Collections.Concurrent;
using System.Net.Http.Json;
using System.Text.Json;
using CounterStrikeSharp.API;

namespace Clutchboard.Services;

public sealed class ApiClient : IDisposable
{
    private readonly HttpClient _http;
    private readonly ConcurrentQueue<object> _queue = new();
    private readonly Timer _timer;
    private readonly JsonSerializerOptions _json = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
    };
    private bool _disposed;

    public ApiClient(string baseUrl, string apiSecret)
    {
        _http = new HttpClient { BaseAddress = new Uri(baseUrl) };
        if (!string.IsNullOrEmpty(apiSecret))
            _http.DefaultRequestHeaders.Add("X-Api-Secret", apiSecret);

        _timer = new Timer(Flush, null, TimeSpan.FromMilliseconds(500), TimeSpan.FromMilliseconds(500));
    }

    /// <summary>Enqueue an event DTO to be flushed in the next batch.</summary>
    public void EnqueueEvent(object dto) => _queue.Enqueue(dto);

    private void Flush(object? _)
    {
        if (_queue.IsEmpty) return;
        var batch = new List<object>();
        while (_queue.TryDequeue(out var item))
            batch.Add(item);
        if (batch.Count > 0)
            _ = PostBatchAsync(batch);
    }

    private async Task PostBatchAsync(List<object> batch)
    {
        try
        {
            var response = await _http.PostAsJsonAsync("/events", batch, _json);
            if (!response.IsSuccessStatusCode)
                Server.PrintToConsole($"[Clutchboard] API error {(int)response.StatusCode}");
        }
        catch (Exception ex)
        {
            Server.PrintToConsole($"[Clutchboard] Failed to send events: {ex.Message}");
        }
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _timer.Dispose();
        // Best-effort flush on unload
        Flush(null);
        _http.Dispose();
    }
}
