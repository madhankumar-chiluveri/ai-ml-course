---
post_id: LI-026
status: review
intended_date: 2026-11-24
scheduled_at: 2026-11-24T16:00:00+05:30
instagram_scheduled_at: 2026-11-24T19:00:00+05:30
schedule_note: Proposed Tuesday slots for review.
timezone: Asia/Kolkata
pillar: community
format: single_image
instagram_format: single_image
visual_treatment: image_generated_character_scenes
visual_rationale: Mad's double take and the oversized report reveal that the agent kept working after the chat stopped.
primary_goal: shares
instagram_primary_goal: shares
audience: Full-stack engineers building AI agents
proof_type: demo
course_source: ../../../../course-path/phase-0-engineering-foundations/03_async_typehints_pydantic.html
public_credit: madvibe.ai
asset: ../assets/LI-026-agent-stop-button/LI-026-agent-stop-button.png
asset_source: ../assets/LI-026-agent-stop-button/prompt.txt
---

# The user hit Stop. The AI agent kept working.

- [Shared 2160 × 2700 comic](../assets/LI-026-agent-stop-button/LI-026-agent-stop-button.png) and [ImageGen prompt](../assets/LI-026-agent-stop-button/prompt.txt).
- **Alt text** — Mad clicks Stop as his AI chat displays “Compiling report.” A robot drops a huge bound report onto his desk and says, “I finished it quietly.”

## Evidence

The comic is fictional. In a local Python 3.14.4 demo, cancelling the update task left a separately started worker running. The worker completed after the stream stopped. The demo used two in-process tasks. [Python task cancellation](https://docs.python.org/3.14/library/asyncio-task.html#asyncio.Task.cancel)

## LinkedIn

### Final copy

The user hit 𝐒𝐭𝐨𝐩. The AI agent kept working.

A Stop button can close the chat while a background job keeps running. Check the job’s final state before showing “Cancelled.”

When someone clicks Stop in your AI app, what’s still running?

## Instagram

### Caption

Apparently, Stop meant “fewer updates.” 😅

A background job can keep running after the chat goes quiet.

#DeveloperHumor #AIAgents
