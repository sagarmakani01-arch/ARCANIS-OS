// Fibonacci with memoization
var cache = {};

fun fib(n) {
    if (mapHas(cache, n)) {
        return cache[n];
    }
    var result;
    if (n < 2) {
        result = n;
    } else {
        result = fib(n - 1) + fib(n - 2);
    }
    cache[n] = result;
    return result;
}

// Print first 20 Fibonacci numbers
for (var i = 0; i < 20; i = i + 1) {
    print("fib(" + toString(i) + ") = " + toString(fib(i)));
}
