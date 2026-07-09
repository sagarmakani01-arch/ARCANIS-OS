using System.Runtime.CompilerServices;

namespace Arcanis.Mathematics;

/// <summary>
/// High-performance statistical functions for data analysis.
/// </summary>
public static class Statistics
{
    /// <summary>
    /// Calculates the mean (average) of a collection of numbers.
    /// </summary>
    /// <param name="values">The values to average.</param>
    /// <returns>The mean value.</returns>
    public static double Mean(IEnumerable<double> values)
    {
        double sum = 0;
        int count = 0;

        foreach (var value in values)
        {
            sum += value;
            count++;
        }

        if (count == 0)
            throw new ArgumentException("Collection cannot be empty.", nameof(values));

        return sum / count;
    }

    /// <summary>
    /// Calculates the mean of a collection of floats.
    /// </summary>
    /// <param name="values">The values to average.</param>
    /// <returns>The mean value.</returns>
    public static float Mean(IEnumerable<float> values)
    {
        return (float)Mean(values.Select(v => (double)v));
    }

    /// <summary>
    /// Calculates the median of a collection of numbers.
    /// </summary>
    /// <param name="values">The values.</param>
    /// <returns>The median value.</returns>
    public static double Median(IEnumerable<double> values)
    {
        var sorted = values.OrderBy(x => x).ToList();
        int count = sorted.Count;

        if (count == 0)
            throw new ArgumentException("Collection cannot be empty.", nameof(values));

        if (count % 2 == 0)
        {
            return (sorted[count / 2 - 1] + sorted[count / 2]) / 2.0;
        }
        else
        {
            return sorted[count / 2];
        }
    }

    /// <summary>
    /// Calculates the mode (most frequent value) of a collection.
    /// </summary>
    /// <param name="values">The values.</param>
    /// <returns>The mode value(s).</returns>
    public static IEnumerable<double> Mode(IEnumerable<double> values)
    {
        var groups = values.GroupBy(v => v);
        int maxCount = groups.Max(g => g.Count());
        return groups.Where(g => g.Count() == maxCount).Select(g => g.Key);
    }

    /// <summary>
    /// Calculates the variance of a collection of numbers.
    /// </summary>
    /// <param name="values">The values.</param>
    /// <param name="population">If true, calculates population variance; otherwise, sample variance.</param>
    /// <returns>The variance.</returns>
    public static double Variance(IEnumerable<double> values, bool population = false)
    {
        var list = values.ToList();
        int count = list.Count;

        if (count < 2 && !population)
            throw new ArgumentException("Need at least 2 values for sample variance.", nameof(values));

        double mean = Mean(list);
        double sumSquaredDiff = list.Sum(v => (v - mean) * (v - mean));

        return population ? sumSquaredDiff / count : sumSquaredDiff / (count - 1);
    }

    /// <summary>
    /// Calculates the standard deviation of a collection of numbers.
    /// </summary>
    /// <param name="values">The values.</param>
    /// <param name="population">If true, calculates population std dev; otherwise, sample.</param>
    /// <returns>The standard deviation.</returns>
    public static double StandardDeviation(IEnumerable<double> values, bool population = false)
    {
        return Math.Sqrt(Variance(values, population));
    }

    /// <summary>
    /// Calculates the covariance of two collections.
    /// </summary>
    /// <param name="x">First collection.</param>
    /// <param name="y">Second collection.</param>
    /// <returns>The covariance.</returns>
    public static double Covariance(IEnumerable<double> x, IEnumerable<double> y)
    {
        var xList = x.ToList();
        var yList = y.ToList();

        if (xList.Count != yList.Count)
            throw new ArgumentException("Collections must have the same length.", nameof(y));

        int n = xList.Count;
        if (n < 2)
            throw new ArgumentException("Need at least 2 values.", nameof(x));

        double meanX = Mean(xList);
        double meanY = Mean(yList);

        double sum = 0;
        for (int i = 0; i < n; i++)
        {
            sum += (xList[i] - meanX) * (yList[i] - meanY);
        }

        return sum / (n - 1);
    }

    /// <summary>
    /// Calculates the Pearson correlation coefficient.
    /// </summary>
    /// <param name="x">First collection.</param>
    /// <param name="y">Second collection.</param>
    /// <returns>The correlation coefficient (-1 to 1).</returns>
    public static double Correlation(IEnumerable<double> x, IEnumerable<double> y)
    {
        double cov = Covariance(x, y);
        double stdX = StandardDeviation(x);
        double stdY = StandardDeviation(y);

        if (stdX == 0 || stdY == 0)
            return 0;

        return cov / (stdX * stdY);
    }

    /// <summary>
    /// Calculates the percentile of a value in a collection.
    /// </summary>
    /// <param name="values">The values.</param>
    /// <param name="percentile">The percentile (0-100).</param>
    /// <returns>The percentile value.</returns>
    public static double Percentile(IEnumerable<double> values, double percentile)
    {
        var sorted = values.OrderBy(x => x).ToList();
        int count = sorted.Count;

        if (count == 0)
            throw new ArgumentException("Collection cannot be empty.", nameof(values));

        if (percentile < 0 || percentile > 100)
            throw new ArgumentOutOfRangeException(nameof(percentile), "Percentile must be between 0 and 100.");

        double index = (percentile / 100.0) * (count - 1);
        int lower = (int)Math.Floor(index);
        int upper = (int)Math.Ceiling(index);

        if (lower == upper)
            return sorted[lower];

        double fraction = index - lower;
        return sorted[lower] * (1 - fraction) + sorted[upper] * fraction;
    }

    /// <summary>
    /// Calculates the quartiles (Q1, Q2, Q3) of a collection.
    /// </summary>
    /// <param name="values">The values.</param>
    /// <returns>The quartiles (Q1, Q2/Median, Q3).</returns>
    public static (double Q1, double Q2, double Q3) Quartiles(IEnumerable<double> values)
    {
        return (Percentile(values, 25), Percentile(values, 50), Percentile(values, 75));
    }

    /// <summary>
    /// Calculates the interquartile range (IQR).
    /// </summary>
    /// <param name="values">The values.</param>
    /// <returns>The IQR (Q3 - Q1).</returns>
    public static double InterquartileRange(IEnumerable<double> values)
    {
        var (q1, _, q3) = Quartiles(values);
        return q3 - q1;
    }

    /// <summary>
    /// Calculates the Z-score of a value.
    /// </summary>
    /// <param name="value">The value.</param>
    /// <param name="values">The collection of values.</param>
    /// <returns>The Z-score.</returns>
    public static double ZScore(double value, IEnumerable<double> values)
    {
        double mean = Mean(values);
        double stdDev = StandardDeviation(values);

        if (stdDev == 0)
            return 0;

        return (value - mean) / stdDev;
    }

    /// <summary>
    /// Calculates the moving average of a collection.
    /// </summary>
    /// <param name="values">The values.</param>
    /// <param name="windowSize">The window size.</param>
    /// <returns>The moving averages.</returns>
    public static IEnumerable<double> MovingAverage(IEnumerable<double> values, int windowSize)
    {
        var list = values.ToList();
        int count = list.Count;

        if (windowSize < 1 || windowSize > count)
            throw new ArgumentOutOfRangeException(nameof(windowSize), "Window size must be between 1 and the collection size.");

        var result = new List<double>();
        double windowSum = 0;

        for (int i = 0; i < count; i++)
        {
            windowSum += list[i];

            if (i >= windowSize)
            {
                windowSum -= list[i - windowSize];
            }

            if (i >= windowSize - 1)
            {
                result.Add(windowSum / windowSize);
            }
        }

        return result;
    }

    /// <summary>
    /// Calculates the exponential moving average.
    /// </summary>
    /// <param name="values">The values.</param>
    /// <param name="alpha">The smoothing factor (0-1).</param>
    /// <returnsThe exponential moving averages.</returns>
    public static IEnumerable<double> ExponentialMovingAverage(IEnumerable<double> values, double alpha = 0.3)
    {
        var list = values.ToList();
        if (list.Count == 0) return Enumerable.Empty<double>();

        var result = new List<double> { list[0] };

        for (int i = 1; i < list.Count; i++)
        {
            result.Add(alpha * list[i] + (1 - alpha) * result[i - 1]);
        }

        return result;
    }

    /// <summary>
    /// Calculates the min and max of a collection.
    /// </summary>
    /// <param name="values">The values.</param>
    /// <returns>The minimum and maximum values.</returns>
    public static (double Min, double Max) MinMax(IEnumerable<double> values)
    {
        double min = double.MaxValue;
        double max = double.MinValue;

        foreach (var value in values)
        {
            if (value < min) min = value;
            if (value > max) max = value;
        }

        return (min, max);
    }

    /// <summary>
    /// Normalizes a collection of values to the range [0, 1].
    /// </summary>
    /// <param name="values">The values.</param>
    /// <returns>The normalized values.</returns>
    public static IEnumerable<double> Normalize(IEnumerable<double> values)
    {
        var (min, max) = MinMax(values);
        double range = max - min;

        if (range == 0)
            return values.Select(_ => 0.5);

        return values.Select(v => (v - min) / range);
    }

    /// <summary>
    /// Detects outliers using the IQR method.
    /// </summary>
    /// <param name="values">The values.</param>
    /// <returns>The outlier values.</returns>
    public static IEnumerable<double> DetectOutliers(IEnumerable<double> values)
    {
        var list = values.ToList();
        var (q1, _, q3) = Quartiles(list);
        double iqr = q3 - q1;

        double lowerBound = q1 - 1.5 * iqr;
        double upperBound = q3 + 1.5 * iqr;

        return list.Where(v => v < lowerBound || v > upperBound);
    }
}
