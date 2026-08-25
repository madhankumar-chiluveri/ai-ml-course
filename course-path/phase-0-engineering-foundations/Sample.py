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




# import os
# from dotenv import load_dotenv
# from google import genai

# load_dotenv()  # Loads GEMINI_API_KEY from .env file

# client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# interaction = client.interactions.create(
#     agent="antigravity-preview-05-2026",
#     input="Tell me about Something",
#     environment="remote",
# )

# # Print the agent's final output
# print(f"Interaction ID: {interaction.id}")
# print(f"Environment ID: {interaction.environment_id}")
# print(f"Output: {interaction.output_text}")


# def movie(title):
#     prompt=f'''Tell me about the movie like main cast of {title} and the result is in bullet points'''
#     try:
#         response=client.models.generate_content(
#             model="gemini-3.5-flash",
#             contents=prompt,
#         )
#         return response.text
#     except Exception as e:
#         return e

# response=movie("Predestination")
# print(f"Output: {response}")


class Employee:
    company="Google"

    def __init__(self,name:str,salary:int):
        self.name=name
        self.salary=salary

e1=Employee("A",10000)
e2=Employee("B",20000)
print(e1.salary)
e1.salary=30000

print(e1.company)
print(e2.company)
print(e1.salary)
print(e2.salary)




class A:
    def show(self):
        print("Class A")

class B(A):
    def show(self):
        # print("Class B")
        super().show()

class C(A):
    def show(self):
        print("Class C")

class D(B, C):
     print("Class D")

d = D()
d.show()  # Which show() gets called?


class Dog:
    def speak(self) -> str:
        return "Woof!"

class Cat:
    def speak(self) -> str:
        return "Meow!"

class Duck:
    def speak(self) -> str:
        return "Quack!"


# Single function demonstrating Polymorphism
def make_animal_speak(animal):
    # It doesn't matter if 'animal' is a Dog, Cat, or Duck.
    # As long as it has a .speak() method, it works!
    print(animal.speak())


# Calling the exact same function with different object types
make_animal_speak(Dog())   # Output: Woof!
make_animal_speak(Cat())   # Output: Meow!
make_animal_speak(Duck())  # Output: Quack!



class users:
    def __init__(self,username):
        self.username=username
    
    def __repr__(self):
        return f"User({self.username!r})"

U=users("Rohith")
print(users("Rohith"))


class A:
    def __init__(self):
        print("Class A")

class B(A):
    def __init__(self):
        print("Class B")
        super().__init__()

class C(A):
    def __init__(self):
        print("Class C")
        super().__init__()

class D(B, C):
    def __init__(self):
        print("Class D")
        super().__init__()

d = D()
print(d)


import asyncio
import time

async def fetch_user(user_id: int):
    print(f"Fetching user {user_id}...")
    await asyncio.sleep(2)  # Simulates network request delay
    print(f"Received user {user_id}")
    return f"User_{user_id}"

async def main():
    start_time = time.time()
    
    # Run all 3 coroutines concurrently in the event loop
    #Non Blocking
    results = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3)
    )
    
    elapsed = time.time() - start_time
    print(f"\nAll results: {results}")
    print(f"Total time taken: {elapsed:.2f} seconds")

# Run the event loop
asyncio.run(main())


import asyncio

async def fetch_data():
    print("Start")
    await asyncio.sleep(2)
    print("Got it")
    return "Here is Result"

async def main():
    try:
        result=await asyncio.wait_for(asyncio.shield(fetch_data()),timeout=2.9)
        print(result)
    except asyncio.TimeoutError:
        print("Timeout Error")

asyncio.run(main())


# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ValidationError, field_validator

class UserRegistration(BaseModel):
    username: str
    age: int

    # 1. Custom Field Validator
    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if len(value) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not value.isalnum():
            raise ValueError("Username must contain only letters and numbers")
        return value.lower()  # Transforms and normalizes data

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: int) -> int:
        if value < 18:
            raise ValueError("User must be at least 18 years old")
        return value

user = UserRegistration(username="Alice99", age=25)
print(user.username)  # Output: 'alice99' (normalized to lowercase)
print(user.age)       # Output: 25


def add(a:int,b:int):
    return a+b

def div(a:int,b:int):
    if b==0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a/b


class UserManager:
    def __init__(self):
        self.users={}

    def add_user(self,username,email):
        if username in self.users:
            raise ValueError("User already exists")
        self.users[username]=email
        return True

    def get_user(self,username):
        return self.users.get(username)

    def delete_user(self,username):
        if username not in self.users:
            raise ValueError("User not found")
        del self.users[username]
        return True

    def update_user(self,username,email):
        if username not in self.users:
            raise ValueError("User not found")
        self.users[username]=email
        return True

    def list_users(self):
        return self.users