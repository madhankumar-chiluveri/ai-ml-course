# LinkedIn Metrics Framework

Store raw post outcomes in [`post-timing-snapshots.csv`](../data/post-timing-snapshots.csv). Use the platform column to keep LinkedIn and Instagram comparisons distinct.

## Analytics source order

1. Query the connected Buffer MCP first for every account analytics request. Report the source and refresh time with the figures.
2. If Buffer lacks a required LinkedIn metric, date range, or timely update, evaluate a free, open-source custom LinkedIn MCP. Use authorized read access and verify the required fields against native analytics for a known post before relying on it.
3. Use a native screenshot or export the account owner shares to resolve an immediate gap. Record unavailable metrics as `NA`.

## Snapshot policy

- Record each published post at approximately 24 hours and 72 hours.
- Record the provider’s refresh time. Set `planned_snapshot_hours` to `NA` for a cumulative pull outside the planned windows and record the observed age.
- Use `NA` for unavailable data. Zero means a measured zero, not missing data.
- Keep `post_id` stable across every snapshot and file.
- Record the LinkedIn post ID or URL as soon as it is published.
- Use the same timezone and ISO-8601 timestamps.

## Field definitions

| Field | Definition |
|---|---|
| `post_id` | Stable local ID such as `LI-001` |
| `snapshot_hours` | Intended observation window, normally `24` or `72` |
| `format` | `text`, `single_image`, `document`, `video`, or `poll` |
| `pillar` | `authority`, `build_proof`, `narrative`, or `community` |
| `proof_type` | `benchmark`, `trace`, `demo`, `diagram`, `source_analysis`, or `none` |
| `qualified_comments` | Substantive comments from the intended audience |
| `profile_views` | Profile views LinkedIn attributes to this post, when available |
| `reposts` | Reposts LinkedIn reports for this post, when available |
| `followers_gained` | Followers attributable to the post when LinkedIn exposes the value; otherwise `NA` |

## Qualified-comment definition

A qualified comment comes from the intended audience and contributes an implementation experience, correction, counterexample, architecture decision, technical question, or relevant professional conversation. Generic praise is not equivalent to a technical conversation.

## Derived metrics

```text
comment rate          = comments / impressions × 1,000
save rate             = saves / impressions × 1,000
profile-view rate     = profile views / impressions × 1,000
follow conversion     = followers gained / profile views × 100
follows per 1,000     = followers gained / members reached × 1,000
qualified-comment mix = target-audience comments / comments × 100
```

Do not calculate a rate when its denominator is missing or zero.

## Experiment rules

- Do not declare a format winner from one post; use at least three comparable tests.
- Change one major variable at a time where possible: topic, format, hook, CTA, or time.
- Keep posting time controlled for a full week before interpreting time-of-day effects.
- Compare medians as well as averages because one high-reach post can distort the mean.
- Review member reach alongside qualified audience response, profile views, and follower conversion. Compare follows per 1,000 reached across tested LinkedIn posts.
- Store interpretation in the weekly retrospective or a dated audit, never in the CSV.

## Weekly review questions

1. Which post attracted the intended audience rather than only existing connections?
2. Which proof earned saves, profile visits, or substantive questions?
3. Did the opening promise match the actual body?
4. Which comment exposes the next useful research question?
5. Which claim needs correction, qualification, or a better benchmark?
6. What should be repeated once, and what should stop?

