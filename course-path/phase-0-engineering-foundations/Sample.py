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

word="abc"
mod=word.upper()
print(mod)
print(word.upper())

status="open"
if status == "OPEN":
    print("open")
elif status.upper() == "OVERDUE":
    print("overdue")
else:
    print("closed")

# n=[1,2,3,4,5,6]
for i in range(1,10):
    if i<3:
        continue
    elif i==5:
        break
    else:
        print(i)


numbers=[1,2,3,4,5,6,7,8,9,10]
isprime=[i for i in numbers if i>2 and i%2!=0]
print(isprime)

from collections import defaultdict

totals = defaultdict(float)
# Set a starting baseline before multiplying
totals["vendor"] = 100.0  
for i in range(1, 5):
    totals["vendor"] += totals["vendor"] * i
print(totals)

s=sorted(["10","2","1"],key=int)
print(s)

a=[1,2,3]
b=[10,20,30]
c=[]
for i in range(len(a)):
    c.append(a[i]*b[i])
print(c)

import numpy as np

a=np.array([1,2,3])
b=np.array([10,20,30])
c=a*b
print(c)
