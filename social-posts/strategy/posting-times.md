# Posting times: LinkedIn and Instagram

Last checked: 2026-10-28. Timezone: Asia/Kolkata (IST). These are starting hypotheses, not proven personal optima.

## Daily starting slots

Use these when choosing a new post time. They do not require a post every day.

| Day | LinkedIn | Instagram | Basis |
|---|---|---|---|
| Monday | 10:00 PM | 7:00 PM | Buffer day-specific peaks |
| Tuesday | 4:00 PM | 7:00 PM | Buffer day-specific peaks |
| Wednesday | 4:00 PM | 7:00 PM | LinkedIn: Buffer; Instagram: reported follower activity |
| Thursday | 5:00 PM | 9:00 AM | Buffer day-specific peaks |
| Friday | 3:00 PM | 7:00 PM | LinkedIn: Buffer; Instagram: reported follower activity |
| Saturday | 9:00 AM | 9:00 PM | Buffer day-specific peaks; weekend is a lower-priority test |
| Sunday | 10:00 PM | 7:00 PM | LinkedIn: Buffer; Instagram: reported follower activity |

Buffer normalized its study results to local time. The table assumes IST is the target audience's relevant timezone; check follower geography before treating it as representative. Late slots are research hypotheses, not a requirement to be online. Schedule only when relevant content is ready.

On 28 October, the account owner reported that Instagram Insights shows follower activity from 6 PM to 9 PM on Wednesday, Friday, and Sunday. Assume those times are IST until the Insights display timezone is verified. Use 7 PM as a test within the reported window; it is not a measured peak. Retain 6 PM as another Wednesday test and Buffer's 12 PM as a population-based comparison. Follower activity is not post engagement.

## What the account data says

On 28 October, Buffer returned all visible sent posts with per-post metrics in one page for the connected LinkedIn profile and @madvibe.ai Instagram account. Of the posts sent from 1 September through 28 October, 10 LinkedIn and 10 Instagram posts were all published during the 10 AM IST hour. Buffer metrics were last refreshed on 28 October and represent different post ages. The export is an available Buffer view, not a guaranteed complete platform history.

This provides a 10 AM baseline, but no comparable hour within this recent sample. Do not infer that another hour is better from these posts. The 27 September LinkedIn audit also lacked historical posting times and audience geography.

For the eight visible posts per platform sent from 1 September to 25 October, Buffer's latest available snapshot reports median LinkedIn impressions of 184.5 and median Instagram reach of 146. All eight Instagram posts show zero comments; LinkedIn shows comments on three of eight. These are cumulative metrics for posts of different ages and formats, not 72-hour snapshots or a test of posting time. Metrics refreshed on 28 October.

The connected Buffer tools expose post-level results but not hourly follower activity. The channel Insights dashboards inspected on 28 October did not display a personalized best-time chart. Buffer's Answers feature may provide recommendations for eligible Instagram Professional accounts; its documentation does not list LinkedIn profiles for personalized best-time recommendations: [Buffer Analyze](https://support.buffer.com/article/521-instagram-metric-descriptions). LinkedIn's [audience analytics](https://www.linkedin.com/help/linkedin/answer/a1373345) documents follower growth and demographics, not an hourly activity chart.

## Why the studies are hypotheses

- [Buffer LinkedIn study](https://buffer.com/resources/best-time-to-post-on-linkedin/): 4.8 million posts; day-level engagement patterns, normalized to local time. Its Thursday peak is 5 PM.
- [Buffer Instagram study](https://buffer.com/resources/when-is-the-best-time-to-post-on-instagram/): 9.6 million Instagram posts, January 2024 to December 2025; median engagement rate. Its Thursday peak is 9 AM; all formats were pooled.
- [Sprout Social Instagram study](https://sproutsocial.com/insights/best-times-to-post-on-instagram/): approximately 2 billion engagements across 307,000 profiles on several networks, November 2025 to February 2026. It identifies Thursday noon to 2 PM, unlike Buffer's morning peak. The studies use different populations and methods; neither proves a personal best.

These are observational findings. Topic, format, audience location, distribution, post age, and platform changes can affect outcomes. The sample counts do not mean every account or each format was represented equally.

## Test the slots

1. Keep the current 3–5 post weekly cadence. Select comparable posts within the same pillar and format.
2. For one weekday and platform at a time, alternate 10 AM IST and that day's table slot across comparable weeks. Record the assigned time before posting. If the slots coincide, select a different weekday.
3. Aim for at least four posts per slot on that platform before an initial directional review. This takes about eight weeks if testing one post per week. More observations are better; do not claim causation or a winner from this small sample.
4. Record actual publication time, platform, stable post ID, format, pillar, source, and 24-hour and 72-hour snapshots in `../data/post-timing-snapshots.csv`. Record retrieval time and provider refresh time. Buffer refreshes metrics periodically, so a late snapshot or stale metric is not an exact 24-hour or 72-hour measurement.
5. Compare medians at the same observed age. On Instagram, use saves and shares per 1,000 reached accounts when all fields exist and reach is positive. On LinkedIn, inspect qualified comments and impressions; calculate comments per 1,000 impressions only when available and positive. Record missing values as `NA`, not zero. Review the post topic and format alongside outcomes.
6. Review monthly, and recheck external sources at least quarterly. Promote a slot to a personal working preference only after repeatable comparable evidence. Record the evidence and limitations here.

If Instagram follower activity and geography are visible in native Insights, use them to select the next test windows. Active followers are not the same as measured post engagement. Buffer's connected tools did not expose hourly follower activity in this review.

## Scheduling guardrails

- Check the weekly plan and this table before proposing a time. An explicitly approved date or time wins over the table and Buffer's recurring queue.
- Check the actual `dueAt`, timezone, channel, caption, assets, and publishing mode after creating a Buffer post. A queue slot can differ from the suggested time.
- Keep scheduled posts unchanged unless the user asks to move them. The 29 October LI-014 posts are scheduled for LinkedIn 3:20 PM and Instagram 10:45 AM IST.
- Instagram feed music is not supported for automatic posting through Buffer. Notification publishing requires the mobile app and manual completion; do not switch modes without explaining the impact.
- This file does not configure a Buffer queue, collect snapshots automatically, or schedule recurring reviews.
