"""
0.1 — Python Basics: the idioms framework source code assumes.

Self-contained and runnable: `python 01_python_basics.py`
Creates its own sample data, so there is nothing to download or set up.
"""

import csv
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

SEP = "=" * 68

def make_sample_csv() -> Path:
    rows = [
        {"invoice_id": "INV-001", "vendor": "Acme",  "amount": "51000", "status": "OPEN"},
        {"invoice_id": "INV-002", "vendor": "Beta",  "amount": "9000",  "status": "PAID"},
        {"invoice_id": "INV-003", "vendor": "Acme",  "amount": "72000", "status": "OVERDUE"},
        {"invoice_id": "INV-004", "vendor": "Gamma", "amount": "150000", "status": "OPEN"},
        {"invoice_id": "INV-005", "vendor": "Beta",  "amount": "63000", "status": "OPEN"},
        {"invoice_id": "INV-006", "amount": "88000", "status": "OPEN"},
    ]
    path = Path(tempfile.gettempdir()) / "invoices_demo.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["invoice_id", "vendor", "amount", "status"])
        writer.writeheader()
        writer.writerows(rows)
    return path

def load_invoices(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def demo_01_variables() -> None:
    print(SEP)
    print("DEMO 1 — Variables (No type declaration needed, Python infers)")
    print(SEP)
    x_int = 10
    x_float = 10.0
    print(f"  x = 10   -> {type(x_int).__name__}")
    print(f"  x = 10.0 -> {type(x_float).__name__}")

def demo_02_strings() -> None:
    print(SEP)
    print("DEMO 2 — Strings (Immutable, every method returns a new string)")
    print(SEP)
    original = "hello"
    modified = original.upper()
    print(f"  original string : {original!r}")
    print(f"  after .upper()  : {original!r}  <- unchanged")
    print(f"  returned string : {modified!r}")

def demo_03_fstrings() -> None:
    print(SEP)
    print("DEMO 3 — f-strings (The modern string formatting)")
    print(SEP)
    vendor = "Acme"
    amount = 51000
    bad_fstring = "{vendor} owes {amount}"
    good_fstring = f"{vendor} owes {amount:,}"
    print(f"  Forgot 'f' prefix : {bad_fstring!r}")
    print(f"  Correct f-string  : {good_fstring!r}")

def demo_04_conditionals() -> None:
    print(SEP)
    print("DEMO 4 — Conditionals (if / elif / else)")
    print(SEP)
    status = "OVERDUE"
    print(f"  status is {status!r}")
    if status == "OPEN":
        print("  -> Invoice is open.")
    elif status == "OVERDUE":
        print("  -> ALERT: Invoice is overdue!")
    else:
        print("  -> Invoice is paid or unknown.")

def demo_05_loops() -> None:
    print(SEP)
    print("DEMO 5 — Loops (for / break / continue)")
    print(SEP)
    nums = [10, 15, -1, 20]
    for n in nums:
        if n < 0:
            print(f"  Encountered {n}, skipping (continue).")
            continue
        print(f"  Processing {n}")

def demo_06_lists() -> None:
    print(SEP)
    print("DEMO 6 — Lists (Ordered, mutable, allows duplicates)")
    print(SEP)
    lst = [3, 1, 2]
    result = lst.sort()
    print(f"  list.sort() ret: {result}  <- returns None!")
    print(f"  mutated list   : {lst}  <- sorted in-place")

def demo_07_slicing() -> None:
    print(SEP)
    print("DEMO 7 — Slicing ([start:stop:step])")
    print(SEP)
    seq = [0, 1, 2, 3, 4, 5]
    print(f"  seq[1:4] : {seq[1:4]}  <- excludes stop index 4")
    print(f"  seq[::-1]: {seq[::-1]}  <- reverses the list")

def demo_08_tuples() -> None:
    print(SEP)
    print("DEMO 8 — Tuples (Ordered, immutable, single element trap)")
    print(SEP)
    trap_tuple = (42)
    correct_tuple = (42,)
    print(f"  (42)  type is : {type(trap_tuple).__name__}")
    print(f"  (42,) type is : {type(correct_tuple).__name__}")

def demo_09_dicts() -> None:
    print(SEP)
    print("DEMO 9 — Dicts (Key-value pairs, hashable keys only)")
    print(SEP)
    valid_dict = {("INV", 101): "OPEN"}
    print(f"  Tuple as key  : {valid_dict}")
    try:
        invalid_dict = {["INV", 101]: "OPEN"}
    except TypeError as e:
        print(f"  List as key   : raised TypeError({e})")

def demo_10_sets() -> None:
    print(SEP)
    print("DEMO 10 — Sets (Unordered, unique elements, O(1) lookup)")
    print(SEP)
    raw_list = ["apple", "banana", "apple", "orange"]
    unique_set = set(raw_list)
    print(f"  deduplicated  : {sorted(list(unique_set))}  <- duplicates removed")
    print(f"  'apple' in set: {'apple' in unique_set}  <- O(1) check")

def demo_11_functions() -> None:
    print(SEP)
    print("DEMO 11 — Functions & Arguments (*args, **kwargs)")
    print(SEP)
    def my_func(*args, **kwargs):
        print(f"  args  : {args}")
        print(f"  kwargs: {kwargs}")
    my_func(1, 2, name="Acme", status="OPEN")

def demo_12_exceptions() -> None:
    print(SEP)
    print("DEMO 12 — Exception Handling (try / except / finally)")
    print(SEP)
    try:
        1 / 0
    except ZeroDivisionError as e:
        print(f"  Caught specific error: {type(e).__name__}")
    finally:
        print("  Cleanup happens regardless of errors.")

def demo_13_comprehensions(rows: list[dict]) -> None:
    print(SEP)
    print("DEMO 13 — Comprehensions (vs explicit loop)")
    print(SEP)
    loop_result = []
    for r in rows:
        if float(r.get("amount", 0)) > 50_000:
            loop_result.append(r["invoice_id"])
    comp_result = [r["invoice_id"] for r in rows if float(r.get("amount", 0)) > 50_000]
    print(f"  loop  : {loop_result}")
    print(f"  comp  : {comp_result}")
    print(f"  identical? {loop_result == comp_result}")

def demo_14_context_managers() -> None:
    print(SEP)
    print("DEMO 14 — Context Managers (with guarantees cleanup)")
    print(SEP)
    path = Path(tempfile.gettempdir()) / "test_file.txt"
    with path.open("w") as f:
        f.write("test")
    print(f"  File created. After 'with' block, f.closed is: {f.closed}")

def demo_15_defaultdict(rows: list[dict]) -> None:
    print(SEP)
    print("DEMO 15 — defaultdict (removes accumulator boilerplate)")
    print(SEP)
    auto: dict[str, float] = defaultdict(float)
    for r in rows:
        auto[r.get("vendor") or "UNKNOWN"] += float(r["amount"])
    print(f"  auto totals : {dict(auto)}")

def demo_16_falsy(rows: list[dict]) -> None:
    print(SEP)
    print("DEMO 16 — Falsy / .get() (The CSV empty string trap)")
    print(SEP)
    csv_row = rows[-1]
    print(f"  csv row              : {csv_row}")
    print(f"  .get('vendor','UNK') : {csv_row.get('vendor', 'UNK')!r}  <- default did NOT fire")
    print(f"  .get('vendor') or UNK: {csv_row.get('vendor') or 'UNK'!r}  <- correct for CSV")

def demo_17_lexicographic(rows: list[dict]) -> None:
    print(SEP)
    print("DEMO 17 — Lexicographic Ordering (Sorting numbers as strings)")
    print(SEP)
    amounts_str = [r["amount"] for r in rows]
    wrong = sorted(amounts_str, reverse=True)
    right = sorted((float(a) for a in amounts_str), reverse=True)
    print(f"  sorted as strings   : {wrong}")
    print(f"  sorted as floats    : {[int(x) for x in right]}")
    print(f"  '9000' > '150000' ? {'9000' > '150000'}   <- TRUE!")

def demo_18_vectorization() -> None:
    print(SEP)
    print("DEMO 18 — Vectorization (Preview of 0.6)")
    print(SEP)
    big = list(range(2_000_000))
    t0 = time.perf_counter()
    out2 = [x for x in big if x > 1_000_000]
    t_comp = time.perf_counter() - t0
    print(f"  rows scanned      : {len(big):,}")
    print(f"  list comprehension: {t_comp*1000:7.1f} ms")
    try:
        import numpy as np
        arr = np.arange(2_000_000)
        t0 = time.perf_counter()
        out3 = arr[arr > 1_000_000]
        t_np = time.perf_counter() - t0
        print(f"  numpy mask        : {t_np*1000:7.1f} ms")
        print(f"  speedup vs comp   : {t_comp/t_np:.1f}x")
    except ImportError:
        print("  numpy not installed.")

def demo_19_generators() -> None:
    print(SEP)
    print("DEMO 19 — Generators (Lazy iteration, can only iterate once)")
    print(SEP)
    gen = (x * 2 for x in range(3))
    print(f"  first iteration : {list(gen)}")
    print(f"  second iteration: {list(gen)}  <- exhausted, yields nothing!")

def demo_20_decorators() -> None:
    print(SEP)
    print("DEMO 20 — Decorators (Wrap function behavior)")
    print(SEP)
    def log_call(func):
        def wrapper(*args, **kwargs):
            print(f"  [LOG] Calling {func.__name__}...")
            return func(*args, **kwargs)
        return wrapper
    
    @log_call
    def process_invoice():
        print("  Processing...")
    process_invoice()

def demo_21_typehints() -> None:
    print(SEP)
    print("DEMO 21 — Type hints (Documentation, not enforcement)")
    print(SEP)
    def add_numbers(a: int, b: int) -> int:
        return a + b
    result = add_numbers("hello", " world")
    print(f"  add_numbers('hello', ' world') -> {result!r}")

def demo_22_if_name() -> None:
    print(SEP)
    print("DEMO 22 — if __name__ == '__main__': (Makes scripts importable)")
    print(SEP)
    print(f"  Current __name__ is: {__name__!r}")

def main() -> None:
    print(f"Python {sys.version.split()[0]}")
    path = make_sample_csv()
    try:
        rows = load_invoices(path)
    except FileNotFoundError:
        return

    demo_01_variables()
    demo_02_strings()
    demo_03_fstrings()
    demo_04_conditionals()
    demo_05_loops()
    demo_06_lists()
    demo_07_slicing()
    demo_08_tuples()
    demo_09_dicts()
    demo_10_sets()
    demo_11_functions()
    demo_12_exceptions()
    demo_13_comprehensions(rows)
    demo_14_context_managers()
    demo_15_defaultdict(rows)
    demo_16_falsy(rows)
    demo_17_lexicographic(rows)
    demo_18_vectorization()
    demo_19_generators()
    demo_20_decorators()
    demo_21_typehints()
    demo_22_if_name()

if __name__ == "__main__":
    main()
