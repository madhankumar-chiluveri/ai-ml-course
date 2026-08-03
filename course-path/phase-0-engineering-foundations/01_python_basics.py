"""
0.1 — Python Basics: the idioms framework source code assumes.

Self-contained and runnable: `python 01_python_basics.py`
Creates its own sample data, so there is nothing to download or set up.

What this proves practically:
  1. A comprehension and an explicit loop produce IDENTICAL output.
  2. dict.get() survives a missing key where dict[] raises.
  3. defaultdict removes accumulator boilerplate.
  4. Naive string sorting of numbers is WRONG — a real, silent bug.
  5. A specific `except` catches; a bare `except` would also swallow Ctrl-C.
"""

import csv
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

SEP = "=" * 68


def make_sample_csv() -> Path:
    """Write a throwaway CSV so this script needs no external files."""
    rows = [
        {"invoice_id": "INV-001", "vendor": "Acme",  "amount": "51000", "status": "OPEN"},
        {"invoice_id": "INV-002", "vendor": "Beta",  "amount": "9000",  "status": "PAID"},
        {"invoice_id": "INV-003", "vendor": "Acme",  "amount": "72000", "status": "OVERDUE"},
        {"invoice_id": "INV-004", "vendor": "Gamma", "amount": "150000", "status": "OPEN"},
        {"invoice_id": "INV-005", "vendor": "Beta",  "amount": "63000", "status": "OPEN"},
        # No "vendor" key at all — exercises dict.get() vs dict[]
        {"invoice_id": "INV-006", "amount": "88000", "status": "OPEN"},
    ]
    path = Path(tempfile.gettempdir()) / "invoices_demo.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["invoice_id", "vendor", "amount", "status"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def load_invoices(path: Path) -> list[dict]:
    # `with` closes the handle even if parsing raises. In a long-lived
    # FastAPI process (0.9) leaked handles eventually exhaust the fd limit.
    with path.open(newline="", encoding="utf-8") as fh:
        # DictReader keys by header row, so downstream reads row["amount"]
        # instead of row[2]. Positional indexing breaks the day a column moves.
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- DEMO 1
def demo_comprehension_equivalence(rows: list[dict]) -> None:
    print(SEP)
    print("DEMO 1 — comprehension vs explicit loop: identical output")
    print(SEP)

    # The way most self-taught Python is written.
    loop_result = []
    for r in rows:
        if float(r.get("amount", 0)) > 50_000:
            loop_result.append(r["invoice_id"])

    # The way library source code is written. Same result, one line.
    comp_result = [r["invoice_id"] for r in rows if float(r.get("amount", 0)) > 50_000]

    print(f"  loop  : {loop_result}")
    print(f"  comp  : {comp_result}")
    print(f"  identical? {loop_result == comp_result}")


# ---------------------------------------------------------------- DEMO 2
def demo_get_vs_bracket(rows: list[dict]) -> None:
    print(SEP)
    print("DEMO 2 — the CSV trap, then dict.get() vs dict[]")
    print(SEP)

    # --- Part A: the trap. INV-006 had NO vendor field in the source rows,
    # but DictReader does NOT give you a missing key — it gives you ''.
    # So a .get() default NEVER FIRES on CSV data. This surprises everyone
    # once, and it is why `r.get("vendor") or "UNKNOWN"` (with `or`) is the
    # correct idiom for CSV, not `r.get("vendor", "UNKNOWN")`.
    csv_row = rows[-1]
    print(f"  csv row              : {csv_row}")
    print(f"  'vendor' in row?     : {'vendor' in csv_row}   <- present, not missing")
    print(f"  .get('vendor','UNK') : {csv_row.get('vendor', 'UNK')!r}  <- default did NOT fire")
    print(f"  .get('vendor') or UNK: {csv_row.get('vendor') or 'UNK'!r}  <- correct for CSV")

    # --- Part B: a genuinely absent key, e.g. parsed JSON from an LLM (4.8)
    # where the model simply omitted a field.
    llm_row = {"invoice_id": "INV-007", "amount": "42000"}
    print(f"\n  llm-style row        : {llm_row}")
    print(f"  .get('vendor','UNK') : {llm_row.get('vendor', 'UNK')!r}  <- default DID fire")
    try:
        print(llm_row["vendor"])
    except KeyError as e:
        # Catch the SPECIFIC exception. A bare `except:` would also swallow
        # KeyboardInterrupt and SystemExit, making a hung process unkillable.
        print(f"  ['vendor']           : raised KeyError({e})")


# ---------------------------------------------------------------- DEMO 3
def demo_defaultdict(rows: list[dict]) -> None:
    print(SEP)
    print("DEMO 3 — defaultdict removes accumulator boilerplate")
    print(SEP)

    manual: dict[str, float] = {}
    for r in rows:
        v = r.get("vendor") or "UNKNOWN"
        if v not in manual:          # <- the boilerplate defaultdict deletes
            manual[v] = 0.0
        manual[v] += float(r["amount"])

    auto: dict[str, float] = defaultdict(float)
    for r in rows:
        # float() is called on FIRST access, yielding 0.0 automatically.
        auto[r.get("vendor") or "UNKNOWN"] += float(r["amount"])

    print(f"  manual : {manual}")
    print(f"  auto   : {dict(auto)}")
    print(f"  identical? {manual == dict(auto)}")
    # Return a plain dict: leaking a defaultdict lets callers create keys
    # merely by READING them, which is a genuinely nasty bug to trace.


# ---------------------------------------------------------------- DEMO 4
def demo_string_sort_bug(rows: list[dict]) -> None:
    print(SEP)
    print("DEMO 4 — the silent bug: sorting numbers as strings")
    print(SEP)

    amounts_str = [r["amount"] for r in rows]           # csv gives STRINGS
    wrong = sorted(amounts_str, reverse=True)           # lexicographic!
    right = sorted((float(a) for a in amounts_str), reverse=True)

    print(f"  raw from csv        : {amounts_str}")
    print(f"  sorted as strings   : {wrong}")
    print(f"  sorted as floats    : {[int(x) for x in right]}")
    print(f"  '9000' > '150000' ? {'9000' > '150000'}   <- lexicographic, TRUE")
    print("  ^ This is why every csv numeric field needs float() first.")


# ---------------------------------------------------------------- DEMO 5
def demo_vectorised_preview() -> None:
    """Preview of 0.6: the same filter, timed, loop vs list-comp."""
    print(SEP)
    print("DEMO 5 — comprehensions are also faster (preview of 0.6)")
    print(SEP)

    # Already numeric, so we time the LOOP MACHINERY itself rather than
    # float() parsing — otherwise parsing dominates and hides the difference.
    big = list(range(2_000_000))

    t0 = time.perf_counter()
    out = []
    for x in big:                       # interpreted loop + method lookup
        if x > 1_000_000:
            out.append(x)               # .append resolved on every iteration
    t_loop = time.perf_counter() - t0

    t0 = time.perf_counter()
    out2 = [x for x in big if x > 1_000_000]   # loop runs in C, no lookup
    t_comp = time.perf_counter() - t0

    print(f"  rows scanned      : {len(big):,}")
    print(f"  loop + append     : {t_loop*1000:7.1f} ms")
    print(f"  list comprehension: {t_comp*1000:7.1f} ms")
    print(f"  same result?      : {out == out2}")
    print(f"  speedup           : {t_loop/t_comp:.2f}x")
    print("  Modest — because BOTH still loop in Python.")
    print("  0.6 NumPy removes the Python-level loop entirely. Compare:")

    try:
        import numpy as np
        arr = np.arange(2_000_000)
        t0 = time.perf_counter()
        out3 = arr[arr > 1_000_000]
        t_np = time.perf_counter() - t0
        print(f"  numpy boolean mask: {t_np*1000:7.1f} ms")
        print(f"  speedup vs loop   : {t_loop/t_np:.1f}x   <- this is why 0.6 matters")
        print(f"  same result?      : {len(out3) == len(out)}")
    except ImportError:
        print("  numpy not installed — install it for 0.6 and re-run.")


def main() -> None:
    print(f"Python {sys.version.split()[0]}")
    path = make_sample_csv()

    try:
        rows = load_invoices(path)
    except FileNotFoundError:
        print(f"No invoice file at {path}. Create it and re-run.")
        return

    demo_comprehension_equivalence(rows)
    demo_get_vs_bracket(rows)
    demo_defaultdict(rows)
    demo_string_sort_bug(rows)
    demo_vectorised_preview()

    print(SEP)
    print("Ranked vendor totals (the closed-book rebuild target):")
    totals: dict[str, float] = defaultdict(float)
    for r in rows:
        totals[r.get("vendor") or "UNKNOWN"] += float(r["amount"])
    for vendor, total in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {vendor:<10} {total:>14,.2f}")
    print(SEP)


# Without this guard, importing the module from a pytest file (0.5) would
# execute everything above. That is what makes a script untestable.
if __name__ == "__main__":
    main()
