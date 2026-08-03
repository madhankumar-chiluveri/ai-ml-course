"""
0.9 - Building APIs with FastAPI.

Runnable: `python 09_building_apis_with_fastapi.py`
Requires: fastapi uvicorn httpx  (pip install fastapi uvicorn httpx)

SAFE + OFFLINE: runs the app in-process and on a local uvicorn server bound
to 127.0.0.1 on a free port, then shuts it down. No internet, no API keys.

What this proves practically:
  1. Pydantic rejects bad input BEFORE your function runs. Counter proves it.
  2. response_model validates the way OUT too - and strips leaking fields.
  3. Depends is a testing seam: override it, no monkeypatching, no network.
  4. The OpenAPI schema is generated FROM the type hints. Same idea as 6.13.
  5. THE ASYNC TRAP: a blocking call in `async def` freezes every other
     request. Measured with 6 concurrent clients against three endpoints.
  6. Streaming needs X-Accel-Buffering:no or 0.12 NGINX swallows it.
  7. lifespan runs ONCE. Liveness and readiness are different questions.
"""

import asyncio
import json
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Annotated, Literal

import httpx
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

SEP = "=" * 70

# Observable counters. The endpoint bodies increment these, so "did my code
# run at all?" becomes a fact rather than an assumption.
CALLS = {"score_body_entered": 0, "lifespan_startups": 0}
ml_models: dict = {}
BLOCK = 0.3          # seconds of work per request in the concurrency demo
CLIENTS = 6          # concurrent callers


# ==================================================================== app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs ONCE at startup, before the first request is served. Loading a
    # model inside the endpoint instead means every request pays the load
    # cost - the most common cause of a terrible p99 (7.7).
    CALLS["lifespan_startups"] += 1
    ml_models["scorer"] = {"name": "gbm-v3", "loaded": True}
    yield
    # Everything after yield runs at SHUTDOWN: close pools, flush traces (7.6).
    ml_models.clear()


app = FastAPI(title="Invoice Risk API", version="1.0.0", lifespan=lifespan)


class ScoreRequest(BaseModel):
    vendor: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0, description="Invoice total in INR")
    days_late: int = Field(0, ge=0)


class ScoreResponse(BaseModel):
    risk: float = Field(..., ge=0, le=1)
    band: Literal["LOW", "MEDIUM", "HIGH"]
    model_version: str


def get_scorer() -> dict:
    """A dependency is just a callable FastAPI resolves per request.

    Why this matters beyond tidiness: in a test (0.5) you assign
    app.dependency_overrides[get_scorer] = lambda: fake and the endpoint
    uses the fake - no monkeypatching, no network. Reaching for the global
    ml_models dict inside the endpoint would make that impossible.
    """
    scorer = ml_models.get("scorer")
    if scorer is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="model not loaded")
    return scorer


ScorerDep = Annotated[dict, Depends(get_scorer)]


@app.post("/score", response_model=ScoreResponse)
async def score(req: ScoreRequest, scorer: ScorerDep) -> ScoreResponse:
    # req is ALREADY validated. A negative amount never reaches this line -
    # FastAPI returned 422 (0.7) with a field-level error before calling it.
    CALLS["score_body_entered"] += 1
    risk = min(1.0, (req.days_late / 90) * 0.7 + (req.amount > 50_000) * 0.3)
    band = "HIGH" if risk > 0.66 else "MEDIUM" if risk > 0.33 else "LOW"
    return ScoreResponse(risk=risk, band=band, model_version=scorer["name"])


@app.post("/score-buggy", response_model=ScoreResponse)
async def score_buggy(req: ScoreRequest):
    # A real bug: risk outside [0,1]. response_model catches it on the way
    # OUT and fails loudly, instead of shipping nonsense to a caller who
    # will store it, chart it, and only notice weeks later.
    return {"risk": 1.7, "band": "HIGH", "model_version": "gbm-v3"}


@app.post("/score-leaky", response_model=ScoreResponse)
async def score_leaky(req: ScoreRequest):
    # The handler returns internal fields. response_model FILTERS them out,
    # so a careless return cannot leak a key or a raw prompt (7.13).
    return {
        "risk": 0.4, "band": "MEDIUM", "model_version": "gbm-v3",
        "internal_api_key": "sk-live-DEMO0000NOTAREALKEY0000",
        "raw_prompt": "system: you are an internal scoring model...",
        "db_connection": "postgres://user:pw@10.0.0.4/prod",
    }


# ---- the three concurrency shapes. Same 0.3s of work each. --------------
@app.get("/sync-blocking")
def sync_blocking():
    # `def` (not async): FastAPI runs it in a THREADPOOL, so a blocking call
    # here does not stop the event loop. Correct for legacy blocking code.
    time.sleep(BLOCK)
    return {"kind": "sync-blocking"}


@app.get("/async-blocking")
async def async_blocking():
    # `async def` with a BLOCKING call: the single worst FastAPI mistake.
    # There is one event loop. time.sleep holds it, so every other request
    # in the process waits - even ones that touch nothing related.
    time.sleep(BLOCK)
    return {"kind": "async-blocking"}


@app.get("/async-correct")
async def async_correct():
    # `async def` with an AWAITABLE: the loop is released during the wait
    # and serves other requests. This is what 0.3's async work buys you.
    await asyncio.sleep(BLOCK)
    return {"kind": "async-correct"}


async def token_generator(prompt: str):
    for word in f"analysing invoice for {prompt} now".split():
        yield f"event: token\ndata: {json.dumps({'text': word + ' '})}\n\n"
        await asyncio.sleep(0.12)


@app.post("/explain")
async def explain(req: ScoreRequest):
    return StreamingResponse(
        token_generator(req.vendor),
        media_type="text/event-stream",       # the SSE format from 0.7
        headers={
            # Without this, NGINX (0.12) buffers the whole stream and
            # delivers it as one blob - streaming that silently is not.
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        },
    )


@app.get("/healthz")
async def liveness():
    # LIVENESS: "is the process alive?" Must NOT check dependencies -
    # otherwise a transient DB blip restarts a perfectly healthy process.
    return {"status": "ok"}


@app.get("/readyz")
async def readiness():
    # READINESS: "can it serve traffic?" SHOULD check dependencies, so the
    # load balancer stops routing while the model is still loading (7.11).
    if "scorer" not in ml_models:
        raise HTTPException(503, detail="warming up")
    return {"status": "ready"}


# ===================================================================== 1
def demo_validation_gate(client) -> None:
    print(SEP)
    print("DEMO 1 - bad input never reaches your function")
    print(SEP)
    CALLS["score_body_entered"] = 0

    bad = [
        ({"vendor": "Acme", "amount": -5}, "amount must be > 0"),
        ({"vendor": "", "amount": 100}, "vendor min_length=1"),
        ({"amount": 100}, "vendor missing entirely"),
        ({"vendor": "Acme", "amount": "not a number"}, "wrong type"),
        ({"vendor": "Acme", "amount": 100, "days_late": -3}, "days_late >= 0"),
    ]
    for payload, label in bad:
        r = client.post("/score", json=payload)
        err = r.json()["detail"][0]
        loc = ".".join(str(p) for p in err["loc"][1:]) or "(body)"
        print(f"  {label:<26} -> {r.status_code}  {loc}: {err['msg'][:44]}")

    r = client.post("/score", json={"vendor": "Acme", "amount": 90000,
                                    "days_late": 88})
    print(f"  {'valid request':<26} -> {r.status_code}  {r.json()}")

    print(f"\n  endpoint body entered: {CALLS['score_body_entered']} time(s),"
          f" out of {len(bad)+1} requests.")
    print("  Five malformed requests, zero lines of validation code, and the")
    print("  function never ran for any of them. The error names the exact")
    print("  field. This is 0.7's 422 and 0.3's Pydantic, wired together.")


# ===================================================================== 2
def demo_response_model(client) -> None:
    print(SEP)
    print("DEMO 2 - response_model guards the way OUT, not just the way in")
    print(SEP)
    good = {"vendor": "Acme", "amount": 1000}

    r = client.post("/score-leaky", json=good)
    handler_returned = ["risk", "band", "model_version", "internal_api_key",
                        "raw_prompt", "db_connection"]
    print(f"  handler RETURNED keys : {handler_returned}")
    print(f"  client RECEIVED keys  : {list(r.json())}")
    print(f"  secrets in response   : "
          f"{'sk-live' in r.text or 'postgres://' in r.text}")
    print("  ^ response_model is an allow-list. A careless return cannot leak")
    print("    a key, a raw prompt or a connection string (7.13).")

    print("\n  and a genuine bug - the handler computes risk=1.7:")
    try:
        r = client.post("/score-buggy", json=good)
        print(f"    status {r.status_code}")
    except Exception as e:
        print(f"    raised {type(e).__name__}: {str(e).splitlines()[0][:70]}")
    print("    ^ caught at the boundary. Without response_model this ships")
    print("      a risk score above 1.0 to whoever stores and charts it.")


# ===================================================================== 3
def demo_dependency_override() -> None:
    print(SEP)
    print("DEMO 3 - Depends is a testing seam, not just tidiness")
    print(SEP)
    # NOTE: TestClient(app) is used WITHOUT `with` here on purpose. As a
    # context manager it runs the lifespan - including SHUTDOWN on exit,
    # which calls ml_models.clear(). This script shares one app object with
    # a live uvicorn server, so that shutdown would wipe the running
    # server's state mid-run. (Found by this script failing exactly that
    # way.) In a normal test file, `with TestClient(app) as c:` is right,
    # because the app is not also serving traffic somewhere else.
    payload = {"vendor": "Acme", "amount": 90000, "days_late": 88}

    # This is exactly what a test file (0.5) does. No monkeypatch, no
    # network, no model on disk - and the endpoint code is untouched.
    app.dependency_overrides[get_scorer] = lambda: {"name": "test-stub-v0"}
    try:
        c = TestClient(app)
        r = c.post("/score", json=payload)
        print(f"  with override    -> model_version="
              f"{r.json()['model_version']!r}")
    finally:
        app.dependency_overrides.clear()

    c = TestClient(app)
    r = c.post("/score", json=payload)
    print(f"  without override -> model_version="
          f"{r.json()['model_version']!r}")

    print("\n  Same endpoint, two models, zero changes to the endpoint. That")
    print("  substitution is what makes an eval suite (7.5) runnable in CI")
    print("  with no GPU, no weights and no provider key.")


# ===================================================================== 4
def demo_openapi_schema() -> None:
    print(SEP)
    print("DEMO 4 - the schema is GENERATED from the type hints")
    print(SEP)
    spec = app.openapi()
    print(f"  {len(spec['paths'])} paths registered, no docs written by hand:")
    for path, ops in list(spec["paths"].items())[:5]:
        print(f"    {','.join(m.upper() for m in ops):<5} {path}")

    props = spec["components"]["schemas"]["ScoreRequest"]["properties"]
    print("\n  ScoreRequest, as a machine-readable contract:")
    for name, meta in props.items():
        limits = {k: v for k, v in meta.items()
                  if k in ("exclusiveMinimum", "minimum", "minLength", "type",
                           "default")}
        print(f"    {name:<11} {limits}")

    print("\n  Nobody wrote that. It came from `amount: float = Field(gt=0)`.")
    print("  This is the same idea as an MCP tool definition in 6.13: a typed")
    print("  Python signature becomes a contract another machine can read and")
    print("  validate against - which is why 0.3 was a prerequisite.")


# ===================================================================== 5
def demo_async_trap(base) -> None:
    print(SEP)
    print(f"DEMO 5 - THE ASYNC TRAP: {CLIENTS} concurrent clients, "
          f"{BLOCK}s work each")
    print(SEP)

    rows = [
        ("/sync-blocking", "def + time.sleep", "threadpool: loop untouched"),
        ("/async-blocking", "async def + time.sleep", "BLOCKS THE EVENT LOOP"),
        ("/async-correct", "async def + await asyncio.sleep", "loop released"),
    ]
    # One pooled client shared across threads (httpx.Client is thread-safe),
    # sized so all CLIENTS callers get a connection. A fresh client per call
    # would add its own handshake to every measurement and muddy the result -
    # which is the 0.8 Demo 1 lesson showing up again.
    limits = httpx.Limits(max_connections=CLIENTS + 4,
                          max_keepalive_connections=CLIENTS + 4)
    with httpx.Client(base_url=base, timeout=60, limits=limits) as c:
        def hit(path):
            return c.get(path).status_code

        # Warm up: open the connections and touch the code paths, so the
        # first row measured is not also paying setup the others skip.
        with ThreadPoolExecutor(max_workers=CLIENTS) as pool:
            list(pool.map(hit, ["/healthz"] * CLIENTS))

        print(f"  {'endpoint':<17} {'what it does':<32} "
              f"{'wall clock':<11} verdict")
        print(f"  {'-'*17} {'-'*32} {'-'*11} {'-'*26}")
        for path, what, verdict in rows:
            t0 = time.perf_counter()
            with ThreadPoolExecutor(max_workers=CLIENTS) as pool:
                list(pool.map(hit, [path] * CLIENTS))
            el = time.perf_counter() - t0
            print(f"  {path:<17} {what:<32} {el:>7.2f}s    {verdict}")

    print(f"\n  Ideal concurrent time is ~{BLOCK}s: all {CLIENTS} overlap.")
    print(f"  Serialised time is ~{CLIENTS * BLOCK:.1f}s: they queue.")
    print("\n  The middle row is the trap. It LOOKS like the fastest option -")
    print("  it says async - and it is the slowest. One blocking call in one")
    print("  `async def` stalls every request in the process, including ones")
    print("  that touch nothing related. If a call is blocking, either use")
    print("  plain `def` or push it to a thread with asyncio.to_thread.")


# ===================================================================== 6
def demo_streaming(base) -> None:
    print(SEP)
    print("DEMO 6 - StreamingResponse, and the header that keeps it streaming")
    print(SEP)
    # Build the client OUTSIDE the timer. This measurement was wrong the
    # first time it was written: httpx.Client() construction is expensive
    # (it loads the CA bundle), and timing it alongside the request made
    # streaming look ~450ms slower than it is. Measure the thing you mean.
    t_build = time.perf_counter()
    c = httpx.Client(timeout=30)
    build_ms = (time.perf_counter() - t_build) * 1000

    first_at, words = None, []
    t0 = time.perf_counter()
    with c.stream("POST", f"{base}/explain",
                  json={"vendor": "Acme", "amount": 1000}) as r:
        print(f"  Content-Type     : {r.headers['content-type']}")
        print(f"  X-Accel-Buffering: {r.headers.get('x-accel-buffering')}")
        for line in r.iter_lines():
            if line.startswith("data: "):
                if first_at is None:
                    first_at = time.perf_counter() - t0
                words.append(json.loads(line[6:])["text"])
    total = time.perf_counter() - t0
    c.close()

    print(f"\n  first token at {first_at*1000:5.0f} ms, "
          f"complete at {total*1000:5.0f} ms")
    print(f"  reassembled: {''.join(words)!r}")
    print(f"\n  (aside: constructing that httpx.Client took {build_ms:.0f} ms -")
    print("   MORE than the entire request. Client objects are expensive and")
    print("   meant to be reused; this is 0.8 Demo 1 from the other side.)")
    print("\n  X-Accel-Buffering: no is the instruction to NGINX (0.12) not to")
    print("  hold chunks. Without it the proxy collects the whole response and")
    print("  delivers one blob - the app streams perfectly and the user still")
    print("  waits. It fails only in production, which is the worst place.")


# ===================================================================== 7
def demo_lifespan_and_probes(base) -> None:
    print(SEP)
    print("DEMO 7 - lifespan runs ONCE. Liveness and readiness differ.")
    print(SEP)
    with httpx.Client(timeout=10) as c:
        for _ in range(3):
            c.post(f"{base}/score", json={"vendor": "A", "amount": 10})
        print(f"  lifespan startups after several requests: "
              f"{CALLS['lifespan_startups']}")
        print(f"  /healthz -> {c.get(f'{base}/healthz').status_code}  "
              f"liveness: is the PROCESS alive?")
        print(f"  /readyz  -> {c.get(f'{base}/readyz').status_code}  "
              f"readiness: can it SERVE?")

        # Simulate the dependency vanishing - a DB blip, a model unload.
        saved = ml_models.pop("scorer")
        print(f"\n  now with the model unloaded (simulating a dependency blip):")
        print(f"  /healthz -> {c.get(f'{base}/healthz').status_code}  "
              f"still alive: do NOT restart me")
        print(f"  /readyz  -> {c.get(f'{base}/readyz').status_code}  "
              f"not ready: stop sending me traffic")
        ml_models["scorer"] = saved

    print("\n  If liveness checked the database, that blip would have killed a")
    print("  healthy process - and every replica at once, since they share the")
    print("  database. Readiness sheds traffic; liveness restarts. Different")
    print("  questions, different blast radius (7.11).")


# ================================================================== runner
def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    import fastapi
    print(f"fastapi {fastapi.__version__} | uvicorn {uvicorn.__version__} "
          f"| httpx {httpx.__version__}")

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    # log_level="critical": Demo 2 triggers a ResponseValidationError ON
    # PURPOSE, and uvicorn would print its full traceback here. In real
    # operation you WANT that traceback - it is how the bug reaches 7.6.
    config = uvicorn.Config(app, host="127.0.0.1", port=port,
                            log_level="critical")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.02)
    print(f"uvicorn on {base}  (offline, 127.0.0.1 only)")

    try:
        with httpx.Client(base_url=base, timeout=30) as client:
            demo_validation_gate(client)
            demo_response_model(client)
        demo_dependency_override()
        demo_openapi_schema()
        demo_async_trap(base)
        demo_streaming(base)
        demo_lifespan_and_probes(base)
        print(SEP)
        print("Two of these gates are free: input validation and output")
        print("validation. That is why a FastAPI endpoint contains so little")
        print("defensive code - and why the one you must think about is the")
        print("async/blocking choice in Demo 5.")
        print(SEP)
    finally:
        server.should_exit = True
        time.sleep(0.3)
        print("server stopped")


if __name__ == "__main__":
    main()
