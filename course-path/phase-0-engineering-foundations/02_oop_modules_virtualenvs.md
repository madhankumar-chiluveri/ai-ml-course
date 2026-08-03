# 0.2 — OOP, Modules, Virtual Environments

**Phase 0 · CORE · CODE · 10 focused hours · Review in 7 days**

**Companion script:** [`02_oop_modules_virtualenvs.py`](02_oop_modules_virtualenvs.py) — stdlib only, `python 02_oop_modules_virtualenvs.py`.

---

## 1. Overview

Every LangChain tool, LangGraph node and FastAPI dependency is a class or a module-level function. You cannot read framework source — which you will do constantly from **Phase 2** onward — without OOP fluency. Building on **0.1**, this adds the structure that lets code be *extended* rather than copied.

Virtual environments matter for a reason specific to this roadmap: **Phase 3** installs PyTorch against a pinned CUDA build, **Phase 2** wants a particular scikit-learn, **Phase 6** wants specific LangGraph versions. Without isolation these conflict, and the failure arrives as a cryptic import error weeks later rather than an obvious one today.

Unlocks **0.3** (Pydantic models *are* validating classes), **0.9** FastAPI, and **6.3** where LangGraph state is declared as a `TypedDict`.

---

## 2. Skip Test — Answered

> Gate **before** studying. Both correct from memory → skip. §7 withholds its answers deliberately.

**① Difference between a class attribute and an instance attribute?**

A **class attribute** is defined in the class body and stored once on the class object — every instance sees the same object. An **instance attribute** is assigned via `self.x = ...` (normally in `__init__`) and exists once per object.

The consequence that matters: a **mutable** class attribute is shared. `call_log: list = []` in the class body gives every instance *the same list*. Demo 2 below proves it — `a.call_log is b.call_log` returns `True`, and appending through one instance is visible through every other. Fix: create it per-instance in `__init__`.

**② What does `super().__init__()` do, and what breaks without it?**

It runs the parent's initialiser, which is what sets the parent's instance attributes. Skip it and those attributes never exist. Demo 3 shows the symptom: `AttributeError: 'ForgotSuper' object has no attribute 'timeout'` — raised at whatever later line happens to read it, with nothing pointing back at the real cause in `__init__`.

---

## 3. Visual Concept Diagrams

### 3.1 — Class vs instance attributes, and the shared-mutable bug

```mermaid
flowchart TD
    subgraph ClassObj ["Tool — the CLASS object, exists once"]
        CA1["name = 'unnamed'<br>immutable, safe to share"]
        CA2["call_log = []<br>MUTABLE — one list, shared by all"]
        CA3["run, __repr__<br>function objects"]
    end

    subgraph InstA ["instance a = SQLTool(...)"]
        IA1["timeout = 30.0"]
        IA2["dsn = 'oracle://a'"]
    end

    subgraph InstB ["instance b = SearchTool(...)"]
        IB1["timeout = 15.0"]
        IB2["endpoint = 'https://search'"]
    end

    InstA -->|"lookup misses locally,<br>walks up to class"| ClassObj
    InstB -->|"lookup misses locally,<br>walks up to class"| ClassObj

    IA1 -.->|"a.call_log.append()"| CA2
    IB1 -.->|"b.call_log.append()"| CA2
    CA2 --> BUG["a.call_log IS b.call_log -> True<br>Both see BOTH entries"]

    style CA2 fill:#9b2226,stroke:#ae2012,color:#fff
    style BUG fill:#9b2226,stroke:#ae2012,color:#fff
    style IA1 fill:#2d6a4f,stroke:#52b788,color:#fff
    style IB1 fill:#2d6a4f,stroke:#52b788,color:#fff
```

### 3.2 — Attribute lookup walks the MRO

```mermaid
flowchart LR
    START["t.name"] --> S1{"on the<br>INSTANCE?"}
    S1 -->|"yes"| F1["return instance value<br>shadows everything above"]
    S1 -->|"no"| S2{"on SQLTool?"}
    S2 -->|"yes"| F2["return 'sql_query'<br>shadows Tool"]
    S2 -->|"no"| S3{"on Tool?"}
    S3 -->|"yes"| F3["return 'unnamed'"]
    S3 -->|"no"| S4{"on ABC / object?"}
    S4 -->|"no"| ERR["AttributeError"]

    MRO["MRO: SQLTool -> Tool -> ABC -> object<br>the exact search order"]

    style F2 fill:#2d6a4f,stroke:#52b788,color:#fff
    style ERR fill:#9b2226,stroke:#ae2012,color:#fff
    style MRO fill:#005f73,stroke:#0a9396,color:#fff
```

### 3.3 — ABC moves the failure earlier

```mermaid
flowchart TD
    subgraph NoABC ["Without ABC — plain base class"]
        N1["BrokenTool defined,<br>run() missing"] --> N2["BrokenTool() constructs FINE"]
        N2 --> N3["Registered in a tool list"]
        N3 --> N4["Agent selects it mid-run (6.10)"]
        N4 --> N5["AttributeError in production<br>after tokens already spent"]
    end

    subgraph WithABC ["With ABC + @abstractmethod"]
        A1["BrokenTool defined,<br>run() missing"] --> A2["BrokenTool() raises TypeError<br>IMMEDIATELY"]
        A2 --> A3["Caught at import / startup<br>zero cost"]
    end

    style N5 fill:#9b2226,stroke:#ae2012,color:#fff
    style A3 fill:#2d6a4f,stroke:#52b788,color:#fff
```

---

## 4. Core Technical Deep Dive

| Concept | The failure it prevents | Where it returns |
|---|---|---|
| `ABC` + `@abstractmethod` | Incomplete subclass discovered mid-run | **6.13** tool contracts |
| `super().__init__()` | Parent attributes silently missing | Any inheritance hierarchy |
| Class vs instance attribute | Mutable state shared across all objects | Tool registries, caches |
| `__repr__` | Useless log lines in an agent trace | **7.6** tracing |
| `__init__.py` | `ModuleNotFoundError` unrelated to code correctness | **0.5** test imports |
| `venv` | PyTorch/CUDA fighting another project | **3.10**, **4.11** |

**Package layout** — the part that produces confusing import errors:

```
project/
├── pyproject.toml
├── tools/
│   ├── __init__.py      # makes `tools` an importable package
│   ├── base.py
│   └── sql.py
└── tests/
    └── test_sql.py      # `from tools.sql import SQLTool`
```

**Virtual environment** — once per project, never skipped:

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS (0.10)
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
pip freeze > requirements.txt    # EXACT versions, including transitive
```

---

## 5. Hands-On Script & Verified Output

Run: `python 02_oop_modules_virtualenvs.py`. Output below is **actual, captured**.

```text
====================================================================
DEMO 1 — ABC refuses an incomplete subclass AT CONSTRUCTION
====================================================================
  BrokenTool()  -> TypeError: Can't instantiate abstract class BrokenTool without an implementation for abstract method 'run'
  ^ Caught when building the object, NOT when an agent calls run().
  SQLTool(...)  -> SQLTool(name='sql_query', timeout=30.0)          <- __repr__ fires here
====================================================================
DEMO 2 — the classic bug: a MUTABLE class attribute is SHARED
====================================================================
  a.call_log            : ['sql_query:SELECT 1', 'web_search:langgraph docs']
  b.call_log            : ['sql_query:SELECT 1', 'web_search:langgraph docs']
  same list object?     : True
  Tool.call_log         : ['sql_query:SELECT 1', 'web_search:langgraph docs']
  ^ ONE list shared by every instance AND the class itself.
    Fix: create it per-instance in __init__ (self.call_log = []).
====================================================================
DEMO 3 — forgetting super().__init__() loses parent attributes
====================================================================
  SQLTool.timeout       : 30.0
  ForgotSuper.timeout   : AttributeError: 'ForgotSuper' object has no attribute 'timeout'
  ^ The symptom appears FAR from the cause — some later line reads
    self.timeout and blows up, with nothing pointing at __init__.
====================================================================
DEMO 4 — attribute lookup: instance -> class -> parent (the MRO)
====================================================================
  t.dsn      -> 'oracle://finance'     found on the INSTANCE
  t.name     -> 'sql_query'            found on SQLTool (shadows Tool)
  Tool.name  -> 'unnamed'              the parent's value, untouched
  MRO        : ['SQLTool', 'Tool', 'ABC', 'object']

  after t.name = 'instance_override':
  t.name       -> 'instance_override'
  SQLTool.name -> 'sql_query'   <- class value UNCHANGED
====================================================================
DEMO 5 — polymorphism: why agent frameworks take list[Tool]
====================================================================
  sql_query    times out after 30.0s
  web_search   times out after 15.0s

  all isinstance(Tool)? True
====================================================================
DEMO 6 — __repr__ decides if a log line is useful
====================================================================
  with __repr__    : SQLTool(name='sql_query', timeout=30.0)
  without __repr__ : <__main__.demo_repr_matters.<locals>.NoRepr object at 0x000001241ADE9400>
  ^ The second tells you nothing when tracing an agent run (7.6).
====================================================================
```

**Demo 2 is the one to sit with.** `a` is a `SQLTool` and `b` is a `SearchTool` — *different classes* — and they still share one list, because both inherit it from `Tool`. `a.call_log is b.call_log` → `True`. In a tool registry that accumulates call history, this is a cross-tenant data leak waiting to happen (**7.13**).

**Modify and re-run:**
- Move `call_log` into `__init__` as `self.call_log = []` and re-run Demo 2. Predict the output first.
- Add `run()` to `BrokenTool` and confirm Demo 1 stops raising.
- Add a third subclass and confirm Demo 5's `describe()` works on it **without being modified** — that is the extension mechanism in one observation.

---

## 6. Video

**"Python OOP Tutorial 1: Classes and Instances"** — *Corey Schafer* — [youtube.com/watch?v=ZDa-Z5JzLYM](https://www.youtube.com/watch?v=ZDa-Z5JzLYM). Verified live.

Full 6-part series (classes → class variables → classmethods/staticmethods → inheritance → dunder methods → property decorators): [playlist PL-osiE80TeTsqhIuOqKhwlXsIBIdSeYtc](https://www.youtube.com/playlist?list=PL-osiE80TeTsqhIuOqKhwlXsIBIdSeYtc). Parts 1, 2, 4 and 5 cover this session; 3 and 6 are optional.

---

## 7. Retrieval Checkpoint — Unanswered

> Close this file. No notes. Answers deliberately withheld.

1. You set a class attribute to `[]` and `.append()` to it from two instances of two *different* subclasses. What is in each list, and why?
2. What does `super().__init__()` do, and describe precisely where in the code the symptom of forgetting it will appear versus where the actual cause is.
3. Name a concrete dependency conflict from this roadmap that a per-project virtual environment prevents.

---

## 8. Closed-Book Rebuild

With this file **and** the script closed: create a package with `__init__.py`, define an abstract `Tool` base with one abstract method and a `__repr__`, subclass it twice with correct `super()` calls, write a function accepting the base type that works on both, and demonstrate the shared-mutable-class-attribute bug and its fix — all inside a fresh venv with a `requirements.txt`.

---

## 9. Glossary

### 9.1 — ABC (Abstract Base Class)

A blueprint class that cannot be instantiated directly and forces any subclass to implement marked `@abstractmethod`s before an object can be built.

#### 💡 The Beginner Analogy: Employment Contract
An ABC is like a strict **employment contract**. You cannot hire an employee (instantiate an object) who signed a blank contract with missing job duties (`@abstractmethod`). Python stops you the moment you attempt to create the object.

#### 🎨 Failing at Startup vs. Failing in Production

```mermaid
flowchart TD
    subgraph NoABC ["❌ Without ABC (Fails late in production)"]
        N1["BrokenTool defined (forgot run method)"] --> N2["Instantiates fine: tool = BrokenTool()"]
        N2 --> N3["Agent executes at 3 AM: tool.run('query')"]
        N3 --> N4["💥 AttributeError: 'BrokenTool' object has no attribute 'run'"]
    end

    subgraph WithABC ["✅ With ABC + @abstractmethod (Fails instantly at construction)"]
        A1["BrokenTool(Tool) (forgot run method)"] --> A2["Try tool = BrokenTool()"]
        A2 --> A3["⛔ TypeError: Can't instantiate abstract class BrokenTool..."]
    end

    style N4 fill:#9b2226,stroke:#ae2012,color:#fff
    style A3 fill:#2d6a4f,stroke:#52b788,color:#fff
```

#### 💻 Code Example
```python
from abc import ABC, abstractmethod

class BaseTool(ABC):
    @abstractmethod
    def run(self, query: str) -> str:
        pass

class BrokenTool(BaseTool):
    pass # Forgot to implement run()!

# tool = BrokenTool() 
# 💥 TypeError: Can't instantiate abstract class BrokenTool without an implementation for abstract method 'run'
```

---

### 9.2 — Class Attribute vs. Instance Attribute

- **Class Attribute**: Defined directly in the class body; stored **once** on the class object and **shared by all instances**.
- **Instance Attribute**: Defined on `self` (usually inside `__init__`); unique copy per object instance.

#### 💡 The Beginner Analogy: Hallway Whiteboard vs. Desk Notepad
- **Class Attribute**: A whiteboard in the office hallway. If Employee A writes a note on it, Employee B sees it too!
- **Instance Attribute**: A personal notebook inside Employee A's private desk drawer.

#### 🎨 The Shared Mutable Attribute Bug

```mermaid
flowchart TD
    subgraph ClassLevel ["Tool Class Object (Shared)"]
        CLASS_NAME["name = 'unnamed' (Immutable, safe to share)"]
        CLASS_LOG["call_log = [] (MUTABLE — SHARED WHITEBOARD!)"]
    end

    subgraph InstA ["Instance a (SQLTool)"]
        A_DSN["self.dsn = 'oracle://a'"]
    end

    subgraph InstB ["Instance b (SearchTool)"]
        B_END["self.endpoint = 'https://search'"]
    end

    InstA -->|"a.call_log.append('SELECT 1')"| CLASS_LOG
    InstB -->|"b.call_log.append('search py')"| CLASS_LOG
    CLASS_LOG --> BUG["💥 Cross-Tenant Data Leak!<br>a.call_log IS b.call_log -> True<br>Both instances see BOTH entries!"]

    style CLASS_LOG fill:#9b2226,stroke:#ae2012,color:#fff
    style BUG fill:#9b2226,stroke:#ae2012,color:#fff
    style A_DSN fill:#2d6a4f,stroke:#52b788,color:#fff
    style B_END fill:#2d6a4f,stroke:#52b788,color:#fff
```

#### 💻 Code Example & Fix
```python
# ❌ BUG: Mutable class attribute shared across ALL instances
class Tool:
    call_log: list[str] = [] # Shared list!

# ✅ FIX: Create mutable attributes inside __init__ per instance
class Tool:
    def __init__(self) -> None:
        self.call_log: list[str] = [] # Private list per instance
```

---

### 9.3 — MRO (Method Resolution Order)

The exact linear sequence of classes Python searches when looking up an attribute or method on an object.

#### 💡 The Beginner Analogy: Searching for Misplaced Keys
When searching for your keys:
1. Check your **pockets** (Instance attributes `self.x`).
2. Check your **bedroom** (The child class `SQLTool`).
3. Check the **living room** (The parent base class `Tool`).
4. Check the **house foundation** (`ABC` / `object`).

Python searches in this exact order and stops at the very **first** location where it finds the attribute!

#### 🎨 Attribute Lookup Path

```mermaid
flowchart LR
    LOOKUP["t.name"] --> STEP1{"1. On Instance (t)?"}
    STEP1 -->|"Yes"| RET1["Return instance value"]
    STEP1 -->|"No"| STEP2{"2. On Child Class (SQLTool)?"}
    STEP2 -->|"Yes"| RET2["Return 'sql_query'"]
    STEP2 -->|"No"| STEP3{"3. On Base Class (Tool)?"}
    STEP3 -->|"Yes"| RET3["Return 'unnamed'"]
    STEP3 -->|"No"| STEP4{"4. On ABC / object?"}
    STEP4 -->|"No"| ERR["💥 AttributeError"]

    style RET1 fill:#2d6a4f,stroke:#52b788,color:#fff
    style RET2 fill:#2d6a4f,stroke:#52b788,color:#fff
    style ERR fill:#9b2226,stroke:#ae2012,color:#fff
```

#### 💻 How to view MRO in code
```python
print(SQLTool.__mro__)
# Output: (<class 'SQLTool'>, <class 'Tool'>, <class 'abc.ABC'>, <class 'object'>)
```

---

### 9.4 — Shadowing

Creating an instance attribute with the same name as a class attribute. The instance attribute hides ("shadows") the class value for that specific object without altering the class default for other objects.

#### 💡 The Beginner Analogy: Door Sticky Note
Placing a sticky note over a printed office room sign. The sticky note covers up the printed text for anyone looking at that specific door (the instance), but the original printed sign underneath (the class) remains unchanged for everyone else!

#### 🎨 Shadowing Mechanism

```mermaid
flowchart TD
    subgraph ClassLevel ["Class Definition (Tool)"]
        C_VAL["Tool.name = 'unnamed'"]
    end

    subgraph InstanceLevel ["Instance (t)"]
        I_VAL["t.name = 'instance_override'<br>(Shadows Tool.name)"]
    end

    READ_T["Read t.name"] --> I_VAL
    READ_CLASS["Read Tool.name"] --> C_VAL

    style I_VAL fill:#2d6a4f,stroke:#52b788,color:#fff
    style C_VAL fill:#005f73,stroke:#0a9396,color:#fff
```

#### 💻 Code Example
```python
t = SQLTool()
t.name = "my_custom_sql"  # Assigning on instance creates an instance attribute!

print(t.name)         # -> 'my_custom_sql' (Found on instance)
print(SQLTool.name)   # -> 'sql_query'       (Class value UNCHANGED!)
```

---

### 9.5 — Polymorphism

Designing functions to accept a general base class (`Tool`), enabling any present or future subclass (`SQLTool`, `SearchTool`, `APITool`) to be passed in and executed without modifying the caller.

#### 💡 The Beginner Analogy: Universal USB-C Port
A laptop's USB-C port doesn't care whether you plug in a mouse, keyboard, or flash drive. As long as the device adheres to the USB standard protocol, the laptop interacts with it seamlessly.

#### 🎨 Framework Polymorphism in Action

```mermaid
flowchart TD
    FRAMEWORK["Agent Framework / Tool Registry"] -->|"Calls describe(tool: Tool)"| CONTRACT["Abstract Base: Tool"]
    CONTRACT --> IMPL1["SQLTool (runs SQL queries)"]
    CONTRACT --> IMPL2["SearchTool (runs Web searches)"]
    CONTRACT --> IMPL3["NewCustomTool (Built next month!)"]

    style CONTRACT fill:#005f73,stroke:#0a9396,color:#fff
    style FRAMEWORK fill:#2d6a4f,stroke:#52b788,color:#fff
```

#### 💻 Code Example
```python
def describe_tool(tool: Tool) -> str:
    # Written ONCE. Works for SQLTool, SearchTool, and tools not created yet!
    return f"{tool.name} (Timeout: {tool.timeout}s)"

tools: list[Tool] = [SQLTool(), SearchTool()]
for t in tools:
    print(describe_tool(t))
```

---

### 9.6 — `__init__.py`

A special configuration file placed inside a directory to signal to Python's import engine that the folder should be treated as an importable package.

#### 💡 The Beginner Analogy: Passport Entry Permit
Without `__init__.py`, Python treats a folder full of files as just a plain file system directory, refusing to let other Python modules import code from inside it. `__init__.py` acts as the passport entry stamp.

#### 🎨 Directory Structure
```
my_project/
├── tools/
│   ├── __init__.py    <-- 🔑 Entry Permit! Makes `tools` an importable package
│   ├── base.py
│   └── sql.py
└── main.py            <-- Imports via: `from tools.sql import SQLTool`
```

#### ⚠️ Why It Matters
Forgetting `__init__.py` causes `ModuleNotFoundError` errors when structuring multi-file projects, test suites, or modular libraries.

---

### 9.7 — venv (Virtual Environment)

An isolated sandbox directory per project containing its own Python executable and `site-packages` folder.

#### 💡 The Beginner Analogy: Private Toolboxes
Installing Python packages globally is like throwing all your tools onto **one shared workbench**:
- **Project A** requires `pandas==1.5.3`.
- **Project B** upgrades the workbench to `pandas==2.2.0`.
- **Project A breaks** because its required version was overwritten!

A **Virtual Environment** gives every project its own **private toolbox** containing the exact package versions it needs, completely isolated from system Python and other projects.

#### 🎨 Global Python vs. Isolated Virtual Environments

```mermaid
flowchart TD
    subgraph GlobalSystem ["❌ Global Python (Shared Workbench)"]
        SYS_PY["System Python (Global)"]
        SYS_PKGS["Global site-packages"]
        PROJ_A1["Project A (wants pandas 1.5)"] --> SYS_PKGS
        PROJ_B1["Project B (wants pandas 2.2)"] --> SYS_PKGS
        SYS_PKGS --> CONFLICT["💥 Overwritten Package & Production Crash!"]
    end

    subgraph IsolatedVenv ["✅ Virtual Environments (Private Toolboxes)"]
        subgraph VENV_A ["Project A Sandbox (.venv/)"]
            PY_A["Isolated python"]
            PKG_A["site-packages: pandas 1.5"]
        end
        subgraph VENV_B ["Project B Sandbox (.venv/)"]
            PY_B["Isolated python"]
            PKG_B["site-packages: pandas 2.2"]
        end
        PROJ_A2["Project A"] --> VENV_A
        PROJ_B2["Project B"] --> VENV_B
    end

    style CONFLICT fill:#9b2226,stroke:#ae2012,color:#fff
    style VENV_A fill:#2d6a4f,stroke:#52b788,color:#fff
    style VENV_B fill:#005f73,stroke:#0a9396,color:#fff
```

#### ⚙️ How it works under the hood
1. **Creation** (`python -m venv .venv`): Creates a `.venv/` folder containing local binaries (`python`, `pip`) and a fresh `site-packages/` directory.
2. **Activation** (`source .venv/bin/activate` or `.\.venv\Scripts\Activate.ps1`): Prepends `.venv` to your OS environment `PATH` variable so running `python` or `pip` automatically resolves to the local `.venv`.
3. **Deactivation** (`deactivate`): Restores your terminal's original system `PATH`.

---

## Review again in

**7 days** — mostly mechanical, but the shared-mutable-class-attribute result from Demo 2 is a genuine interview question and worth one spaced repetition.
