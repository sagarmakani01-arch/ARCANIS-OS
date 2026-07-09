# Control flow examples

# If-elif-else
score = 85
if score >= 90:
    print("Grade: A")
elif score >= 80:
    print("Grade: B")
elif score >= 70:
    print("Grade: C")
else:
    print("Grade: F")

# While loop
count = 5
while count > 0:
    print("Countdown: " + str(count))
    count = count - 1

# For loop
print("Numbers 0 to 4:")
for i in range(5):
    print("  " + str(i))

# Break and continue
print("Even numbers up to 10:")
for i in range(10):
    if i % 2 == 0:
        print("  " + str(i))
