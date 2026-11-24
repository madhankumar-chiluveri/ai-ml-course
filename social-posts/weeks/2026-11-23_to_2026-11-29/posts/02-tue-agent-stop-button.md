---
post_id: LI-026
status: scheduled
intended_date: 2026-11-24
scheduled_at: 2026-11-24T16:00:00+05:30
instagram_scheduled_at: 2026-11-24T19:00:00+05:30
buffer_scheduling_status: scheduled_verified
buffer_verified_on: 2026-11-24
buffer_organization: My organization
buffer_linkedin_post_id: 6b0507dfc43c1f2f5c85d95e
buffer_instagram_post_id: 6b0507e0f0d7b1e0deabeeea
media_url: https://raw.githubusercontent.com/madhankumar-chiluveri/ai-ml-course/69b8ed95e517ea382760c594142e1f93a570fe6a/social-posts/weeks/2026-11-23_to_2026-11-29/assets/LI-026-agent-stop-button/LI-026-agent-stop-button.png
media_commit: 69b8ed95e517ea382760c594142e1f93a570fe6a
media_sha256: e4bff1a57b5ae17e06fe46dcea8ee3084ee91f0fa32df50eb81a35bd5f71a822
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

## Buffer scheduling

Buffer confirmed automatic publishing on 24 November at 4 PM IST on LinkedIn and 7 PM IST on Instagram. Both saved posts matched their captions, image, and alt text. The Instagram post has its AI-generated disclosure enabled.

The public GitHub PNG matched the local file’s SHA-256 and byte count.

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
