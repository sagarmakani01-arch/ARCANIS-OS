using System.Security.Cryptography;
using System.Text;

namespace Arcanis.Security.Cryptography;

/// <summary>
/// High-performance AES encryption/decryption utilities.
/// Supports AES-256-CBC and AES-256-GCM modes.
/// </summary>
public static class AesEncryption
{
    /// <summary>
    /// Generates a cryptographically secure random key.
    /// </summary>
    /// <param name="keySize">Key size in bits (128, 192, or 256).</param>
    /// <returns>The generated key as a byte array.</returns>
    public static byte[] GenerateKey(int keySize = 256)
    {
        using var aes = Aes.Create();
        aes.KeySize = keySize;
        aes.GenerateKey();
        return aes.Key;
    }

    /// <summary>
    /// Generates a cryptographically secure random initialization vector.
    /// </summary>
    /// <returns>The generated IV as a byte array.</returns>
    public static byte[] GenerateIV()
    {
        using var aes = Aes.Create();
        aes.GenerateIV();
        return aes.IV;
    }

    /// <summary>
    /// Generates a random salt for key derivation.
    /// </summary>
    /// <param name="size">Salt size in bytes.</param>
    /// <returns>The generated salt.</returns>
    public static byte[] GenerateSalt(int size = 16)
    {
        var salt = new byte[size];
        using var rng = RandomNumberGenerator.Create();
        rng.GetBytes(salt);
        return salt;
    }

    /// <summary>
    /// Derives a cryptographic key from a password using PBKDF2.
    /// </summary>
    /// <param name="password">The password.</param>
    /// <param name="salt">The salt.</param>
    /// <param name="iterations">Number of iterations.</param>
    /// <param name="keySize">Desired key size in bits.</param>
    /// <returns>The derived key.</returns>
    public static byte[] DeriveKey(string password, byte[] salt, int iterations = 100000, int keySize = 256)
    {
        using var deriveBytes = new Rfc2898DeriveBytes(
            password,
            salt,
            iterations,
            HashAlgorithmName.SHA256);

        return deriveBytes.GetBytes(keySize / 8);
    }

    /// <summary>
    /// Encrypts data using AES-CBC mode.
    /// </summary>
    /// <param name="plainText">The plaintext to encrypt.</param>
    /// <param name="key">The encryption key.</param>
    /// <param name="iv">The initialization vector.</param>
    /// <returns>The encrypted bytes.</returns>
    public static byte[] EncryptAesCbc(byte[] plainText, byte[] key, byte[] iv)
    {
        using var aes = Aes.Create();
        aes.Key = key;
        aes.IV = iv;
        aes.Mode = CipherMode.CBC;
        aes.Padding = PaddingMode.PKCS7;

        using var encryptor = aes.CreateEncryptor();
        using var ms = new MemoryStream();
        using (var cs = new CryptoStream(ms, encryptor, CryptoStreamMode.Write))
        {
            cs.Write(plainText, 0, plainText.Length);
        }
        return ms.ToArray();
    }

    /// <summary>
    /// Decrypts data using AES-CBC mode.
    /// </summary>
    /// <param name="cipherText">The encrypted data.</param>
    /// <param name="key">The encryption key.</param>
    /// <param name="iv">The initialization vector.</param>
    /// <returns>The decrypted bytes.</returns>
    public static byte[] DecryptAesCbc(byte[] cipherText, byte[] key, byte[] iv)
    {
        using var aes = Aes.Create();
        aes.Key = key;
        aes.IV = iv;
        aes.Mode = CipherMode.CBC;
        aes.Padding = PaddingMode.PKCS7;

        using var decryptor = aes.CreateDecryptor();
        using var ms = new MemoryStream(cipherText);
        using var cs = new CryptoStream(ms, decryptor, CryptoStreamMode.Read);
        using var result = new MemoryStream();
        cs.CopyTo(result);
        return result.ToArray();
    }

    /// <summary>
    /// Encrypts a string using AES-CBC.
    /// </summary>
    /// <param name="plainText">The plaintext string.</param>
    /// <param name="key">The encryption key.</param>
    /// <param name="iv">The initialization vector.</param>
    /// <returns>The encrypted string (Base64).</returns>
    public static string EncryptStringAesCbc(string plainText, byte[] key, byte[] iv)
    {
        var plainBytes = Encoding.UTF8.GetBytes(plainText);
        var encryptedBytes = EncryptAesCbc(plainBytes, key, iv);
        return Convert.ToBase64String(encryptedBytes);
    }

    /// <summary>
    /// Decrypts a string using AES-CBC.
    /// </summary>
    /// <param name="cipherText">The encrypted string (Base64).</param>
    /// <param name="key">The encryption key.</param>
    /// <param name="iv">The initialization vector.</param>
    /// <returns>The decrypted string.</returns>
    public static string DecryptStringAesCbc(string cipherText, byte[] key, byte[] iv)
    {
        var cipherBytes = Convert.FromBase64String(cipherText);
        var decryptedBytes = DecryptAesCbc(cipherBytes, key, iv);
        return Encoding.UTF8.GetString(decryptedBytes);
    }

    /// <summary>
    /// Encrypts data using AES-GCM mode (authenticated encryption).
    /// </summary>
    /// <param name="plainText">The plaintext to encrypt.</param>
    /// <param name="key">The encryption key (128, 192, or 256 bits).</param>
    /// <param name="nonce">The nonce (12 bytes recommended for GCM).</param>
    /// <param name="tag">The authentication tag (16 bytes).</param>
    /// <returns>The encrypted bytes.</returns>
    public static byte[] EncryptAesGcm(byte[] plainText, byte[] key, byte[] nonce, out byte[] tag)
    {
        tag = new byte[16]; // GCM tag size
        var cipherText = new byte[plainText.Length];

        using var aes = new AesGcm(key, 16);
        aes.Encrypt(nonce, plainText, cipherText, tag);

        return cipherText;
    }

    /// <summary>
    /// Decrypts data using AES-GCM mode (authenticated encryption).
    /// </summary>
    /// <param name="cipherText">The encrypted data.</param>
    /// <param name="key">The encryption key.</param>
    /// <param name="nonce">The nonce.</param>
    /// <param name="tag">The authentication tag.</param>
    /// <returns>The decrypted bytes.</returns>
    public static byte[] DecryptAesGcm(byte[] cipherText, byte[] key, byte[] nonce, byte[] tag)
    {
        var plainText = new byte[cipherText.Length];

        using var aes = new AesGcm(key, 16);
        aes.Decrypt(nonce, cipherText, tag, plainText);

        return plainText;
    }

    /// <summary>
    /// Performs AES-CBC encryption with automatic IV generation.
    /// Returns IV + cipherText concatenated.
    /// </summary>
    /// <param name="plainText">The plaintext to encrypt.</param>
    /// <param name="key">The encryption key.</param>
    /// <returns>IV + cipherText as a single byte array.</returns>
    public static byte[] EncryptAesCbcAutoIV(byte[] plainText, byte[] key)
    {
        var iv = GenerateIV();
        var cipherText = EncryptAesCbc(plainText, key, iv);

        var result = new byte[iv.Length + cipherText.Length];
        Buffer.BlockCopy(iv, 0, result, 0, iv.Length);
        Buffer.BlockCopy(cipherText, 0, result, iv.Length, cipherText.Length);

        return result;
    }

    /// <summary>
    /// Decrypts data that was encrypted with automatic IV generation.
    /// </summary>
    /// <param name="data">The IV + cipherText data.</param>
    /// <param name="key">The encryption key.</param>
    /// <returns>The decrypted bytes.</returns>
    public static byte[] DecryptAesCbcAutoIV(byte[] data, byte[] key)
    {
        var iv = new byte[16]; // AES block size
        var cipherText = new byte[data.Length - iv.Length];

        Buffer.BlockCopy(data, 0, iv, 0, iv.Length);
        Buffer.BlockCopy(data, iv.Length, cipherText, 0, cipherText.Length);

        return DecryptAesCbc(cipherText, key, iv);
    }
}
