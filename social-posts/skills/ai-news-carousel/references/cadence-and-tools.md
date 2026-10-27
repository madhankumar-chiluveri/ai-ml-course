# Cadence and optional tools

Checked on 27 October 2026. Recheck service capabilities, limits, and timing evidence before making new recommendations.
This file supports the reusable workflow; it is not a per-post research report.

## Timing hypothesis

| Platform | Initial slot, Asia/Kolkata | Evidence and limit |
|---|---|---|
| LinkedIn | Wednesday, 4 PM | Buffer's 9 September 2026 study of 4.8 million posts ranked this slot highest. |
| Instagram | Wednesday, 6 PM | Buffer's 23 September 2026 study of 9.6 million posts ranked Wednesday highest overall; 6 PM was a leading slot. |

Sources: [LinkedIn study](https://buffer.com/resources/best-time-to-post-on-linkedin/),
[Instagram study](https://buffer.com/resources/when-is-the-best-time-to-post-on-instagram/).
These are observational samples of posts sent through Buffer, normalized to local time.
They do not establish Madhan's best time, an India-specific effect, or a carousel-specific result.
The Instagram data covers January 2024 through December 2025.
The saved account audit lacks posting times and audience geography, so it cannot establish a personal timing optimum.

Keep four editions at the initial slots. Compare equivalent 24-hour and 72-hour snapshots using existing metric definitions.
Prioritize qualified response and useful actions over raw impressions. A small sample supports a next test, not a proven winner.

The 28 October 2026 humour post is already scheduled by the user at 10 AM IST.
Do not replace or reschedule it. LI-014 is the proposed 29 October follow-up, with assets in review.
The active weekly plan owns proposed dates; these are not platform schedules or publication commitments.

## Smallest useful toolset

Start with existing web search, original release documentation, and the local style/renderer tools.
No new publishing MCP or paid discovery service is required to prepare a weekly package.
Public video and transcript availability varies; do not promise access to every YouTube video.

| Tool | Useful role | Constraint |
|---|---|---|
| Google Trends | Check Google or YouTube search interest for candidate topics. | Sampled relative attention does not verify a technical claim. |
| vidIQ plugin | Find recent videos outperforming their own channel baseline; inspect views per hour. | Optional, not connected when this reference was created. Advanced Outliers filters require a paid plan. |
| Existing NotebookLM MCP | Compare a selected set of articles and accessible video transcripts. | Read-only access check returned expired authentication. Reauthenticate only when this optional workflow is wanted. |
| Metricool plugin | Optional consolidated social analytics later. | Not connected. LinkedIn connection is paid; confirm coverage for manually published personal posts. |

Do not add all tools to every edition. Use direct browsing when it supplies enough evidence for the selected topic.
Use NotebookLM only when multiple long sources justify the extra account workflow.
Its YouTube import supports public captioned videos and imports the transcript only.
Videos uploaded less than 72 hours earlier may not import, so it cannot be the only breaking-news source.

Metricool's LinkedIn timing recommendations use general studies, not personal follower activity.
Its help pages differ on the history available for manually published personal posts; verify actual coverage after connection.
Use native account analytics before paying for another dashboard.

## User setup

- Start with existing web search and local asset tools. No new key or paid plan is required for that workflow.
- Google Trends can be checked through its website. No MCP server or API key is required for browser-based checks.
- vidIQ is optional and was confirmed uninstalled. Add it through the plugin directory and complete its account prompts if wanted.
- NotebookLM is already configured, but the access check returned expired authentication. On this Windows setup, run `notebooklm-mcp-server.cmd auth` and finish the Google login in its browser window. The installed CLI and its README confirm this command. After login, call `refresh_auth` and verify a bounded notebook read before using it.

The NotebookLM login is optional; it does not block a carousel made from accessible web sources.
Do not ask for passwords, cookies, or tokens in chat. Do not start login or install extra services merely to prepare an edition.

Primary guidance:

- [Google Trends and relevant topic selection](https://developers.google.com/search/docs/monitor-debug/trends-start)
- [vidIQ Outliers](https://support.vidiq.com/en/articles/9660010-outliers)
- [NotebookLM source and YouTube limits](https://support.google.com/gemininotebook/answer/16215270?co=GENIE.Platform%3DDesktop&hl=en)
- [Metricool personal LinkedIn metrics](https://help.metricool.com/linkedin-personal-profile-metrics-h3usk)
- [Metricool timing methodology](https://help.metricool.com/best-time-to-post-on-social-media-in-metricool-w7ll9)
