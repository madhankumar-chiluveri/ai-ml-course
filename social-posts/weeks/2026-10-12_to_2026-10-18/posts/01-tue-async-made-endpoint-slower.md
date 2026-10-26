---
post_id: LI-008
status: review
scheduled_at: 2026-10-13T09:00:00+05:30
timezone: Asia/Kolkata
pillar: build_proof
format: single_image
instagram_format: single_image
primary_goal: technical-comments
instagram_primary_goal: saves
audience: full-stack engineers moving into AI product engineering
research: ../research/LI-008-async-made-endpoint-slower.md
course_source: ../../../../course-path/phase-0-engineering-foundations/09_building_apis_with_fastapi.py
asset: ../assets/LI-008-async-event-loop-result-card.png
published_url:
instagram_published_url:
---

# Async Made the Endpoint Slower

## Shared strategy

- **Topic:** Blocking synchronous work inside a FastAPI `async def` endpoint.
- **Evidence and limits:** One local six-request reproduction measured 0.31 s, 1.81 s, and 0.32 s across three endpoint styles. It is illustrative, not a production benchmark.
- **AI-product connection:** A blocked event loop delays token streaming, unrelated requests, and health checks, which can be misdiagnosed as model latency.

## Shared asset

- **File:** `../assets/LI-008-async-event-loop-result-card.png`
- **Canvas:** 4:5 portrait so the same evidence card works in LinkedIn and Instagram feeds.
- **Alt text:** Measured FastAPI concurrency comparison for six 300-millisecond requests: a plain def endpoint with blocking work completed in 0.31 seconds, async def with blocking work took 1.81 seconds, and correct async completed in 0.32 seconds. The blocking call held the event loop and queued requests.

## LinkedIn

### Chosen format

Single-image result card plus concise technical copy. The card makes the measured comparison scannable; the post explains the mechanism, AI-product consequence, and limit.

### Working hook

See the first line under **Final copy**. It is the single canonical hook.

### Reader promise

Recognize when `async def` destroys rather than preserves concurrency, and choose the correct execution boundary.

### Asset brief

Show the three measured wall times, visually isolate the failing `async def` plus blocking call, and trace the causal path from the blocking call to a held event loop and queued requests. Keep the single-run limitation visible.

### CTA

Ask readers which apparent AI-latency bug they eventually traced outside the model.

### Final copy

𝐈 𝐦𝐚𝐝𝐞 𝐚 𝐅𝐚𝐬𝐭𝐀𝐏𝐈 𝐞𝐧𝐝𝐩𝐨𝐢𝐧𝐭 𝟓.𝟖× 𝐬𝐥𝐨𝐰𝐞𝐫 𝐛𝐲 𝐚𝐝𝐝𝐢𝐧𝐠 𝐚𝐬𝐲𝐧𝐜.

Async was not the problem.

The blocking function inside it was.

I sent six concurrent requests to three local endpoints. Each request performed 300 ms of simulated work.

𝐓𝐡𝐞 𝐫𝐞𝐬𝐮𝐥𝐭:

def + time.sleep() → 𝟎.𝟑𝟏 𝐬𝐞𝐜𝐨𝐧𝐝𝐬

async def + time.sleep() → 𝟏.𝟖𝟏 𝐬𝐞𝐜𝐨𝐧𝐝𝐬

async def + await asyncio.sleep() → 𝟎.𝟑𝟐 𝐬𝐞𝐜𝐨𝐧𝐝𝐬

One blocking call inside async def forced the six requests to behave like a queue.

That matters in an AI product because the same event loop may also be serving token streams, health checks, and unrelated API requests. A synchronous HTTP client, database driver, or other blocking operation can make all of them wait—and the model may get blamed for latency it did not create.

𝐓𝐡𝐞 𝐫𝐮𝐥𝐞 𝐈 𝐚𝐦 𝐭𝐚𝐤𝐢𝐧𝐠 𝐟𝐨𝐫𝐰𝐚𝐫𝐝:

• Async operation → await it

• Blocking I/O → use plain def or deliberately offload it

• CPU-heavy inference → use an appropriate worker or process strategy

• Verify with concurrent load, not one localhost request

Async is not a performance feature by itself.

𝐑𝐞𝐥𝐞𝐚𝐬𝐢𝐧𝐠 𝐭𝐡𝐞 𝐞𝐯𝐞𝐧𝐭 𝐥𝐨𝐨𝐩 𝐢𝐬 𝐰𝐡𝐚𝐭 𝐩𝐫𝐞𝐬𝐞𝐫𝐯𝐞𝐬 𝐜𝐨𝐧𝐜𝐮𝐫𝐫𝐞𝐧𝐜𝐲.

Environment: FastAPI 0.141.1, Uvicorn 0.45.0, HTTPX 0.28.1. This was one local illustrative run using time.sleep(0.3), not a production benchmark.

What is the last “AI latency” problem you discovered outside the model?

#AIEngineering #FastAPI #BackendEngineering

## Instagram

### Chosen format

Single-image evidence card. The same 4:5 asset preserves the measured proof, while the caption is shorter, front-loads the searchable topic, and uses a save-oriented CTA.

### Production plan

- **Headline:** `ASYNC MADE THIS ENDPOINT 5.8× SLOWER`
- **Setup strip:** `6 CONCURRENT REQUESTS · 300 MS EACH`
- **Result rows:** `def + blocking — 0.31 s`; `async def + blocking — 1.81 s`; `async def + await — 0.32 s`.
- **Causal strip:** `BLOCKING CALL → EVENT LOOP HELD → REQUESTS QUEUED`.
- **Limitation footer:** `LOCAL ILLUSTRATIVE RUN · NOT A PRODUCTION BENCHMARK`.
- **Brand footer:** `PRODUCTION AI FAILURE FILES · MADHAN KUMAR`.

### Caption

FastAPI `async` made this endpoint **5.8× slower**.

The problem was not asynchronous Python. It was a blocking call inside `async def`.

I tested six concurrent requests with 300 ms of simulated work:

• `def` + blocking → **0.31 s**  
• `async def` + blocking → **1.81 s**  
• `async def` + proper `await` → **0.32 s**

The blocking version held the event loop, so requests that should have overlapped formed a queue.

In an AI API, that can delay token streams, health checks, and unrelated requests. The model may look slow even when the real bottleneck is the endpoint around it.

Save this result card for the next time you review a FastAPI or AI streaming endpoint.

Which blocking call have you found hiding inside async code?

#FastAPI #PythonAsyncIO #AIEngineering #BackendDevelopment

**Alt text:** Measured FastAPI concurrency comparison for six 300-millisecond requests: a plain def endpoint with blocking work completed in 0.31 seconds, async def with blocking work took 1.81 seconds, and correct async completed in 0.32 seconds. The blocking call held the event loop and queued requests.

**SEO keywords:** FastAPI async, Python event loop, AI API latency.

### Visual style prompt

Use the personal AI Product Engineer visual system: #0B1220 ink, #F8FAFC paper, #94A3B8 secondary labels, #38BDF8 signal, #22C55E verified state, #F59E0B constraint, and #F43F5E failure. Use a modern sans-serif, left alignment, generous margins, simple solid shapes, and 2 px connectors. Make the measured comparison the main object. Avoid stock AI brains, robots, neon circuits, generic gradients, unreadable microcopy, and another creator's signature layout. Keep contrast accessible and every key label readable on a phone.
