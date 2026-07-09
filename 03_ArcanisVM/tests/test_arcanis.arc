// ArcanisVM Test Suite
// Run with: arcanisvm tests/test_arcanis.arc

print("=== ArcanisVM Test Suite ===");
print("");

// Helper
var testCount = 0;
var passCount = 0;

fun test(name, fn) {
    testCount = testCount + 1;
    print("  Test: " + name + "...");
    fn();
    passCount = passCount + 1;
    print("    PASS");
}

// === Basic Operations ===
test("nil literal", fun() {
    var x = nil;
    assert(type(x) == "nil");
});

test("boolean literals", fun() {
    assert(true == true);
    assert(false == false);
    assert(true != false);
    assert(type(true) == "bool");
});

test("integer arithmetic", fun() {
    assert(1 + 2 == 3);
    assert(5 - 3 == 2);
    assert(3 * 4 == 12);
    assert(10 / 2 == 5);
    assert(10 % 3 == 1);
    assert(-5 == -5);
});

test("float arithmetic", fun() {
    var x = 3.14;
    assert(x > 3.0);
    assert(x < 4.0);
    assert(type(x) == "float");
});

test("string operations", fun() {
    var s = "hello";
    assert(len(s) == 5);
    assert(s[0] == "h");
    assert(s[4] == "o");
    assert(type(s) == "string");
});

test("string concatenation", fun() {
    var s = "hello " + "world";
    assert(s == "hello world");
    assert(len(s) == 11);
});

// === Variables ===
test("variable declaration", fun() {
    var x = 42;
    assert(x == 42);
    x = 100;
    assert(x == 100);
});

test("multiple variables", fun() {
    var a = 1;
    var b = 2;
    var c = a + b;
    assert(c == 3);
});

// === Control Flow ===
test("if statement", fun() {
    var x = 0;
    if (true) { x = 1; }
    assert(x == 1);
    if (false) { x = 2; }
    assert(x == 1);
});

test("if-else statement", fun() {
    var x = 0;
    if (false) { x = 1; } else { x = 2; }
    assert(x == 2);
});

test("while loop", fun() {
    var i = 0;
    var sum = 0;
    while (i < 5) {
        sum = sum + i;
        i = i + 1;
    }
    assert(sum == 10);
    assert(i == 5);
});

test("for loop", fun() {
    var sum = 0;
    for (var i = 0; i < 10; i = i + 1) {
        sum = sum + i;
    }
    assert(sum == 45);
});

// === Functions ===
test("function definition and call", fun() {
    fun add(a, b) {
        return a + b;
    }
    assert(add(3, 4) == 7);
});

test("recursive function", fun() {
    fun factorial(n) {
        if (n <= 1) return 1;
        return n * factorial(n - 1);
    }
    assert(factorial(5) == 120);
    assert(factorial(0) == 1);
});

test("fibonacci", fun() {
    fun fib(n) {
        if (n < 2) return n;
        return fib(n-1) + fib(n-2);
    }
    assert(fib(0) == 0);
    assert(fib(1) == 1);
    assert(fib(10) == 55);
});

// === Arrays ===
test("array literal", fun() {
    var arr = [1, 2, 3];
    assert(len(arr) == 3);
    assert(arr[0] == 1);
    assert(arr[2] == 3);
});

test("array push", fun() {
    var arr = [];
    arrayPush(arr, 10);
    arrayPush(arr, 20);
    assert(len(arr) == 2);
    assert(arr[0] == 10);
    assert(arr[1] == 20);
});

test("array pop", fun() {
    var arr = [1, 2, 3];
    var v = arrayPop(arr);
    assert(v == 3);
    assert(len(arr) == 2);
});

test("array insert and remove", fun() {
    var arr = [1, 3];
    arrayInsert(arr, 1, 2);
    assert(arr[0] == 1);
    assert(arr[1] == 2);
    assert(arr[2] == 3);
    var r = arrayRemove(arr, 1);
    assert(r == 2);
    assert(len(arr) == 2);
});

test("array slice", fun() {
    var arr = [0, 1, 2, 3, 4];
    var s = arraySlice(arr, 1, 3);
    assert(len(s) == 2);
    assert(s[0] == 1);
    assert(s[1] == 2);
});

// === Maps ===
test("map literal", fun() {
    var m = {"a": 1, "b": 2};
    assert(mapHas(m, "a") == true);
    assert(m["a"] == 1);
    assert(m["b"] == 2);
});

test("map keys and values", fun() {
    var m = {"x": 10, "y": 20};
    var keys = mapKeys(m);
    assert(len(keys) == 2);
    var vals = mapValues(m);
    assert(len(vals) == 2);
});

// === Built-in Functions ===
test("len function", fun() {
    assert(len("hello") == 5);
    assert(len([1, 2, 3]) == 3);
    assert(len("") == 0);
    assert(len([]) == 0);
});

test("type function", fun() {
    assert(type(nil) == "nil");
    assert(type(true) == "bool");
    assert(type(42) == "int");
    assert(type(3.14) == "float");
    assert(type("hi") == "string");
    assert(type([1]) == "array");
});

test("toInt and toFloat", fun() {
    assert(toInt(3.14) == 3);
    assert(toFloat(42) == 42.0);
    assert(toInt("123") == 123);
});

// === Scope ===
test("block scope", fun() {
    var x = 1;
    {
        var x = 2;
        assert(x == 2);
    }
    assert(x == 1);
});

// === Comparison ===
test("comparison operators", fun() {
    assert(1 < 2);
    assert(2 > 1);
    assert(1 <= 1);
    assert(1 >= 1);
    assert(1 == 1);
    assert(1 != 2);
});

// === Logical Operators ===
test("logical operators", fun() {
    assert(true and true);
    assert(true or false);
    assert(not false);
    assert(not (false or false));
});

// === Nested Calls ===
test("nested function calls", fun() {
    fun add(a, b) { return a + b; }
    fun mul(a, b) { return a * b; }
    assert(mul(add(2, 3), add(4, 5)) == 45);
});

// === Summary ===
print("");
print("=== Results ===");
print("Passed: " + toString(passCount) + " / " + toString(testCount));
if (passCount == testCount) {
    print("ALL TESTS PASSED!");
} else {
    print("SOME TESTS FAILED!");
    exit(1);
}
