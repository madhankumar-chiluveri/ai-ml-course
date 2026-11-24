---
post_id: LI-008
status: review
scheduled_at: 2026-11-25T16:00:00+05:30
instagram_scheduled_at: 2026-11-25T19:00:00+05:30
timezone: Asia/Kolkata
pillar: build_proof
format: single_image
instagram_format: single_image
visual_treatment: image_generated_editorial_illustration
visual_rationale: Generated editorial artwork makes the event-loop queue visible; a character is included only if it helps explain the mechanism.
primary_goal: technical-comments
instagram_primary_goal: saves
audience: Full-stack engineers building AI APIs
proof_type: demo
course_source: ../../../../course-path/phase-0-engineering-foundations/09_building_apis_with_fastapi.py
public_credit: madvibe.ai
asset: ../assets/LI-008-async-event-loop/LI-008-async-event-loop.png
asset_source: ../assets/LI-008-async-event-loop/prompt.txt
published_url:
instagram_published_url:
---

# Why did async make this slower?

- [Shared illustrated result card](../assets/LI-008-async-event-loop/LI-008-async-event-loop.png) · [Image-generation prompt](../assets/LI-008-async-event-loop/prompt.txt)
- **Alt text:** Six request envelopes queue at an event loop stopped by a blocking call. Three FastAPI endpoints handle six simultaneous requests with a 0.3-second simulated wait each. A synchronous handler takes 0.32 seconds, an async handler with a blocking sleep takes 1.82 seconds, and an async handler with an awaited sleep takes 0.32 seconds. This is one local illustrative run.

## Evidence

On 24 November 2026, the linked course script ran locally on Python 3.14.4, FastAPI 0.141.1, Uvicorn 0.45.0, and HTTPX 0.28.1. Six clients concurrently sent requests to a single local Uvicorn server. Each handler used a 0.3-second simulated wait. One run measured 0.32 s, 1.82 s, and 0.32 s, respectively. This is an illustrative concurrency demonstration, not a production benchmark or a model latency measurement. [Python asyncio development guidance](https://docs.python.org/3/library/asyncio-dev.html) explains why blocking work delays other tasks on the event loop.

The proposed publishing times are test slots; this post has not been scheduled.

## LinkedIn

### Final copy

I made a FastAPI endpoint slower by adding async.

The problem was a blocking call inside the async handler.

I sent six requests at the same time. Each handler simulated a 0.3-second wait:

• def + time.sleep() → 0.32 s
• async def + time.sleep() → 1.82 s
• async def + await asyncio.sleep() → 0.32 s

In the middle case, time.sleep() held the event loop. The requests queued instead of overlapping.

That matters for an AI API: the same loop may also serve token streams and health checks. A slow stream can have causes outside the model.

For blocking I/O, consider an async library or move the call off the event loop. Check CPU-heavy work separately and test with concurrent requests.

This was one local run with simulated waits, not a production benchmark or a measurement of model latency.

What is the last AI latency issue you traced outside the model?

#AIEngineering #FastAPI

## Instagram

### Caption

Why did this FastAPI async endpoint take longer?

The blocking sleep held the event loop, so six requests queued. With an awaited sleep, the loop could run other tasks while each request waited.

In an AI app, that same loop may also handle streaming and health checks. Check the code around the model when a response feels slow.

The numbers come from one local run with simulated waits. They are not a production benchmark.

Save this for your next async endpoint review.

#FastAPI #PythonAsyncIO #AIEngineering
