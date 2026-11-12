---
post_id: LI-021
status: review
instagram_status: review
scheduled_at: 2026-11-13T15:00:00+05:30
instagram_scheduled_at: 2026-11-13T19:00:00+05:30
schedule_note: User authorized a GitHub push and Buffer scheduling on 12 November; these are the intended Friday slots, pending Buffer verification.
intended_date: 2026-11-13
timezone: Asia/Kolkata
pillar: community
format: single_image
instagram_format: single_image
visual_treatment: image_generated_character_scenes
visual_rationale: Mad's disbelief and the relaxed bug carry the joke; readable cache labels and an explanation strip make the mechanism clear within the image.
primary_goal: shares
instagram_primary_goal: shares
audience: Full-stack engineers building AI apps with cached tool responses
course_source: ../../../../course-path/phase-0-engineering-foundations/15_postgres_pgvector_redis.md
proof_type: fictional_illustration
public_credit: madvibe.ai
asset: ../assets/LI-021-bug-notice-period/LI-021-bug-notice-period.png
published_url:
instagram_published_url:
---

# The bug is serving its notice period

## Asset

- [Final meme](../assets/LI-021-bug-notice-period/LI-021-bug-notice-period.png).
- [Generation prompt](../assets/LI-021-bug-notice-period/source/prompt.txt). Built-in image generation, with Mad's portrait as the character identity reference.
- [Native generated source](../assets/LI-021-bug-notice-period/source/generated-source.png), 1122 × 1402. The final 2160 × 2700 PNG is a resampled export; it does not gain native detail. Full-size and 360-pixel feed inspections passed for text, reading order, anatomy, and the cache-to-user arrow.
- **Upload verification:** metadata-only preparation preserved decoded pixels. The opaque RGB PNG is 2160 × 2700 and has no parsed caBX chunk. SHA-256: c9a7e6a86a1a55d9b70753fd6a889bc3f797634fb3b4d2acf276af64fa769bb9.
- **Alt text:** Mad announces that the bug is fixed beside a laptop marked FIX DEPLOYED. A smug bug sits inside a CACHE box labelled Saved responses, holding an OLD ANSWER and saying its notice period has not expired. The cache sends that old answer to a user interface showing Same bug. The explanation states that the fixed server can coexist with an old cached answer until that answer expires or is cleared.

## Source note

Fictional humour, not a reported incident or measured trace. The scenario assumes a response-cache hit after a server deployment, with no invalidation or replacement of the existing response. The saved response therefore bypasses the corrected server handler. This does not imply Redis ignores writes.

[Redis EXPIRE documentation](https://redis.io/docs/latest/commands/expire/), checked 12 November 2026, documents key expiration. The AI-product connection is a cached tool response that outlives a code change. The image uses "cleared" as plain-language wording for invalidating the saved answer.

## LinkedIn

### Final copy

𝐓𝐡𝐞 𝐟𝐢𝐱 𝐬𝐡𝐢𝐩𝐩𝐞𝐝.
The bug is serving its notice period. 😅

A cached tool response can outlive the code that produced it.

#DeveloperHumor #AIEngineering

## Instagram

### Caption

When the fix ships but the cached answer stays. 😅

#DeveloperHumor #AIEngineering
