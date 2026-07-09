# Maps (dictionaries) in ArcanisLang

person = {"name": "Alice", "age": 30, "city": "New York"}
print("Person: " + str(person))
print("Name: " + person["name"])
print("Age: " + str(person["age"]))

# Update value
person["age"] = 31
print("Updated age: " + str(person["age"]))

# Nested maps
users = {
    "alice": {"score": 95, "level": "expert"},
    "bob": {"score": 72, "level": "intermediate"}
}
print("\nUsers and scores:")
print("Alice's score: " + str(users["alice"]["score"]))
print("Bob's level: " + str(users["bob"]["level"]))
