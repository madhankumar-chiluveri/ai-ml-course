# 0.1 — Python Basics

**Phase 0 · CORE · CODE · 25 focused hours · Review in 7 days**

**Companion script:** [`01_python_basics.py`](01_python_basics.py) — self-contained, `python 01_python_basics.py`, no setup required.

---

## 1. Overview

Python is the language every framework in this roadmap is written in: NumPy and Pandas in **0.6**, scikit-learn across **Phase 2**, PyTorch in **3.10**, LangGraph in **Phase 6**. Nothing downstream works without it.

What matters here is **fluency, not knowledge**. You can look up syntax. What you cannot look up mid-interview is the instinct that a `for` loop building a list should have been a comprehension. That instinct makes **0.2** OOP and **0.3** type hints feel like refinements rather than new subjects.

Feeds **0.5** pytest (a test is just a function), **0.6** the scientific stack (Pandas method chaining is comprehension thinking applied to tables), and **0.9** FastAPI (every endpoint is a decorated, typed function).

---

## 2. Skip Test — Answered

> Gate **before** studying. Both correct from memory → skip the topic. Contrast with §7, whose answers are deliberately withheld.

**① Write a function that reads a CSV, filters rows where `amount` > 1000, and returns a list of dicts.**

```python
import csv
from pathlib import Path

def load_and_filter(path: Path, threshold: float = 1000) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if float(r["amount"]) > threshold]
```

Three things must be present: `with` (handle closes on exception), `DictReader` (key by name, not position), and `float()` (CSV yields strings — see the Demo 4 output below for what happens without it).

**② Write a `try/except` that catches `FileNotFoundError` and prints a custom message.**

```python
try:
    rows = load_and_filter(Path("invoices.csv"))
except FileNotFoundError:
    print("No invoice file found — create it and re-run.")
```

The load-bearing detail is that the exception is **specific**. A bare `except:` also swallows `KeyboardInterrupt` and `SystemExit`, which is how you get a process that ignores Ctrl-C.

---

## 3. Visual Concept Diagrams

### 3.1 — Comprehension desugaring

A comprehension is not different logic, it is the *same* logic reordered. The expression that was last in the loop body moves to the front.

```mermaid
flowchart LR
    subgraph Loop ["Explicit loop — 4 statements"]
        L1["out = []"] --> L2["for r in rows:"]
        L2 --> L3["if float(r['amount']) > 50000:"]
        L3 --> L4["out.append(r['invoice_id'])"]
    end

    subgraph Comp ["Comprehension — 1 expression"]
        C1["r['invoice_id']<br>the APPEND expression, moved to front"]
        C2["for r in rows"]
        C3["if float(r['amount']) > 50000"]
        C1 --- C2 --- C3
    end

    L4 -.->|"moves to position 1"| C1
    L2 -.->|"unchanged, position 2"| C2
    L3 -.->|"unchanged, position 3"| C3

    style C1 fill:#1b4332,stroke:#40916c,color:#fff
    style L4 fill:#1b4332,stroke:#40916c,color:#fff
    style L1 fill:#6b705c,stroke:#a5a58d,color:#fff
```

### 3.2 — The CSV `.get()` trap

This is the diagram worth internalising, because it contradicts the rule most people carry. `DictReader` **never gives you a missing key** — it gives you an empty string. So the `.get(key, default)` default never fires on CSV data.

```mermaid
flowchart TD
    subgraph SourceA ["Source A: CSV row missing a field"]
        A1["csv.DictWriter writes ''<br>for the absent field"]
        A2["DictReader returns:<br>{'vendor': '', 'amount': '88000'}"]
        A1 --> A2
    end

    subgraph SourceB ["Source B: LLM JSON omitting a field (4.8)"]
        B1["Model simply does not emit the key"]
        B2["Parsed dict:<br>{'amount': '42000'}"]
        B1 --> B2
    end

    A2 --> D1{"row.get('vendor', 'UNK')"}
    B2 --> D2{"row.get('vendor', 'UNK')"}

    D1 --> R1["Returns ''<br>DEFAULT DID NOT FIRE<br>key exists, value is empty"]
    D2 --> R2["Returns 'UNK'<br>DEFAULT FIRED<br>key genuinely absent"]

    R1 --> FIX["Correct idiom for CSV:<br>row.get('vendor') or 'UNK'<br>'' is falsy, so `or` catches both cases"]

    style R1 fill:#9b2226,stroke:#ae2012,color:#fff
    style R2 fill:#2d6a4f,stroke:#52b788,color:#fff
    style FIX fill:#005f73,stroke:#0a9396,color:#fff
```

### 3.3 — Why the loop is slow, and where 0.6 goes next

```mermaid
flowchart LR
    subgraph PyLoop ["Python for-loop + append"]
        P1["Interpreter bytecode<br>per iteration"] --> P2["Attribute lookup<br>out.append EVERY time"]
        P2 --> P3["~100 ms / 2M rows"]
    end

    subgraph PyComp ["List comprehension"]
        Q1["Loop machinery runs in C"] --> Q2["append resolved ONCE"]
        Q2 --> Q3["~95 ms / 2M rows<br>~1.05x — modest"]
    end

    subgraph NumPy ["NumPy boolean mask (0.6)"]
        N1["NO Python-level loop at all"] --> N2["Whole-array op in C/SIMD"]
        N2 --> N3["~4.6 ms / 2M rows<br>~22x — the real win"]
    end

    PyLoop --> PyComp --> NumPy

    style P3 fill:#9b2226,stroke:#ae2012,color:#fff
    style Q3 fill:#6b705c,stroke:#a5a58d,color:#fff
    style N3 fill:#2d6a4f,stroke:#52b788,color:#fff
```

---

## 4. Core Technical Deep Dive

| Idiom | Why it exists | Where it returns |
|---|---|---|
| `pathlib.Path` | Windows dev, Linux deploy — string paths break at the separator | **0.10**, **0.13** |
| `with` context manager | Handle closes even on exception; leaked fds are fatal in a long-lived server | **0.9** |
| List comprehension | The dominant idiom in the source you will read | **Phase 2**, **Phase 6** |
| `dict.get(k, default)` | Missing keys are a normal state in LLM JSON, not a bug | **4.8** |
| `row.get(k) or default` | **CSV-specific** — empty string is falsy, missing-key default is not enough | **2.2** |
| `defaultdict(float)` | Removes accumulator boilerplate | **2.2** feature engineering |
| Specific `except` | Bare `except` swallows `KeyboardInterrupt` | **6.14** typed errors |
| `if __name__ == "__main__"` | Makes the module importable, which pytest requires | **0.5** |

**The `float()` rule.** `csv` returns strings, always. String comparison is lexicographic, so `'9000' > '150000'` evaluates `True` — a silent, plausible-looking wrong answer rather than a crash. Demo 4 below proves it.

---

## 5. Hands-On Script & Verified Output

Run: `python 01_python_basics.py`. Output below is **actual, captured on Python 3.14.4** — not illustrative.

```text
Python 3.14.4
====================================================================
DEMO 1 — comprehension vs explicit loop: identical output
====================================================================
  loop  : ['INV-001', 'INV-003', 'INV-004', 'INV-005', 'INV-006']
  comp  : ['INV-001', 'INV-003', 'INV-004', 'INV-005', 'INV-006']
  identical? True
====================================================================
DEMO 2 — the CSV trap, then dict.get() vs dict[]
====================================================================
  csv row              : {'invoice_id': 'INV-006', 'vendor': '', 'amount': '88000', 'status': 'OPEN'}
  'vendor' in row?     : True   <- present, not missing
  .get('vendor','UNK') : ''  <- default did NOT fire
  .get('vendor') or UNK: 'UNK'  <- correct for CSV

  llm-style row        : {'invoice_id': 'INV-007', 'amount': '42000'}
  .get('vendor','UNK') : 'UNK'  <- default DID fire
  ['vendor']           : raised KeyError('vendor')
====================================================================
DEMO 3 — defaultdict removes accumulator boilerplate
====================================================================
  manual : {'Acme': 123000.0, 'Beta': 72000.0, 'Gamma': 150000.0, 'UNKNOWN': 88000.0}
  auto   : {'Acme': 123000.0, 'Beta': 72000.0, 'Gamma': 150000.0, 'UNKNOWN': 88000.0}
  identical? True
====================================================================
DEMO 4 — the silent bug: sorting numbers as strings
====================================================================
  raw from csv        : ['51000', '9000', '72000', '150000', '63000', '88000']
  sorted as strings   : ['9000', '88000', '72000', '63000', '51000', '150000']
  sorted as floats    : [150000, 88000, 72000, 63000, 51000, 9000]
  '9000' > '150000' ? True   <- lexicographic, TRUE
  ^ This is why every csv numeric field needs float() first.
====================================================================
DEMO 5 — comprehensions are also faster (preview of 0.6)
====================================================================
  rows scanned      : 2,000,000
  loop + append     :    99.8 ms
  list comprehension:    94.7 ms
  same result?      : True
  speedup           : 1.05x
  Modest — because BOTH still loop in Python.
  0.6 NumPy removes the Python-level loop entirely. Compare:
  numpy boolean mask:     4.6 ms
  speedup vs loop   : 21.8x   <- this is why 0.6 matters
  same result?      : True
====================================================================
Ranked vendor totals (the closed-book rebuild target):
  Gamma          150,000.00
  Acme           123,000.00
  UNKNOWN         88,000.00
  Beta            72,000.00
====================================================================
```

**Read Demo 4 carefully.** `'9000'` sorts *above* `'150000'` because `'9'` > `'1'` at the first character. Nothing raises. A report built on that ranking is simply wrong, and nobody notices until someone questions the numbers.

**Read Demo 5 honestly.** The comprehension is only ~1.05x faster — both still loop in Python. The 22x figure comes from NumPy removing the Python-level loop entirely. Comprehensions are for *readability*; **0.6** is where the performance argument actually lives.

**Modify and re-run** (this is the practice step, not optional):
- Change the Demo 1 threshold to `100_000` and predict the output before running.
- Delete `float()` from Demo 1's filter and predict what happens. Then run it.
- Add a row with `amount` = `"abc"` and see which demo breaks first, and how.

---

## 6. Video

**Corey Schafer — Python tutorials** — [youtube.com/@coreyms](https://www.youtube.com/@coreyms). The standard recommendation at this level: idiomatic, no filler, one topic per video.

A specific beginner-Python video title and current URL is **[VERIFY]** — the OOP series used in 0.2 was confirmed live, but an individual basics video was not verified for this pass. Search the channel directly rather than trusting a guessed link.

---

## 7. Retrieval Checkpoint — Unanswered

> Gate **after** studying. Close this file. No notes. Answers deliberately not given here.

1. Rewrite as a single comprehension: `out = []` / `for r in rows:` / `if r["status"] == "OPEN":` / `out.append(r["id"])`
2. A CSV row is missing the `vendor` column. Does `row.get("vendor", "UNKNOWN")` return `"UNKNOWN"`? Explain your answer and give the idiom that does work.
3. Why does `if __name__ == "__main__":` exist, and what specifically breaks in **0.5** without it?

---

## 8. Closed-Book Rebuild

With this file **and** the script closed, write from scratch: read a CSV of invoices, filter above a threshold using a comprehension, group totals by vendor using `defaultdict`, handle the missing-vendor case with the CSV-correct idiom, sort descending, and catch the missing-file case with a specific exception.

---

## 9. Glossary

**Comprehension** — expression-form loop producing a list, dict or set. The append-expression moves to the front. Same semantics as the loop, more idiomatic, marginally faster.

**Context manager** — object usable with `with`, guaranteeing cleanup (`__exit__`) even when the block raises. `open()` is the canonical one.

**`defaultdict`** — dict subclass calling a zero-argument factory on first access to a missing key. `defaultdict(float)` yields `0.0`, removing the "if key not in d" guard.

**Falsy** — values evaluating `False` in a boolean context: `''`, `0`, `[]`, `{}`, `None`. The reason `x or default` catches empty strings where `.get(k, default)` does not.

**Lexicographic ordering** — character-by-character string comparison. `'9000' > '150000'` is `True` because `'9' > '1'`. The cause of Demo 4's silent bug.

**Vectorization** — expressing an operation over a whole array rather than element-by-element, pushing the loop into C. Introduced in **0.6**, formalised in **1.14**.

---

## Review again in

**7 days** — low conceptual density, high mechanical familiarity. If the Closed-Book Rebuild takes under 15 minutes with no lookups, mark 0.1 done and do not revisit. The one item genuinely worth retaining is the CSV `.get()` trap from §3.2.
