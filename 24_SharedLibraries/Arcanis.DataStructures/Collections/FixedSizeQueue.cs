namespace Arcanis.DataStructures.Collections;

/// <summary>
/// A fixed-size circular queue that overwrites old elements when capacity is reached.
/// Optimized for high-throughput scenarios with minimal allocations.
/// </summary>
/// <typeparam name="T">The type of elements in the queue.</typeparam>
public sealed class FixedSizeQueue<T>
{
    private readonly T[] _buffer;
    private int _head;
    private int _tail;
    private int _count;

    /// <summary>
    /// Initializes a new instance of the FixedSizeQueue class.
    /// </summary>
    /// <param name="capacity">Maximum number of elements the queue can hold.</param>
    public FixedSizeQueue(int capacity)
    {
        if (capacity <= 0)
            throw new ArgumentOutOfRangeException(nameof(capacity), "Capacity must be positive.");

        _buffer = new T[capacity];
        _head = 0;
        _tail = 0;
        _count = 0;
    }

    /// <summary>
    /// Gets the maximum capacity of the queue.
    /// </summary>
    public int Capacity => _buffer.Length;

    /// <summary>
    /// Gets the current number of elements in the queue.
    /// </summary>
    public int Count => _count;

    /// <summary>
    /// Gets whether the queue is full.
    /// </summary>
    public bool IsFull => _count == _buffer.Length;

    /// <summary>
    /// Gets whether the queue is empty.
    /// </summary>
    public bool IsEmpty => _count == 0;

    /// <summary>
    /// Gets the element at the front of the queue without removing it.
    /// </summary>
    public T Peek => _count > 0 ? _buffer[_head] : throw new InvalidOperationException("Queue is empty.");

    /// <summary>
    /// Enqueues an item. If the queue is full, overwrites the oldest element.
    /// </summary>
    /// <param name="item">The item to add to the queue.</param>
    /// <returns>True if an element was overwritten; otherwise, false.</returns>
    public bool Enqueue(T item)
    {
        bool overwritten = false;

        if (_count == _buffer.Length)
        {
            overwritten = true;
            _head = (_head + 1) % _buffer.Length;
        }
        else
        {
            _count++;
        }

        _buffer[_tail] = item;
        _tail = (_tail + 1) % _buffer.Length;

        return overwritten;
    }

    /// <summary>
    /// Dequeues an item from the front of the queue.
    /// </summary>
    /// <returns>The removed item.</returns>
    public T Dequeue()
    {
        if (_count == 0)
            throw new InvalidOperationException("Queue is empty.");

        T item = _buffer[_head];
        _buffer[_head] = default!;
        _head = (_head + 1) % _buffer.Length;
        _count--;

        return item;
    }

    /// <summary>
    /// Clears all elements from the queue.
    /// </summary>
    public void Clear()
    {
        Array.Clear(_buffer, 0, _buffer.Length);
        _head = 0;
        _tail = 0;
        _count = 0;
    }

    /// <summary>
    /// Copies elements to an array.
    /// </summary>
    /// <returns>An array containing all elements in the queue.</returns>
    public T[] ToArray()
    {
        var result = new T[_count];
        for (int i = 0; i < _count; i++)
        {
            result[i] = _buffer[(_head + i) % _buffer.Length];
        }
        return result;
    }
}
