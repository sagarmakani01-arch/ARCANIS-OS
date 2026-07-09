// Object-Oriented Programming in Arcanis

// Base class
class Animal {
    init(name) {
        this.name = name;
    }

    speak() {
        print(this.name + " makes a sound");
    }

    describe() {
        return "Animal(" + this.name + ")";
    }
}

// Derived class
class Dog < Animal {
    init(name, breed) {
        super.init(name);
        this.breed = breed;
    }

    speak() {
        print(this.name + " barks!");
    }

    fetch() {
        print(this.name + " fetches the ball");
    }
}

// Usage
var a = Animal("Generic");
a.speak();

var d = Dog("Buddy", "Golden Retriever");
d.speak();
d.fetch();
print(d.describe());
