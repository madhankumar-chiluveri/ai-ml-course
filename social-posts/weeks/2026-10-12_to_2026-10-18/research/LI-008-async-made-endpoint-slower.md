---
post_id: LI-008
status: verified
research_owner: Madhan Kumar Chiluveri
post_file: ../posts/01-tue-async-made-endpoint-slower.md
course_source: course-path/phase-0-engineering-foundations/09_building_apis_with_fastapi.py
---

# Study Note & Post Intent — Async Made the Endpoint Slower

## What I am studying

FastAPI runs a plain `def` endpoint in a thread pool, while an `async def` endpoint runs directly on the event-loop thread. A blocking synchronous call inside `async def` holds that loop instead of yielding control, so otherwise independent requests wait.

## The AI-product bridge

Blocking work inside `async def` → AI API or streaming endpoint → queued requests, delayed tokens, slow health checks, and latency incorrectly attributed to the model.

## What I will post

- **Reader:** Full-stack engineers moving into AI product and agent engineering.
- **Main idea:** The `async` keyword does not preserve concurrency when the endpoint body blocks the event loop.
- **Format:** One 4:5 result card shared across LinkedIn and Instagram because the proof is a single measured comparison.
- **Reader action:** Inspect synchronous calls inside async endpoints and verify behavior with concurrent load.

## Explanation to study before drafting

The local demo sends six concurrent requests to three endpoints. Each request performs 300 ms of simulated work:

1. `def` plus `time.sleep(0.3)` is moved to FastAPI's thread pool.
2. `async def` plus `time.sleep(0.3)` blocks the event loop and serializes the six requests.
3. `async def` plus `await asyncio.sleep(0.3)` yields to the loop, allowing requests to overlap.

For blocking I/O inside an async endpoint, use an asynchronous library or deliberately offload the call with `asyncio.to_thread`. CPU-heavy inference needs an appropriate worker or process strategy; moving it to a thread does not automatically make the computation faster.

## Proof and limits

The script was executed locally on 2026-10-12 with FastAPI 0.141.1, Uvicorn 0.45.0, and HTTPX 0.28.1. One run produced:

| Endpoint | Observed wall time |
|---|---:|
| `def` + `time.sleep(0.3)` | 0.31 s |
| `async def` + `time.sleep(0.3)` | 1.81 s |
| `async def` + `await asyncio.sleep(0.3)` | 0.32 s |

The 5.8× comparison is `1.81 / 0.31`, rounded to one decimal. This is a deterministic educational reproduction with simulated blocking work and a single local timing run, not a production benchmark or a universal FastAPI performance ratio.

## Questions to resolve

- Repeat the run or add a distribution before treating the ratio as a benchmark rather than an illustrative reproduction.
- Verify any real SDK or inference claim against that library's actual blocking behavior before naming it.
