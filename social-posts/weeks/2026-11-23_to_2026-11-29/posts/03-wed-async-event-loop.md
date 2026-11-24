---
post_id: LI-008
status: scheduled
scheduled_at: 2026-11-25T16:00:00+05:30
instagram_scheduled_at: 2026-11-25T19:00:00+05:30
buffer_scheduling_status: scheduled_verified
buffer_verified_on: 2026-11-24
buffer_organization: My organization
buffer_linkedin_post_id: 6b05c48b3f48af62c2201a8e
buffer_instagram_post_id: 6b05c49320f9e770f07b9f06
media_url: https://cdn.jsdelivr.net/gh/madhankumar-chiluveri/ai-ml-course@d853d9b51ce22534b06de3893268fca4a5be4a09/social-posts/weeks/2026-11-23_to_2026-11-29/assets/LI-008-async-event-loop/LI-008-async-event-loop.png
media_commit: d853d9b51ce22534b06de3893268fca4a5be4a09
media_expiry: no expiry configured
media_sha256: 378d764243cc724a22f59add6ca91274bfd294c1f1d92c9a9e70390287a1b5ec
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

## Buffer scheduling

Buffer read-back on 24 November confirmed automatic publishing on Wednesday, 25 November at 4 PM IST on LinkedIn and 7 PM IST on Instagram. Both saved posts matched their captions, image, and alt text. The Instagram post has its AI-generated disclosure enabled.

The public jsDelivr URL is pinned to media commit `d853d9b51ce22534b06de3893268fca4a5be4a09`; its PNG matched the local SHA-256. No expiry is configured.

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
