"""
0.5 — Testing with pytest.

Runnable: `python 05_testing_with_pytest.py`
Requires: pytest  (pip install pytest)

SAFE: writes a throwaway test package under the system temp folder, runs
pytest against it, prints the real output, then deletes it.

What this proves practically:
  1. Fixtures are injected BY PARAMETER NAME, with no import.
  2. function-scope runs per test; session-scope runs ONCE. Both observable.
  3. parametrize turns 1 function into N independently-named test cases.
  4. `0.1 + 0.2 == 0.3` FAILS. pytest.approx passes. Real assertion output.
  5. monkeypatch replaces a network call so the suite runs offline.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SEP = "=" * 70

# --------------------------------------------------------------- the code
# under test. A tiny module so the tests have something real to exercise.
SRC = '''
import requests


def parse_amount(raw):
    """CSV/LLM amounts arrive as messy strings. Normalise or raise."""
    if raw is None:
        raise ValueError("amount is None")
    s = str(raw).strip().replace(",", "")
    if not s:
        raise ValueError("amount is empty")
    try:
        return float(s)
    except ValueError as e:
        raise ValueError(f"cannot parse amount: {raw!r}") from e


def high_value(rows, threshold=50_000):
    return [r for r in rows if parse_amount(r["amount"]) > threshold]


def fetch_fx_rate(code):
    """Hits a real API. Tests must NEVER call this for real."""
    r = requests.get(f"https://api.example.com/fx/{code}", timeout=5)
    return r.json()["rate"]
'''

CONFTEST = '''
import pytest

_SESSION_LOADS = []


@pytest.fixture
def sample_invoices():
    """function scope (default): fresh for EVERY test.

    Isolation is the point — one test mutating this list cannot leak into
    another. Shared mutable state produces failures that depend on test
    ORDER, which is agony to debug.
    """
    print("\\n      [fixture: building sample_invoices]")
    return [
        {"vendor": "Acme", "amount": "51000"},
        {"vendor": "Beta", "amount": "9000"},
    ]


@pytest.fixture(scope="session")
def embedding_model():
    """session scope: runs ONCE for the whole run, not per test.

    Use for genuinely expensive read-only setup — loading an embedding
    model (5.1) or starting a container. Function scope here would reload
    it for every single test.
    """
    _SESSION_LOADS.append(1)
    print(f"\\n      [fixture: LOADING MODEL - load #{len(_SESSION_LOADS)}]")
    yield {"name": "fake-embedder", "dim": 384, "loads": len(_SESSION_LOADS)}
    print("\\n      [fixture: unloading model]")   # teardown, after yield
'''

TESTS = '''
import pytest
from app import fetch_fx_rate, high_value, parse_amount


# ---- 1. fixture injection BY NAME, no import ------------------------
def test_filters_below_threshold(sample_invoices):
    result = high_value(sample_invoices, threshold=50_000)
    assert len(result) == 1
    # Assert the MEANINGFUL property, not the whole dict — asserting on the
    # entire object makes the test fail whenever an unrelated field is added.
    assert result[0]["vendor"] == "Acme"


def test_fixture_is_fresh_each_time(sample_invoices):
    """Mutating here must NOT affect the previous test."""
    sample_invoices.append({"vendor": "Gamma", "amount": "99999"})
    assert len(sample_invoices) == 3


def test_fixture_really_was_fresh(sample_invoices):
    """If function scope works, the append above is invisible here."""
    assert len(sample_invoices) == 2


# ---- 2. session scope runs ONCE -------------------------------------
def test_model_loaded_once_a(embedding_model):
    assert embedding_model["loads"] == 1


def test_model_loaded_once_b(embedding_model):
    # Still 1 — the fixture did not re-run.
    assert embedding_model["loads"] == 1


# ---- 3. parametrize: 1 function -> N named cases ---------------------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1000", 1000.0),
        ("1,000", 1000.0),      # thousands separator
        ("  42 ", 42.0),        # whitespace
        ("0", 0.0),             # boundary
    ],
)
def test_parse_amount_real_world_strings(raw, expected):
    assert parse_amount(raw) == expected


@pytest.mark.parametrize("bad", ["", "N/A", "fifty thousand", None])
def test_parse_amount_rejects_garbage(bad):
    # Asserting an exception IS raised. A test that merely calls the
    # function and passes proves nothing about error handling.
    with pytest.raises(ValueError):
        parse_amount(bad)


# ---- 4. floats: the one that surprises people -----------------------
def test_float_equality_is_a_lie():
    """DELIBERATELY FAILING - this is the output you need to recognise."""
    assert 0.1 + 0.2 == 0.3


def test_float_with_approx_passes():
    assert 0.1 + 0.2 == pytest.approx(0.3)


# ---- 5. monkeypatch: no network in tests ----------------------------
def test_fx_rate_without_network(monkeypatch):
    """monkeypatch undoes itself after the test — no manual cleanup."""
    import app

    class FakeResponse:
        status_code = 200
        def json(self):
            return {"rate": 83.2}

    monkeypatch.setattr(app.requests, "get", lambda *a, **k: FakeResponse())
    assert fetch_fx_rate("USD") == 83.2
'''


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def main() -> None:
    try:
        import pytest  # noqa: F401
    except ImportError:
        print("pytest not installed. `pip install pytest` and re-run.")
        sys.exit(1)

    base = Path(tempfile.mkdtemp(prefix="pytest-demo-"))
    print(f"scratch dir: {base}  (safe — deleted at the end)")
    (base / "app.py").write_text(SRC, encoding="utf-8")
    (base / "conftest.py").write_text(CONFTEST, encoding="utf-8")
    (base / "test_app.py").write_text(TESTS, encoding="utf-8")

    try:
        print(SEP)
        print("DEMO 1 — full run. One test FAILS on purpose (float equality).")
        print(SEP)
        r = run([sys.executable, "-m", "pytest", "-q", "--no-header", "-p",
                 "no:cacheprovider"], base)
        print(r.stdout[-3200:])

        print(SEP)
        print("DEMO 2 — parametrize: how the 8 cases are NAMED in the output")
        print(SEP)
        r = run([sys.executable, "-m", "pytest", "-v", "--no-header", "-p",
                 "no:cacheprovider", "-k", "parse_amount"], base)
        for line in r.stdout.splitlines():
            if "::" in line or "passed" in line:
                print("  " + line)
        print("\n  ^ ONE function per group, but each case passes or fails")
        print("    independently and names its own input. 50 eval cases (7.1)")
        print("    are one parametrized test, not 50 copy-pasted functions.")

        print(SEP)
        print("DEMO 3 — fixture scope, made visible with -s")
        print(SEP)
        r = run([sys.executable, "-m", "pytest", "-s", "-q", "--no-header", "-p",
                 "no:cacheprovider", "-k", "fixture or model"], base)
        for line in r.stdout.splitlines():
            if "[fixture" in line or "passed" in line or "failed" in line:
                print("  " + line.strip())
        print("\n  ^ sample_invoices built once PER TEST (function scope).")
        print("    The model LOADED ONCE for the whole run (session scope).")

        print(SEP)
        print("DEMO 4 — the failing float test, in full")
        print(SEP)
        r = run([sys.executable, "-m", "pytest", "--no-header", "-p",
                 "no:cacheprovider", "-k", "float_equality", "-vv"], base)
        for line in r.stdout.splitlines():
            if line.startswith(("E ", ">", "assert")) or "Failed" in line or "failed" in line:
                print("  " + line)
        print("\n  ^ 0.1 + 0.2 is NOT 0.3 in binary floating point. Use")
        print("    pytest.approx for every float assertion from Phase 1 on.")
        print(SEP)
    finally:
        shutil.rmtree(base, ignore_errors=True)
        print(f"cleaned up {base}")


if __name__ == "__main__":
    main()
