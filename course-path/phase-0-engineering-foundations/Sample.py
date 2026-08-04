for fruit in ["apple", "banana", "cherry"]:
    print(fruit)

# range(start, stop, step) — stop is exclusive
for i in range(0, 10, 2):
    print(i)    # 0, 2, 4, 6, 8

# enumerate — get index + value
for i, fruit in enumerate(["apple", "banana"]):
    print(f"{i}: {fruit}")

print(list(enumerate(["apple", "banana"])))

a=["A","B","C"]
b=[1,2,3]
for a,b in zip(a,b):
    print(f"{a} {b}")

