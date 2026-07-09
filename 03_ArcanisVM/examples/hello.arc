// Hello World
print("Hello, Arcanis!");

// Variables
var name = "ArcanisVM";
var version = 1.0;
print("Running " + name + " v" + toString(version));

// Calculations
var result = 0;
for (var i = 0; i < 10; i = i + 1) {
    result = result + i;
}
print("Sum 0-9: " + toString(result));

// Functions
fun greet(name) {
    return "Hello, " + name + "!";
}

print(greet("User"));
