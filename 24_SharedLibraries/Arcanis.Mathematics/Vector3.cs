using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace Arcanis.Mathematics;

/// <summary>
/// A high-performance 3D vector struct.
/// </summary>
[StructLayout(LayoutKind.Sequential)]
public struct Vector3D : IEquatable<Vector3D>, IFormattable
{
    /// <summary>The X component.</summary>
    public float X;
    /// <summary>The Y component.</summary>
    public float Y;
    /// <summary>The Z component.</summary>
    public float Z;

    /// <summary>A vector with all components set to zero.</summary>
    public static readonly Vector3D Zero = new(0, 0, 0);
    /// <summary>A vector with all components set to one.</summary>
    public static readonly Vector3D One = new(1, 1, 1);
    /// <summary>A unit vector pointing right.</summary>
    public static readonly Vector3D Right = new(1, 0, 0);
    /// <summary>A unit vector pointing left.</summary>
    public static readonly Vector3D Left = new(-1, 0, 0);
    /// <summary>A unit vector pointing up.</summary>
    public static readonly Vector3D Up = new(0, 1, 0);
    /// <summary>A unit vector pointing down.</summary>
    public static readonly Vector3D Down = new(0, -1, 0);
    /// <summary>A unit vector pointing forward.</summary>
    public static readonly Vector3D Forward = new(0, 0, 1);
    /// <summary>A unit vector pointing backward.</summary>
    public static readonly Vector3D Backward = new(0, 0, -1);

    /// <summary>
    /// Gets the magnitude (length) of the vector.
    /// </summary>
    public float Magnitude
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        get => MathF.Sqrt(X * X + Y * Y + Z * Z);
    }

    /// <summary>
    /// Gets the squared magnitude (faster for comparisons).
    /// </summary>
    public float SqrMagnitude
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        get => X * X + Y * Y + Z * Z;
    }

    /// <summary>
    /// Gets a normalized version of the vector.
    /// </summary>
    public Vector3D Normalized
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
    /// Initializes a new Vector3D.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public Vector3D(float x, float y, float z)
    {
        X = x;
        Y = y;
        Z = z;
    }

    /// <summary>
    /// Initializes a new Vector3D with all components set to the same value.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public Vector3D(float value) : this(value, value, value) { }

    /// <summary>
    /// Calculates the dot product of two vectors.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static float Dot(Vector3D a, Vector3D b) => a.X * b.X + a.Y * b.Y + a.Z * b.Z;

    /// <summary>
    /// Calculates the cross product of two vectors.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3D Cross(Vector3D a, Vector3D b)
    {
        return new Vector3D(
            a.Y * b.Z - a.Z * b.Y,
            a.Z * b.X - a.X * b.Z,
            a.X * b.Y - a.Y * b.X);
    }

    /// <summary>
    /// Calculates the distance between two vectors.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static float Distance(Vector3D a, Vector3D b) => (a - b).Magnitude;

    /// <summary>
    /// Calculates the squared distance between two vectors.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static float SqrDistance(Vector3D a, Vector3D b) => (a - b).SqrMagnitude;

    /// <summary>
    /// Linearly interpolates between two vectors.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3D Lerp(Vector3D a, Vector3D b, float t)
    {
        t = Math.Clamp(t, 0f, 1f);
        return new Vector3D(
            a.X + (b.X - a.X) * t,
            a.Y + (b.Y - a.Y) * t,
            a.Z + (b.Z - a.Z) * t);
    }

    /// <summary>
    /// Clamps the vector components to the specified range.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3D Clamp(Vector3D value, float min, float max)
    {
        return new Vector3D(
            Math.Clamp(value.X, min, max),
            Math.Clamp(value.Y, min, max),
            Math.Clamp(value.Z, min, max));
    }

    /// <summary>
    /// Returns the vector with its magnitude clamped to max length.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3D ClampMagnitude(Vector3D vector, float maxLength)
    {
        if (vector.SqrMagnitude > maxLength * maxLength)
            return vector.Normalized * maxLength;
        return vector;
    }

    /// <summary>
    /// Reflects a vector off a surface with the given normal.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3D Reflect(Vector3D direction, Vector3D normal)
    {
        return direction - 2 * Dot(direction, normal) * normal;
    }

    /// <summary>
    /// Projects one vector onto another.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3D Project(Vector3D vector, Vector3D onNormal)
    {
        float sqrMag = Dot(onNormal, onNormal);
        if (sqrMag < 1E-06f) return Zero;
        return onNormal * Dot(vector, onNormal) / sqrMag;
    }

    /// <summary>
    /// Projects one vector onto a plane defined by a normal.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3D ProjectOnPlane(Vector3D vector, Vector3D planeNormal)
    {
        return vector - Project(vector, planeNormal);
    }

    /// <summary>
    /// Calculates the angle between two vectors in radians.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static float Angle(Vector3D from, Vector3D to)
    {
        float denominator = MathF.Sqrt(from.SqrMagnitude * to.SqrMagnitude);
        if (denominator < 1E-15f) return 0f;
        float dot = Math.Clamp(Dot(from, to) / denominator, -1f, 1f);
        return MathF.Acos(dot);
    }

    /// <summary>
    /// Rotates a vector around an axis by the given angle.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3D RotateAroundAxis(Vector3D vector, Vector3D axis, float angleRadians)
    {
        axis = axis.Normalized;
        float cos = MathF.Cos(angleRadians);
        float sin = MathF.Sin(angleRadians);

        return vector * cos +
               Cross(axis, vector) * sin +
               axis * Dot(axis, vector) * (1 - cos);
    }

    /// <summary>
    /// Converts to System.Numerics.Vector3.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public System.Numerics.Vector3 ToNumericsVector3() => new(X, Y, Z);

    /// <summary>
    /// Creates from System.Numerics.Vector3.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3D FromNumericsVector3(System.Numerics.Vector3 v) => new(v.X, v.Y, v.Z);

    /// <summary>Operator + for vector addition.</summary>
    public static Vector3D operator +(Vector3D a, Vector3D b) => new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);

    /// <summary>Operator - for vector subtraction.</summary>
    public static Vector3D operator -(Vector3D a, Vector3D b) => new(a.X - b.X, a.Y - b.Y, a.Z - b.Z);

    /// <summary>Operator * for scalar multiplication.</summary>
    public static Vector3D operator *(Vector3D a, float scalar) => new(a.X * scalar, a.Y * scalar, a.Z * scalar);

    /// <summary>Operator * for scalar multiplication.</summary>
    public static Vector3D operator *(float scalar, Vector3D a) => new(a.X * scalar, a.Y * scalar, a.Z * scalar);

    /// <summary>Operator / for scalar division.</summary>
    public static Vector3D operator /(Vector3D a, float scalar) => new(a.X / scalar, a.Y / scalar, a.Z / scalar);

    /// <summary>Operator - for unary negation.</summary>
    public static Vector3D operator -(Vector3D a) => new(-a.X, -a.Y, -a.Z);

    /// <summary>Equality operator.</summary>
    public static bool operator ==(Vector3D left, Vector3D right) => left.Equals(right);

    /// <summary>Inequality operator.</summary>
    public static bool operator !=(Vector3D left, Vector3D right) => !left.Equals(right);

    /// <summary>Implicit conversion to System.Numerics.Vector3.</summary>
    public static implicit operator System.Numerics.Vector3(Vector3D v) => v.ToNumericsVector3();

    /// <summary>Implicit conversion from System.Numerics.Vector3.</summary>
    public static implicit operator Vector3D(System.Numerics.Vector3 v) => FromNumericsVector3(v);

    /// <inheritdoc/>
    public bool Equals(Vector3D other) => X.Equals(other.X) && Y.Equals(other.Y) && Z.Equals(other.Z);

    /// <inheritdoc/>
    public override bool Equals(object? obj) => obj is Vector3D other && Equals(other);

    /// <inheritdoc/>
    public override int GetHashCode() => HashCode.Combine(X, Y, Z);

    /// <inheritdoc/>
    public override string ToString() => $"({X:F2}, {Y:F2}, {Z:F2})";

    /// <summary>
    /// Returns a formatted string representation.
    /// </summary>
    public string ToString(string? format, IFormatProvider? formatProvider = null)
    {
        return $"({X.ToString(format, formatProvider)}, {Y.ToString(format, formatProvider)}, {Z.ToString(format, formatProvider)})";
    }
}
