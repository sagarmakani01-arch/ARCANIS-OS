using System.Security.Cryptography;
using System.Text;

namespace Arcanis.Security.Cryptography;

/// <summary>
/// High-performance cryptographic hashing utilities.
/// Supports SHA-256, SHA-384, SHA-512, and HMAC variants.
/// </summary>
public static class Hashing
{
    /// <summary>
    /// Computes SHA-256 hash of a byte array.
    /// </summary>
    /// <param name="data">The data to hash.</param>
    /// <returns>The hash as a byte array.</returns>
    public static byte[] ComputeSha256(byte[] data)
    {
        return SHA256.HashData(data);
    }

    /// <summary>
    /// Computes SHA-256 hash of a string.
    /// </summary>
    /// <param name="text">The text to hash.</param>
    /// <returns>The hash as a hexadecimal string.</returns>
    public static string ComputeSha256Hex(string text)
    {
        var bytes = Encoding.UTF8.GetBytes(text);
        var hash = SHA256.HashData(bytes);
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    /// <summary>
    /// Computes SHA-384 hash of a byte array.
    /// </summary>
    /// <param name="data">The data to hash.</param>
    /// <returns>The hash as a byte array.</returns>
    public static byte[] ComputeSha384(byte[] data)
    {
        return SHA384.HashData(data);
    }

    /// <summary>
    /// Computes SHA-512 hash of a byte array.
    /// </summary>
    /// <param name="data">The data to hash.</param>
    /// <returns>The hash as a byte array.</returns>
    public static byte[] ComputeSha512(byte[] data)
    {
        return SHA512.HashData(data);
    }

    /// <summary>
    /// Computes SHA-512 hash of a string.
    /// </summary>
    /// <param name="text">The text to hash.</param>
    /// <returns>The hash as a hexadecimal string.</returns>
    public static string ComputeSha512Hex(string text)
    {
        var bytes = Encoding.UTF8.GetBytes(text);
        var hash = SHA512.HashData(bytes);
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    /// <summary>
    /// Computes HMAC-SHA256 hash.
    /// </summary>
    /// <param name="data">The data to hash.</param>
    /// <param name="key">The HMAC key.</param>
    /// <returns>The hash as a byte array.</returns>
    public static byte[] ComputeHmacSha256(byte[] data, byte[] key)
    {
        return HMACSHA256.HashData(key, data);
    }

    /// <summary>
    /// Computes HMAC-SHA256 hash and returns as hex string.
    /// </summary>
    /// <param name="data">The data to hash.</param>
    /// <param name="key">The HMAC key.</param>
    /// <returns>The hash as a hexadecimal string.</returns>
    public static string ComputeHmacSha256Hex(byte[] data, byte[] key)
    {
        var hash = HMACSHA256.HashData(key, data);
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    /// <summary>
    /// Computes HMAC-SHA512 hash.
    /// </summary>
    /// <param name="data">The data to hash.</param>
    /// <param name="key">The HMAC key.</param>
    /// <returns>The hash as a byte array.</returns>
    public static byte[] ComputeHmacSha512(byte[] data, byte[] key)
    {
        return HMACSHA512.HashData(key, data);
    }

    /// <summary>
    /// Verifies a hash against data using constant-time comparison.
    /// </summary>
    /// <param name="data">The data to verify.</param>
    /// <param name="key">The HMAC key.</param>
    /// <param name="expectedHash">The expected hash.</param>
    /// <returns>True if the hash matches; otherwise, false.</returns>
    public static bool VerifyHmacSha256(byte[] data, byte[] key, byte[] expectedHash)
    {
        var computedHash = HMACSHA256.HashData(key, data);
        return CryptographicOperations.FixedTimeEquals(computedHash, expectedHash);
    }

    /// <summary>
    /// Computes a salted hash for password storage.
    /// </summary>
    /// <param name="password">The password to hash.</param>
    /// <param name="salt">The salt (generated if null).</param>
    /// <param name="iterations">Number of PBKDF2 iterations.</param>
    /// <returns>The hash and salt.</returns>
    public static (byte[] hash, byte[] salt) ComputePasswordHash(string password, byte[]? salt = null, int iterations = 100000)
    {
        salt ??= new byte[32];
        using var rng = RandomNumberGenerator.Create();
        rng.GetBytes(salt);

        using var deriveBytes = new Rfc2898DeriveBytes(
            password,
            salt,
            iterations,
            HashAlgorithmName.SHA256);

        var hash = deriveBytes.GetBytes(32);
        return (hash, salt);
    }

    /// <summary>
    /// Verifies a password against a stored hash.
    /// </summary>
    /// <param name="password">The password to verify.</param>
    /// <param name="storedHash">The stored hash.</param>
    /// <param name="salt">The salt used during hashing.</param>
    /// <param name="iterations">Number of PBKDF2 iterations.</param>
    /// <returns>True if the password matches; otherwise, false.</returns>
    public static bool VerifyPassword(string password, byte[] storedHash, byte[] salt, int iterations = 100000)
    {
        using var deriveBytes = new Rfc2898DeriveBytes(
            password,
            salt,
            iterations,
            HashAlgorithmName.SHA256);

        var computedHash = deriveBytes.GetBytes(32);
        return CryptographicOperations.FixedTimeEquals(computedHash, storedHash);
    }

    /// <summary>
    /// Computes a fast non-cryptographic hash for general purposes.
    /// </summary>
    /// <param name="data">The data to hash.</param>
    /// <returns>The hash code.</returns>
    public static int ComputeFastHash(byte[] data)
    {
        unchecked
        {
            int hash = 17;
            foreach (byte b in data)
            {
                hash = hash * 31 + b;
            }
            return hash;
        }
    }

    /// <summary>
    /// Computes MurmurHash3 for high-performance hashing.
    /// </summary>
    /// <param name="data">The data to hash.</param>
    /// <param name="seed">The seed value.</param>
    /// <returns>The hash value.</returns>
    public static uint MurmurHash3(byte[] data, uint seed = 0)
    {
        uint h1 = seed;
        uint c1 = 0xcc9e2d51;
        uint c2 = 0x1b873593;

        int nLength = data.Length;
        int nBlocks = nLength / 4;

        for (int i = 0; i < nBlocks; i++)
        {
            int index = i * 4;
            uint k1 = (uint)(data[index] | (data[index + 1] << 8) | (data[index + 2] << 16) | (data[index + 3] << 24));

            k1 *= c1;
            k1 = (k1 << 15) | (k1 >> 17);
            k1 *= c2;

            h1 ^= k1;
            h1 = (h1 << 13) | (h1 >> 19);
            h1 = h1 * 5 + 0xe6546b64;
        }

        uint tailK1 = 0;
        int tailIndex = nBlocks * 4;

        switch (nLength & 3)
        {
            case 3:
                tailK1 ^= (uint)(data[tailIndex + 2] << 16);
                goto case 2;
            case 2:
                tailK1 ^= (uint)(data[tailIndex + 1] << 8);
                goto case 1;
            case 1:
                tailK1 ^= data[tailIndex];
                tailK1 *= c1;
                tailK1 = (tailK1 << 15) | (tailK1 >> 17);
                tailK1 *= c2;
                h1 ^= tailK1;
                break;
        }

        h1 ^= (uint)nLength;
        h1 ^= h1 >> 16;
        h1 *= 0x85ebca6b;
        h1 ^= h1 >> 13;
        h1 *= 0xc2b2ae35;
        h1 ^= h1 >> 16;

        return h1;
    }
}
