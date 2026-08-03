import csv
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

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

def load_and_filter(path: Path, threshold: float = 1000) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if float(r["amount"]) > threshold]

def main() -> None:
    print(f"Python {sys.version.split()[0]}")
    path = make_sample_csv()
    try:
        rows = load_and_filter(Path("invoices.csv"))
        print(rows)
    except FileNotFoundError:
        print("No invoice file found — create it and re-run.")
    print(load_and_filter(path, threshold=80000))

if __name__ == "__main__":
    main()