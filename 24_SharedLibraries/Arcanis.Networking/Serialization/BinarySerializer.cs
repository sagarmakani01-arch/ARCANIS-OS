using System.Runtime.InteropServices;
using System.Text;

namespace Arcanis.Networking.Serialization;

/// <summary>
/// High-performance binary serializer for converting objects to/from byte arrays.
/// Uses unsafe code and memory spans for maximum performance.
/// </summary>
public static class BinarySerializer
{
    /// <summary>
    /// Serializes a primitive type to bytes.
    /// </summary>
    /// <typeparam name="T">The primitive type to serialize.</typeparam>
    /// <param name="value">The value to serialize.</param>
    /// <returns>The serialized bytes.</returns>
    public static byte[] Serialize<T>(T value) where T : struct
    {
        var size = Marshal.SizeOf<T>();
        var bytes = new byte[size];
        var handle = GCHandle.Alloc(bytes, GCHandleType.Pinned);
        try
        {
            Marshal.StructureToPtr(value, handle.AddrOfPinnedObject(), false);
        }
        finally
        {
            handle.Free();
        }
        return bytes;
    }

    /// <summary>
    /// Deserializes bytes to a primitive type.
    /// </summary>
    /// <typeparam name="T">The type to deserialize to.</typeparam>
    /// <param name="bytes">The bytes to deserialize.</param>
    /// <returns>The deserialized value.</returns>
    public static T Deserialize<T>(byte[] bytes) where T : struct
    {
        var handle = GCHandle.Alloc(bytes, GCHandleType.Pinned);
        try
        {
            return Marshal.PtrToStructure<T>(handle.AddrOfPinnedObject());
        }
        finally
        {
            handle.Free();
        }
    }

    /// <summary>
    /// Serializes a string with length prefix.
    /// </summary>
    /// <param name="value">The string to serialize.</param>
    /// <returns>The serialized bytes.</returns>
    public static byte[] SerializeString(string value)
    {
        var bytes = Encoding.UTF8.GetBytes(value);
        var lengthBytes = BitConverter.GetBytes(bytes.Length);

        var result = new byte[lengthBytes.Length + bytes.Length];
        Buffer.BlockCopy(lengthBytes, 0, result, 0, lengthBytes.Length);
        Buffer.BlockCopy(bytes, 0, result, lengthBytes.Length, bytes.Length);

        return result;
    }

    /// <summary>
    /// Deserializes a length-prefixed string from bytes.
    /// </summary>
    /// <param name="bytes">The bytes to deserialize.</param>
    /// <param name="offset">The offset to start reading from.</param>
    /// <returns>The deserialized string and number of bytes consumed.</returns>
    public static (string value, int bytesConsumed) DeserializeString(byte[] bytes, int offset = 0)
    {
        if (bytes.Length < offset + 4)
            throw new ArgumentException("Not enough bytes to read string length.");

        var length = BitConverter.ToInt32(bytes, offset);
        var value = Encoding.UTF8.GetString(bytes, offset + 4, length);

        return (value, 4 + length);
    }

    /// <summary>
    /// Serializes an array of bytes with length prefix.
    /// </summary>
    /// <param name="data">The data to serialize.</param>
    /// <returns>The serialized bytes with length prefix.</returns>
    public static byte[] SerializeBytes(byte[] data)
    {
        var lengthBytes = BitConverter.GetBytes(data.Length);
        var result = new byte[lengthBytes.Length + data.Length];
        Buffer.BlockCopy(lengthBytes, 0, result, 0, lengthBytes.Length);
        Buffer.BlockCopy(data, 0, result, lengthBytes.Length, data.Length);
        return result;
    }

    /// <summary>
    /// Deserializes a length-prefixed byte array.
    /// </summary>
    /// <param name="bytes">The bytes to deserialize.</param>
    /// <param name="offset">The offset to start reading from.</param>
    /// <returns>The deserialized data and number of bytes consumed.</returns>
    public static (byte[] data, int bytesConsumed) DeserializeBytes(byte[] bytes, int offset = 0)
    {
        if (bytes.Length < offset + 4)
            throw new ArgumentException("Not enough bytes to read data length.");

        var length = BitConverter.ToInt32(bytes, offset);
        var data = new byte[length];
        Buffer.BlockCopy(bytes, offset + 4, data, 0, length);

        return (data, 4 + length);
    }

    /// <summary>
    /// Serializes multiple objects into a single byte array.
    /// </summary>
    /// <param name="objects">The objects to serialize.</param>
    /// <returns>The serialized bytes.</returns>
    public static byte[] SerializeMultiple(params byte[][] objects)
    {
        using var stream = new MemoryStream();
        foreach (var obj in objects)
        {
            var lengthBytes = BitConverter.GetBytes(obj.Length);
            stream.Write(lengthBytes, 0, lengthBytes.Length);
            stream.Write(obj, 0, obj.Length);
        }
        return stream.ToArray();
    }

    /// <summary>
    /// Converts a struct to a byte array using unsafe pointer operations for maximum performance.
    /// </summary>
    /// <typeparam name="T">The struct type.</typeparam>
    /// <param name="value">The value to convert.</param>
    /// <returns>The byte array representation.</returns>
    public static unsafe byte[] StructToBytes<T>(T value) where T : struct
    {
        var size = sizeof(T);
        var bytes = new byte[size];
        fixed (byte* ptr = bytes)
        {
            *(T*)ptr = value;
        }
        return bytes;
    }

    /// <summary>
    /// Converts a byte array to a struct using unsafe pointer operations for maximum performance.
    /// </summary>
    /// <typeparam name="T">The struct type.</typeparam>
    /// <param name="bytes">The byte array to convert.</param>
    /// <returns>The struct value.</returns>
    public static unsafe T BytesToStruct<T>(byte[] bytes) where T : struct
    {
        fixed (byte* ptr = bytes)
        {
            return *(T*)ptr;
        }
    }
}
