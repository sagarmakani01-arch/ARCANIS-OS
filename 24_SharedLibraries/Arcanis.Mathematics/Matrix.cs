using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace Arcanis.Mathematics;

/// <summary>
/// A high-performance 4x4 matrix for 3D transformations.
/// Uses row-major order.
/// </summary>
[StructLayout(LayoutKind.Sequential)]
public struct Matrix4x4 : IEquatable<Matrix4x4>, IFormattable
{
    /// <summary>Matrix elements in row-major order.</summary>
    public float M00, M01, M02, M03;
    public float M10, M11, M12, M13;
    public float M20, M21, M22, M23;
    public float M30, M31, M32, M33;

    /// <summary>The identity matrix.</summary>
    public static readonly Matrix4x4 Identity = new(
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 0,
        0, 0, 0, 1);

    /// <summary>A zero matrix.</summary>
    public static readonly Matrix4x4 Zero = new(
        0, 0, 0, 0,
        0, 0, 0, 0,
        0, 0, 0, 0,
        0, 0, 0, 0);

    /// <summary>
    /// Initializes a new Matrix4x4.
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public Matrix4x4(
        float m00, float m01, float m02, float m03,
        float m10, float m11, float m12, float m13,
        float m20, float m21, float m22, float m23,
        float m30, float m31, float m32, float m33)
    {
        M00 = m00; M01 = m01; M02 = m02; M03 = m03;
        M10 = m10; M11 = m11; M12 = m12; M13 = m13;
        M20 = m20; M21 = m21; M22 = m22; M23 = m23;
        M30 = m30; M31 = m31; M32 = m32; M33 = m33;
    }

    /// <summary>
    /// Gets the determinant of the matrix.
    /// </summary>
    public float Determinant
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        get
        {
            return M00 * (M11 * (M22 * M33 - M23 * M32) - M12 * (M21 * M33 - M23 * M31) + M13 * (M21 * M32 - M22 * M31))
                 - M01 * (M10 * (M22 * M33 - M23 * M32) - M12 * (M20 * M33 - M23 * M30) + M13 * (M20 * M32 - M22 * M30))
                 + M02 * (M10 * (M21 * M33 - M23 * M31) - M11 * (M20 * M33 - M23 * M30) + M13 * (M20 * M31 - M21 * M30))
                 - M03 * (M10 * (M21 * M32 - M22 * M31) - M11 * (M20 * M32 - M22 * M30) + M12 * (M20 * M31 - M21 * M30));
        }
    }

    /// <summary>
    /// Creates a translation matrix.
    /// </summary>
    /// <param name="x">X translation.</param>
    /// <param name="y">Y translation.</param>
    /// <param name="z">Z translation.</param>
    /// <returns>The translation matrix.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Matrix4x4 CreateTranslation(float x, float y, float z)
    {
        return new Matrix4x4(
            1, 0, 0, x,
            0, 1, 0, y,
            0, 0, 1, z,
            0, 0, 0, 1);
    }

    /// <summary>
    /// Creates a scale matrix.
    /// </summary>
    /// <param name="x">X scale.</param>
    /// <param name="y">Y scale.</param>
    /// <param name="z">Z scale.</param>
    /// <returns>The scale matrix.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Matrix4x4 CreateScale(float x, float y, float z)
    {
        return new Matrix4x4(
            x, 0, 0, 0,
            0, y, 0, 0,
            0, 0, z, 0,
            0, 0, 0, 1);
    }

    /// <summary>
    /// Creates a rotation matrix around the X axis.
    /// </summary>
    /// <param name="radians">The rotation angle in radians.</param>
    /// <returns>The rotation matrix.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Matrix4x4 CreateRotationX(float radians)
    {
        float cos = MathF.Cos(radians);
        float sin = MathF.Sin(radians);
        return new Matrix4x4(
            1, 0, 0, 0,
            0, cos, -sin, 0,
            0, sin, cos, 0,
            0, 0, 0, 1);
    }

    /// <summary>
    /// Creates a rotation matrix around the Y axis.
    /// </summary>
    /// <param name="radians">The rotation angle in radians.</param>
    /// <returns>The rotation matrix.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Matrix4x4 CreateRotationY(float radians)
    {
        float cos = MathF.Cos(radians);
        float sin = MathF.Sin(radians);
        return new Matrix4x4(
            cos, 0, sin, 0,
            0, 1, 0, 0,
            -sin, 0, cos, 0,
            0, 0, 0, 1);
    }

    /// <summary>
    /// Creates a rotation matrix around the Z axis.
    /// </summary>
    /// <param name="radians">The rotation angle in radians.</param>
    /// <returns>The rotation matrix.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Matrix4x4 CreateRotationZ(float radians)
    {
        float cos = MathF.Cos(radians);
        float sin = MathF.Sin(radians);
        return new Matrix4x4(
            cos, -sin, 0, 0,
            sin, cos, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1);
    }

    /// <summary>
    /// Creates a rotation matrix from axis and angle.
    /// </summary>
    /// <param name="axis">The rotation axis (will be normalized).</param>
    /// <param name="radians">The rotation angle in radians.</param>
    /// <returns>The rotation matrix.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Matrix4x4 CreateFromAxisAngle(Vector3D axis, float radians)
    {
        axis = axis.Normalized;
        float cos = MathF.Cos(radians);
        float sin = MathF.Sin(radians);
        float t = 1 - cos;

        return new Matrix4x4(
            t * axis.X * axis.X + cos, t * axis.X * axis.Y - sin * axis.Z, t * axis.X * axis.Z + sin * axis.Y, 0,
            t * axis.X * axis.Y + sin * axis.Z, t * axis.Y * axis.Y + cos, t * axis.Y * axis.Z - sin * axis.X, 0,
            t * axis.X * axis.Z - sin * axis.Y, t * axis.Y * axis.Z + sin * axis.X, t * axis.Z * axis.Z + cos, 0,
            0, 0, 0, 1);
    }

    /// <summary>
    /// Creates a perspective projection matrix.
    /// </summary>
    /// <param name="fovY">Field of view in radians.</param>
    /// <param name="aspectRatio">Aspect ratio.</param>
    /// <param name="nearPlane">Near clipping plane distance.</param>
    /// <param name="farPlane">Far clipping plane distance.</param>
    /// <returns>The perspective matrix.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Matrix4x4 CreatePerspectiveFieldOfView(float fovY, float aspectRatio, float nearPlane, float farPlane)
    {
        float yScale = 1.0f / MathF.Tan(fovY / 2.0f);
        float xScale = yScale / aspectRatio;
        float depthRange = farPlane / (nearPlane - farPlane);

        return new Matrix4x4(
            xScale, 0, 0, 0,
            0, yScale, 0, 0,
            0, 0, depthRange, nearPlane * depthRange,
            0, 0, -1, 0);
    }

    /// <summary>
    /// Creates an orthographic projection matrix.
    /// </summary>
    /// <param name="width">The view width.</param>
    /// <param name="height">The view height.</param>
    /// <param name="nearPlane">Near clipping plane distance.</param>
    /// <param name="farPlane">Far clipping plane distance.</param>
    /// <returns>The orthographic matrix.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Matrix4x4 CreateOrthographic(float width, float height, float nearPlane, float farPlane)
    {
        float depthRange = 1.0f / (nearPlane - farPlane);

        return new Matrix4x4(
            2.0f / width, 0, 0, 0,
            0, 2.0f / height, 0, 0,
            0, 0, depthRange, nearPlane * depthRange,
            0, 0, 0, 1);
    }

    /// <summary>
    /// Creates a look-at view matrix.
    /// </summary>
    /// <param name="eye">The camera position.</param>
    /// <param name="target">The target position.</param>
    /// <param name="up">The up vector.</param>
    /// <returns>The view matrix.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Matrix4x4 CreateLookAt(Vector3D eye, Vector3D target, Vector3D up)
    {
        var zAxis = (eye - target).Normalized;
        var xAxis = Vector3D.Cross(up, zAxis).Normalized;
        var yAxis = Vector3D.Cross(zAxis, xAxis);

        return new Matrix4x4(
            xAxis.X, xAxis.Y, xAxis.Z, -Vector3D.Dot(xAxis, eye),
            yAxis.X, yAxis.Y, yAxis.Z, -Vector3D.Dot(yAxis, eye),
            zAxis.X, zAxis.Y, zAxis.Z, -Vector3D.Dot(zAxis, eye),
            0, 0, 0, 1);
    }

    /// <summary>
    /// Transposes the matrix.
    /// </summary>
    /// <returns>The transposed matrix.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public Matrix4x4 Transpose()
    {
        return new Matrix4x4(
            M00, M10, M20, M30,
            M01, M11, M21, M31,
            M02, M12, M22, M32,
            M03, M13, M23, M33);
    }

    /// <summary>
    /// Inverts the matrix.
    /// </summary>
    /// <returns>The inverted matrix.</returns>
    public Matrix4x4 Inverse()
    {
        float det = Determinant;
        if (MathF.Abs(det) < 1E-06f)
            throw new InvalidOperationException("Matrix is not invertible.");

        float invDet = 1.0f / det;

        return new Matrix4x4(
            (M11 * (M22 * M33 - M23 * M32) - M12 * (M21 * M33 - M23 * M31) + M13 * (M21 * M32 - M22 * M31)) * invDet,
            -(M01 * (M22 * M33 - M23 * M32) - M02 * (M21 * M33 - M23 * M31) + M03 * (M21 * M32 - M22 * M31)) * invDet,
            (M01 * (M12 * M33 - M13 * M32) - M02 * (M11 * M33 - M13 * M31) + M03 * (M11 * M32 - M12 * M31)) * invDet,
            -(M01 * (M12 * M23 - M13 * M22) - M02 * (M11 * M23 - M13 * M21) + M03 * (M11 * M22 - M12 * M21)) * invDet,
            -(M10 * (M22 * M33 - M23 * M32) - M12 * (M20 * M33 - M23 * M30) + M13 * (M20 * M32 - M22 * M30)) * invDet,
            (M00 * (M22 * M33 - M23 * M32) - M02 * (M20 * M33 - M23 * M30) + M03 * (M20 * M32 - M22 * M30)) * invDet,
            -(M00 * (M12 * M33 - M13 * M32) - M02 * (M10 * M33 - M13 * M30) + M03 * (M10 * M32 - M12 * M30)) * invDet,
            (M00 * (M12 * M23 - M13 * M22) - M02 * (M10 * M23 - M13 * M20) + M03 * (M10 * M22 - M12 * M20)) * invDet,
            (M10 * (M21 * M33 - M23 * M31) - M11 * (M20 * M33 - M23 * M30) + M13 * (M20 * M31 - M21 * M30)) * invDet,
            -(M00 * (M21 * M33 - M23 * M31) - M01 * (M20 * M33 - M23 * M30) + M03 * (M20 * M31 - M21 * M30)) * invDet,
            (M00 * (M11 * M33 - M13 * M31) - M01 * (M10 * M33 - M13 * M30) + M03 * (M10 * M31 - M11 * M30)) * invDet,
            -(M00 * (M11 * M23 - M13 * M21) - M01 * (M10 * M23 - M13 * M20) + M03 * (M10 * M21 - M11 * M20)) * invDet,
            -(M10 * (M21 * M32 - M22 * M31) - M11 * (M20 * M32 - M22 * M30) + M12 * (M20 * M31 - M21 * M30)) * invDet,
            (M00 * (M21 * M32 - M22 * M31) - M01 * (M20 * M32 - M22 * M30) + M02 * (M20 * M31 - M21 * M30)) * invDet,
            -(M00 * (M11 * M32 - M12 * M31) - M01 * (M10 * M32 - M12 * M30) + M02 * (M10 * M31 - M11 * M30)) * invDet,
            (M00 * (M11 * M22 - M12 * M21) - M01 * (M10 * M22 - M12 * M20) + M02 * (M10 * M21 - M11 * M20)) * invDet);
    }

    /// <summary>Operator * for matrix multiplication.</summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Matrix4x4 operator *(Matrix4x4 a, Matrix4x4 b)
    {
        return new Matrix4x4(
            a.M00 * b.M00 + a.M01 * b.M10 + a.M02 * b.M20 + a.M03 * b.M30,
            a.M00 * b.M01 + a.M01 * b.M11 + a.M02 * b.M21 + a.M03 * b.M31,
            a.M00 * b.M02 + a.M01 * b.M12 + a.M02 * b.M22 + a.M03 * b.M32,
            a.M00 * b.M03 + a.M01 * b.M13 + a.M02 * b.M23 + a.M03 * b.M33,

            a.M10 * b.M00 + a.M11 * b.M10 + a.M12 * b.M20 + a.M13 * b.M30,
            a.M10 * b.M01 + a.M11 * b.M11 + a.M12 * b.M21 + a.M13 * b.M31,
            a.M10 * b.M02 + a.M11 * b.M12 + a.M12 * b.M22 + a.M13 * b.M32,
            a.M10 * b.M03 + a.M11 * b.M13 + a.M12 * b.M23 + a.M13 * b.M33,

            a.M20 * b.M00 + a.M21 * b.M10 + a.M22 * b.M20 + a.M23 * b.M30,
            a.M20 * b.M01 + a.M21 * b.M11 + a.M22 * b.M21 + a.M23 * b.M31,
            a.M20 * b.M02 + a.M21 * b.M12 + a.M22 * b.M22 + a.M23 * b.M32,
            a.M20 * b.M03 + a.M21 * b.M13 + a.M22 * b.M23 + a.M23 * b.M33,

            a.M30 * b.M00 + a.M31 * b.M10 + a.M32 * b.M20 + a.M33 * b.M30,
            a.M30 * b.M01 + a.M31 * b.M11 + a.M32 * b.M21 + a.M33 * b.M31,
            a.M30 * b.M02 + a.M31 * b.M12 + a.M32 * b.M22 + a.M33 * b.M32,
            a.M30 * b.M03 + a.M31 * b.M13 + a.M32 * b.M23 + a.M33 * b.M33);
    }

    /// <summary>Operator * for matrix-vector multiplication.</summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3D operator *(Matrix4x4 m, Vector3D v)
    {
        float w = m.M30 * v.X + m.M31 * v.Y + m.M32 * v.Z + m.M33;
        if (MathF.Abs(w) < 1E-06f) w = 1;

        return new Vector3D(
            (m.M00 * v.X + m.M01 * v.Y + m.M02 * v.Z + m.M03) / w,
            (m.M10 * v.X + m.M11 * v.Y + m.M12 * v.Z + m.M13) / w,
            (m.M20 * v.X + m.M21 * v.Y + m.M22 * v.Z + m.M23) / w);
    }

    /// <summary>Equality operator.</summary>
    public static bool operator ==(Matrix4x4 left, Matrix4x4 right) => left.Equals(right);

    /// <summary>Inequality operator.</summary>
    public static bool operator !=(Matrix4x4 left, Matrix4x4 right) => !left.Equals(right);

    /// <inheritdoc/>
    public bool Equals(Matrix4x4 other)
    {
        return M00.Equals(other.M00) && M01.Equals(other.M01) && M02.Equals(other.M02) && M03.Equals(other.M03) &&
               M10.Equals(other.M10) && M11.Equals(other.M11) && M12.Equals(other.M12) && M13.Equals(other.M13) &&
               M20.Equals(other.M20) && M21.Equals(other.M21) && M22.Equals(other.M22) && M23.Equals(other.M23) &&
               M30.Equals(other.M30) && M31.Equals(other.M31) && M32.Equals(other.M32) && M33.Equals(other.M33);
    }

    /// <inheritdoc/>
    public override bool Equals(object? obj) => obj is Matrix4x4 other && Equals(other);

    /// <inheritdoc/>
    public override int GetHashCode() => HashCode.Combine(M00, M01, M02, M03, M10, M11, M12, M13);

    /// <inheritdoc/>
    public override string ToString() =>
        $"[{M00:F2} {M01:F2} {M02:F2} {M03:F2}]\n" +
        $"[{M10:F2} {M11:F2} {M12:F2} {M13:F2}]\n" +
        $"[{M20:F2} {M21:F2} {M22:F2} {M23:F2}]\n" +
        $"[{M30:F2} {M31:F2} {M32:F2} {M33:F2}]";

    /// <inheritdoc/>
    public string ToString(string? format, IFormatProvider? formatProvider = null)
    {
        return $"[{M00.ToString(format, formatProvider)} {M01.ToString(format, formatProvider)} {M02.ToString(format, formatProvider)} {M03.ToString(format, formatProvider)}]\n" +
               $"[{M10.ToString(format, formatProvider)} {M11.ToString(format, formatProvider)} {M12.ToString(format, formatProvider)} {M13.ToString(format, formatProvider)}]\n" +
               $"[{M20.ToString(format, formatProvider)} {M21.ToString(format, formatProvider)} {M22.ToString(format, formatProvider)} {M23.ToString(format, formatProvider)}]\n" +
               $"[{M30.ToString(format, formatProvider)} {M31.ToString(format, formatProvider)} {M32.ToString(format, formatProvider)} {M33.ToString(format, formatProvider)}]";
    }
}
