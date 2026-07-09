// Fibonacci sequence generator
fun fibonacci(n: Int): Int {
  if (n <= 1) {
    return n;
  }
  return fibonacci(n - 1) + fibonacci(n - 2);
}

fun main(): Unit {
  let n: Int = 10;
  println("Fibonacci(" + intToString(n) + ") = " + intToString(fibonacci(n)));
}
