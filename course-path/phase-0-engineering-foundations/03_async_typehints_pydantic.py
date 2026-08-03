"""
0.3 — Async, Type Hints, Pydantic v2.

Runnable: `python 03_async_typehints_pydantic.py`
Requires: pydantic v2  (pip install pydantic)

What this proves practically:
  1. Pydantic REJECTS bad data at construction, with a field-level error.
  2. A validator catches semantically-null values that are type-correct.
  3. asyncio.gather is ~3x faster than sequential awaits for 3 tool calls.
  4. asyncio.wait_for bounds a hung call instead of hanging forever.
  5. An Annotated reducer MERGES concurrent writes; without it they CLOBBER.
"""

import asyncio
import operator
import time
from typing import Annotated, Literal, TypedDict, get_type_hints

from pydantic import BaseModel, Field, ValidationError, field_validator

SEP = "=" * 70


# ====================================================================== 1
class InvoiceExtraction(BaseModel):
    """The shape you force an LLM to return in 4.8."""

    vendor: str
    # gt=0 is a CONSTRAINT, not a hint. Violating it raises at construction.
    amount: float = Field(..., gt=0, description="Invoice total in INR")
    # Literal restricts to an exact set. The allowed values also appear in
    # the generated JSON schema, so the model is TOLD what is acceptable.
    status: Literal["OPEN", "PAID", "OVERDUE"]
    currency: str = "INR"

    @field_validator("vendor")
    @classmethod
    def reject_placeholder(cls, v: str) -> str:
        # Validators catch what types cannot. An LLM returning "N/A" is
        # type-correct (it is a str) and semantically useless.
        if v.strip().lower() in {"", "n/a", "unknown", "null", "none"}:
            raise ValueError("vendor is a placeholder, not a real value")
        return v.strip()


def demo_validation() -> None:
    print(SEP)
    print("DEMO 1 — Pydantic rejects bad data AT CONSTRUCTION")
    print(SEP)

    good = InvoiceExtraction(vendor="  Acme Ltd  ", amount=51000, status="OPEN")
    print(f"  valid   : {good}")
    print(f"  note    : vendor was auto-stripped by the validator -> {good.vendor!r}")
    print(f"  as json : {good.model_dump_json()}")

    cases = [
        ("negative amount", {"vendor": "Acme", "amount": -5, "status": "OPEN"}),
        ("bad status",      {"vendor": "Acme", "amount": 100, "status": "PENDING"}),
        ("placeholder",     {"vendor": "N/A", "amount": 100, "status": "OPEN"}),
        ("amount as words", {"vendor": "Acme", "amount": "fifty thousand", "status": "OPEN"}),
    ]
    for label, payload in cases:
        try:
            InvoiceExtraction(**payload)
            print(f"  {label:16s}: ACCEPTED (unexpected!)")
        except ValidationError as e:
            err = e.errors()[0]
            loc = ".".join(str(x) for x in err["loc"])
            print(f"  {label:16s}: rejected -> {loc}: {err['msg'][:60]}")

    # This is the point: you get a STRUCTURED error naming the bad field,
    # which is exactly what you feed back to the model to retry (4.8).


# ====================================================================== 2
class AgentState(TypedDict):
    """How LangGraph declares graph state (6.3)."""
    question: str                                   # replaced on write
    findings: Annotated[list[str], operator.add]    # MERGED on write


def demo_reducer() -> None:
    print(SEP)
    print("DEMO 2 — Annotated reducer: merge vs clobber on concurrent writes")
    print(SEP)

    hints = get_type_hints(AgentState, include_extras=True)
    print(f"  question annotation: {hints['question']}")
    print(f"  findings annotation: {hints['findings']}")
    print(f"  extracted reducer  : {hints['findings'].__metadata__[0].__name__}")

    # Simulate what LangGraph does when two parallel nodes both write.
    base = {"question": "why did revenue drop?", "findings": ["baseline"]}
    node_a = {"findings": ["sales down 12%"]}
    node_b = {"findings": ["refunds up 30%"]}

    # WITHOUT a reducer: last write wins. Node A's finding is lost.
    clobbered = dict(base)
    clobbered.update(node_a)
    clobbered.update(node_b)

    # WITH operator.add as the reducer: both are kept.
    merged = dict(base)
    for upd in (node_a, node_b):
        merged["findings"] = operator.add(merged["findings"], upd["findings"])

    print(f"\n  no reducer (clobber): {clobbered['findings']}")
    print(f"  operator.add (merge): {merged['findings']}")
    print("  ^ Without the reducer one agent's work vanishes silently —")
    print("    no error, no warning. The single most common LangGraph bug.")


# ====================================================================== 3
async def call_tool(name: str, delay: float) -> str:
    # `async def` returns a coroutine; nothing runs until awaited/scheduled.
    await asyncio.sleep(delay)          # stands in for a network call (0.8)
    return f"{name} done"


async def sequential() -> tuple[list[str], float]:
    t0 = time.perf_counter()
    out = [
        await call_tool("sql", 0.5),
        await call_tool("search", 0.5),
        await call_tool("email", 0.5),
    ]
    return out, time.perf_counter() - t0


async def concurrent() -> tuple[list[str], float]:
    t0 = time.perf_counter()
    out = await asyncio.gather(
        call_tool("sql", 0.5),
        call_tool("search", 0.5),
        call_tool("email", 0.5),
    )
    return list(out), time.perf_counter() - t0


async def with_timeout() -> str:
    try:
        # Never await a network call unbounded. A hung tool is agent
        # failure mode #1 in 6.14.
        return await asyncio.wait_for(call_tool("slow", 30.0), timeout=1.0)
    except asyncio.TimeoutError:
        return "TIMEOUT after 1.0s -> return a typed error to the agent"


async def demo_async() -> None:
    print(SEP)
    print("DEMO 3 — asyncio.gather vs sequential awaits (3 x 0.5s tools)")
    print(SEP)

    seq_out, seq_t = await sequential()
    con_out, con_t = await concurrent()

    print(f"  sequential : {seq_t:.2f}s  {seq_out}")
    print(f"  gather     : {con_t:.2f}s  {con_out}")
    print(f"  speedup    : {seq_t/con_t:.2f}x")
    print(f"  same result: {sorted(seq_out) == sorted(con_out)}")
    print("  ^ sequential = SUM of delays. gather = MAX of delays.")

    print(SEP)
    print("DEMO 4 — asyncio.wait_for bounds a hung call")
    print(SEP)
    t0 = time.perf_counter()
    msg = await with_timeout()
    print(f"  called a 30s tool with timeout=1.0s")
    print(f"  returned after {time.perf_counter()-t0:.2f}s -> {msg}")
    print("  ^ Without wait_for, this blocks a graph node until the process dies.")


def main() -> None:
    demo_validation()
    demo_reducer()
    asyncio.run(demo_async())
    print(SEP)


if __name__ == "__main__":
    main()
