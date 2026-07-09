// Data Structures in Arcanis

// Arrays
var arr = [];
arrayPush(arr, 10);
arrayPush(arr, 20);
arrayPush(arr, 30);
print("Array: " + toString(arr));
print("Length: " + toString(len(arr)));
print("Pop: " + toString(arrayPop(arr)));

// Maps
var config = {
    "host": "localhost",
    "port": 8080,
    "debug": true
};

print("Host: " + config["host"]);
print("Port: " + toString(config["port"]));
print("Has debug: " + toString(mapHas(config, "debug")));

// List all keys
var keys = mapKeys(config);
for (var i = 0; i < len(keys); i = i + 1) {
    var key = keys[i];
    print("  " + key + " = " + toString(config[key]));
}
