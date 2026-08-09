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


# pyrefly: ignore [missing-import]
import numpy as np

a=np.array([1,2,3])
b=np.array([10,20,30])
c=a*b
print(c)

g=(i*5 for i in range(3))
print(list(g))
print(list(g))

def add(a: int): print(f'{a}')
add("str")




# Rewrite as a single comprehension:
#  out = [] / for r in rows: / if r["status"] == "OPEN": / out.append(r["id"])

# rows = [
#     {"id": 101, "status": "OPEN"},
#     {"id": 102, "status": "CLOSED"},
#     {"id": 103, "status": "OPEN"},
# ]
# out=[]
# out[] = [r["id"] for r in rows if r["status"] == "OPEN" out.append(r["id"])]
# print(out)


rows = [
    {"id": 101, "status": "OPEN"},
    {"id": 102, "status": "CLOSED"},
    {"id": 103, "status": "OPEN"},
]

# Correct List Comprehension
out = [r["id"] for r in rows if r["status"] == "OPEN"]

print(out)



financials=[
    {"rev":50,"exp":10},
    {"rev":100,"exp":50},
        {"rev":10,"exp":20}
]

for i in financials:
    i["profit"]=i["rev"]-i["exp"]
    i["margin"]=i["profit"]*100/i["rev"]

print(f"financials: {financials}")

def addition(*args):
    return sum(args)

print(addition(1,2,3,4,5))


def cal_add(**kwargs):
    for key,value in kwargs.items():
        print(f"{key}: {value}")

cal_add(a=1,b=2,c=3,d=4,e=5)


def test(*args,**kwargs):
    print(sum(args))
    print(sum(kwargs.values()))

test(1,2,3,4,5,a=1,b=2,c=3,d=4,e=5)


class YoutubeChannel:
    def __init__(self,name):
        self.name=name
        self.subscribers=0

    def subscribe(self):
        self.subscribers+=1
        print(f"Thanks for subscribing! Total: {self.subscribers}")

    def unsubscribe(self):
        if self.subscribers>0:
            self.subscribers-=1
            print(f"Thanks for unsubscribing! Total: {self.subscribers}")
        else:
            print("No subscribers to unsubscribe")

    def show(self):
        print(f"{self.name} has {self.subscribers} subscribers")
    
Result=YoutubeChannel("Tech")
Result.show()
Result.subscribe()
Result.subscribe()
Result.unsubscribe()
Result.unsubscribe()
Result.unsubscribe()
Result.show()




import os
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# interaction = client.interactions.create(
#     agent="antigravity-preview-05-2026",
#     input="Tell me about Something",
#     environment="remote",
# )

# # Print the agent's final output
# print(f"Interaction ID: {interaction.id}")
# print(f"Environment ID: {interaction.environment_id}")
# print(f"Output: {interaction.output_text}")


def movie(title):
    prompt=f'''Tell me about the movie like main cast of {title} and the result is in bullet points'''
    try:
        response=client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return e

response=movie("Predestination")
print(f"Output: {response}")