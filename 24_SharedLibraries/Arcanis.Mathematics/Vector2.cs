using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace Arcanis.Mathematics;

/// <summary>
/// A high-performance 2D vector struct with SIMD support.
/// </summary>
[StructLayout(LayoutKind.Sequential)]
public struct Vector2 : IEquatable<Vector2>, IFormattable
{
    /// <summary>The X component.</summary>
    public float X;
    /// <summary>The Y component.</summary>
    public float Y;

    /// <summary>A vector with all components set to zero.</summary>
    public static readonly Vector2 Zero = new(0, 0);
    /// <summary>A vector with all components set to one.</summary>
    public static readonly Vector2 One = new(1, 1);
    /// <summary>A unit vector pointing right.</summary>
    public static readonly Vector2 Right = new(1, 0);
    /// <summary>A unit vector pointing left.</summary>
    public static readonly Vector2 Left = new(-1, 0);
    /// <summary>A unit vector pointing up.</summary>
    public static readonly Vector2 Up = new(0, 1);
    /// <summary>A unit vector pointing down.</summary>
    public static readonly Vector2 Down = new(0, -1);

    /// <summary>
    /// Gets the magnitude (length) of the vector.
    /// </summary>
    public float Magnitude
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        get => MathF.Sqrt(X * X + Y * Y);
    }

    /// <summary>
    /// Gets the squared magnitude (faster than Magnitude for comparisons).
    /// </summary>
    public float SqrMagnitude
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        get => X * X + Y * Y;
    }

    /// <summary>
    /// Gets a normalized version of the vector.
    /// </summary>
    public Vector2 Normalized
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        get
        {
            float mag = Magnitude;
            if (mag > 1E-05f)
                return this / mag;
            return Zero;
        }
    }

    /// <summary>
    /// Initializes a new Vector2.
    /// </summary>
    /// <param name="x">The X component.</param>
    /// <param name="y">The Y component.</param>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public Vector2(float x, float y)
    {
        X = x;
        Y = y;
    }

    /// <summary>
    /// Initializes a new Vector2 with both components set to the same value.
    /// </summary>
    /// <param name="value">The value for both components.</param>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public Vector2(float value) : this(value, value) { }

    /// <summary>
    /// Calculates the dot product of two vectors.
    /// </summary>
    /// <param name="a">First vector.</param>
    /// <param name="b">Second vector.</param>
    /// <returns>The dot product.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static float Dot(Vector2 a, Vector2 b) => a.X * b.X + a.Y * b.Y;

    /// <summary>
    /// Calculates the cross product of two vectors.
    /// </summary>
    /// <param name="a">First vector.</param>
    /// <param name="b">Second vector.</param>
    /// <returns>The cross product magnitude.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static float Cross(Vector2 a, Vector2 b) => a.X * b.Y - a.Y * b.X;

    /// <summary>
    /// Calculates the distance between two vectors.
    /// </summary>
    /// <param name="a">First vector.</param>
    /// <param name="b">Second vector.</param>
    /// <returns>The distance.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static float Distance(Vector2 a, Vector2 b) => (a - b).Magnitude;

    /// <summary>
    /// Calculates the squared distance between two vectors.
    /// </summary>
    /// <param name="a">First vector.</param>
    /// <param name="b">Second vector.</param>
    /// <returns>The squared distance.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static float SqrDistance(Vector2 a, Vector2 b) => (a - b).SqrMagnitude;

    /// <summary>
    /// Linearly interpolates between two vectors.
    /// </summary>
    /// <param name="a">Start vector.</param>
    /// <param name="b">End vector.</param>
    /// <param name="t">Interpolation factor (0-1).</param>
    /// <returns>The interpolated vector.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector2 Lerp(Vector2 a, Vector2 b, float t)
    {
        t = Math.Clamp(t, 0f, 1f);
        return new Vector2(a.X + (b.X - a.X) * t, a.Y + (b.Y - a.Y) * t);
    }

    /// <summary>
    /// Clamps the vector components to the specified range.
    /// </summary>
    /// <param name="value">The vector to clamp.</param>
    /// <param name="min">Minimum component value.</param>
    /// <param name="max">Maximum component value.</param>
    /// <returns>The clamped vector.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector2 Clamp(Vector2 value, float min, float max)
    {
        return new Vector2(
            Math.Clamp(value.X, min, max),
            Math.Clamp(value.Y, min, max));
    }

    /// <summary>
    /// Returns the vector with its magnitude clamped to max length.
    /// </summary>
    /// <param name="vector">The vector to clamp.</param>
    /// <param name="maxLength">The maximum length.</param>
    /// <returns>The clamped vector.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector2 ClampMagnitude(Vector2 vector, float maxLength)
    {
        if (vector.SqrMagnitude > maxLength * maxLength)
            return vector.Normalized * maxLength;
        return vector;
    }

    /// <summary>
    /// Reflects a vector off a surface with the given normal.
    /// </summary>
    /// <param name="direction">The direction vector.</param>
    /// <param name="normal">The surface normal.</param>
    /// <returns>The reflected vector.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector2 Reflect(Vector2 direction, Vector2 normal)
    {
        return direction - 2 * Dot(direction, normal) * normal;
    }

    /// <summary>
    /// Rotates a vector by the given angle (in radians).
    /// </summary>
    /// <param name="vector">The vector to rotate.</param>
    /// <param name="radians">The rotation angle in radians.</param>
    /// <returns>The rotated vector.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector2 Rotate(Vector2 vector, float radians)
    {
        float cos = MathF.Cos(radians);
        float sin = MathF.Sin(radians);
        return new Vector2(
            vector.X * cos - vector.Y * sin,
            vector.X * sin + vector.Y * cos);
    }

    /// <summary>
    /// Converts the vector to a System.Numerics.Vector2.
    /// </summary>
    /// <returns>The System.Numerics.Vector2.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public System.Numerics.Vector2 ToNumericsVector2() => new(X, Y);

    /// <summary>
    /// Creates a Vector2 from a System.Numerics.Vector2.
    /// </summary>
    /// <param name="v">The System.Numerics.Vector2.</param>
    /// <returns>The Arcanis Vector2.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector2 FromNumericsVector2(System.Numerics.Vector2 v) => new(v.X, v.Y);

    /// <summary>Operator + for vector addition.</summary>
    public static Vector2 operator +(Vector2 a, Vector2 b) => new(a.X + b.X, a.Y + b.Y);

    /// <summary>Operator - for vector subtraction.</summary>
    public static Vector2 operator -(Vector2 a, Vector2 b) => new(a.X - b.X, a.Y - b.Y);

    /// <summary>Operator * for scalar multiplication.</summary>
    public static Vector2 operator *(Vector2 a, float scalar) => new(a.X * scalar, a.Y * scalar);

    /// <summary>Operator * for scalar multiplication.</summary>
    public static Vector2 operator *(float scalar, Vector2 a) => new(a.X * scalar, a.Y * scalar);

    /// <summary>Operator / for scalar division.</summary>
    public static Vector2 operator /(Vector2 a, float scalar) => new(a.X / scalar, a.Y / scalar);

    /// <summary>Operator - for unary negation.</summary>
    public static Vector2 operator -(Vector2 a) => new(-a.X, -a.Y);

    /// <summary>Equality operator.</summary>
    public static bool operator ==(Vector2 left, Vector2 right) => left.Equals(right);

    /// <summary>Inequality operator.</summary>
    public static bool operator !=(Vector2 left, Vector2 right) => !left.Equals(right);

    /// <summary>Implicit conversion to System.Numerics.Vector2.</summary>
    public static implicit operator System.Numerics.Vector2(Vector2 v) => v.ToNumericsVector2();

    /// <summary>Implicit conversion from System.Numerics.Vector2.</summary>
    public static implicit operator Vector2(System.Numerics.Vector2 v) => FromNumericsVector2(v);

    /// <inheritdoc/>
    public bool Equals(Vector2 other) => X.Equals(other.X) && Y.Equals(other.Y);

    /// <inheritdoc/>
    public override bool Equals(object? obj) => obj is Vector2 other && Equals(other);

    /// <inheritdoc/>
    public override int GetHashCode() => HashCode.Combine(X, Y);

    /// <inheritdoc/>
    public override string ToString() => $"({X:F2}, {Y:F2})";

    /// <summary>
    /// Returns a formatted string representation.
    /// </summary>
    /// <param name="format">The format string for each component.</param>
    /// <param name="formatProvider">The format provider.</param>
    /// <returns>The formatted string.</returns>
    public string ToString(string? format, IFormatProvider? formatProvider = null)
    {
        return $"({X.ToString(format, formatProvider)}, {Y.ToString(format, formatProvider)})";
    }
}
