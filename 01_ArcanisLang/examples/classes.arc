# Classes and objects in ArcanisLang

class Person:
    fun init(self, name, age):
        self.name = name
        self.age = age

    fun greet(self):
        return "Hi, I'm " + self.name + " and I'm " + str(self.age)

    fun birthday(self):
        self.age = self.age + 1
        return "Happy birthday, " + self.name + "!"

# Create instances
alice = Person("Alice", 30)
bob = Person("Bob", 25)

print(alice.greet())
print(bob.greet())
print(alice.birthday())
print("Alice is now " + str(alice.age))

# Class inheritance
class Student(Person):
    fun init(self, name, age, subject):
        self.name = name
        self.age = age
        self.subject = subject

    fun study(self):
        return self.name + " is studying " + self.subject

student = Student("Charlie", 20, "Computer Science")
print(student.greet())
print(student.study())
