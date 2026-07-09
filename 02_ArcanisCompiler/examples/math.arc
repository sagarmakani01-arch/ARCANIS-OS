// Math utilities in ArcanisLang
fun factorial(n: Int): Int {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}

fun isEven(x: Int): Bool {
  return x % 2 == 0;
}

fun sum(a: Int, b: Int): Int {
  return a + b;
}

fun main(): Unit {
  println("Factorial of 5: " + intToString(factorial(5)));
  println("Is 7 even? " + intToString(if (isEven(7)) { 1 } else { 0 }));
  println("Sum 10 + 20 = " + intToString(sum(10, 20)));
}
