namespace Arcanis.DataStructures.Collections;

/// <summary>
/// A high-performance object pool that reduces garbage collection pressure by reusing objects.
/// Thread-safe implementation using lock-free operations where possible.
/// </summary>
/// <typeparam name="T">The type of objects in the pool.</typeparam>
public sealed class ObjectPool<T> where T : class
{
    private readonly Stack<T> _pool;
    private readonly Func<T> _factory;
    private readonly Action<T>? _reset;
    private readonly int _maxSize;
    private int _count;

    /// <summary>
    /// Initializes a new instance of the ObjectPool class.
    /// </summary>
    /// <param name="factory">Factory function to create new objects when pool is empty.</param>
    /// <param name="reset">Optional reset function to clean objects before returning to pool.</param>
    /// <param name="initialSize">Initial number of objects to create in the pool.</param>
    /// <param name="maxSize">Maximum number of objects the pool can hold.</param>
    public ObjectPool(Func<T> factory, Action<T>? reset = null, int initialSize = 16, int maxSize = 1024)
    {
        _factory = factory ?? throw new ArgumentNullException(nameof(factory));
        _reset = reset;
        _maxSize = maxSize;
        _pool = new Stack<T>(initialSize);

        for (int i = 0; i < initialSize; i++)
        {
            _pool.Push(_factory());
            _count++;
        }
    }

    /// <summary>
    /// Gets the number of available objects in the pool.
    /// </summary>
    public int AvailableCount
    {
        get { lock (_pool) return _count; }
    }

    /// <summary>
    /// Rents an object from the pool. Creates a new one if pool is empty.
    /// </summary>
    /// <returns>A pooled object instance.</returns>
    public T Rent()
    {
        lock (_pool)
        {
            if (_pool.Count > 0)
            {
                _count--;
                return _pool.Pop();
            }
        }

        return _factory();
    }

    /// <summary>
    /// Returns an object to the pool for reuse.
    /// </summary>
    /// <param name="item">The object to return to the pool.</param>
    public void Return(T item)
    {
        if (item == null) throw new ArgumentNullException(nameof(item));

        _reset?.Invoke(item);

        lock (_pool)
        {
            if (_count < _maxSize)
            {
                _pool.Push(item);
                _count++;
            }
        }
    }

    /// <summary>
    /// Clears all objects from the pool.
    /// </summary>
    public void Clear()
    {
        lock (_pool)
        {
            _pool.Clear();
            _count = 0;
        }
    }
}
