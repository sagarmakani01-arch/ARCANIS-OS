# Tutorial 6: Classes and Objects

Classes let you create your own data types.

## Defining a Class

```arcanis
class Animal:
    fun init(self, name):
        self.name = name

    fun speak(self):
        return self.name + " makes a sound"
```

## Creating Objects

```arcanis
animal = Animal("Generic")
print(animal.speak())
```

## Adding More Methods

```arcanis
class Dog:
    fun init(self, name, breed):
        self.name = name
        self.breed = breed

    fun bark(self):
        return self.name + " says Woof!"

    fun describe(self):
        return self.name + " is a " + self.breed

dog = Dog("Rex", "Golden Retriever")
print(dog.bark())
print(dog.describe())
```

## Inheritance

```arcanis
class Puppy(Dog):
    fun init(self, name, breed, toy):
        self.name = name
        self.breed = breed
        self.toy = toy

    fun play(self):
        return self.name + " plays with " + self.toy

puppy = Puppy("Max", "Beagle", "ball")
print(puppy.bark())
print(puppy.play())
```

## Key Points
- `class` defines a new type
- `self` refers to the current instance
- `__init__` is the constructor (actually `init`)
- Parent classes go in parentheses
