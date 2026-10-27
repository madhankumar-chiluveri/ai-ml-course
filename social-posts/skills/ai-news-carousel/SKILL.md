---
name: ai-news-carousel
description: >-
  Find and verify trending AI topics and prepare a branded LinkedIn document with a paired Instagram carousel. Use for Madhan's AI updates, research explainers, tools, creative trends, industry stories, debates, or curated roundups. Choose the narrative and visuals for the topic. Planning produces a brief; production produces assets and captions for manual publishing.
---

# AI Update

Make a trending AI topic clear, interesting, and useful to Madhan's audience.
Cover any AI topic with a supported angle: tools, models, research, art, video, robotics, industry, policy, or culture.
Choose a focused story or a coherent collection. Match the narrative to the topic instead of imposing a release-analysis template.
Audience interest and evidence guide selection. Never promise virality or a global trend ranking.

## Establish the edition

Read `social-posts/README.md`, the active weekly plan, recent post titles, and `BACKLOG.md`.
Use the workspace `linkedin-content-system` skill for positioning and paired-platform delivery.
The local rule against automatic research artifacts overrides that skill's research-file instructions.

Use the saved profile and audit as historical context, not a live account refresh.
State the coverage date when discussing past performance. Do not assume access to every published post.
Avoid a duplicate story unless new evidence or a distinct audience angle justifies returning to it.

This series is an explicit exception to the Phase 0 restriction and the shared skill's required AI-product engineering consequence.
A useful explanation, creative perspective, informed discussion, or curated discovery can justify the topic.
Source analysis does not establish completed study or hands-on experience. Keep ordinary course posts within the active phase.
Choose the pillar for the edition's goal; use `proof_type: source_analysis` for sourced analysis.

## Find a worthwhile story

1. Establish today's date and intended publication date in `Asia/Kolkata`.
2. Scan roughly five candidates attracting attention in the preceding seven days, including older topics with renewed interest.
3. Use web search, official announcements, release notes, model cards, papers, and upstream repositories.
4. Use accessible YouTube transcripts, developer discussions, or trend tools to detect audience questions and attention.
5. Pick the strongest supported audience angle. Explain the choice briefly in chat; do not save a candidate report.

A release or engineering decision is not required. A research idea, creative trend, debate, industry event, or tool collection can qualify.
Explain why the topic deserves this audience's attention. Separate a new event from renewed discussion of an older topic.
Avoid unsupported rumors, misleading controversy, and recycled headlines presented as new events.
When nothing passes, say so. Offer a clearly dated deeper explanation or skip the edition.

To describe a story as trending, seek two independent attention signals with dates and links.
Examples include a visible developer discussion plus rising search interest or relative YouTube outperformance.
Syndicated copies of one announcement are not independent signals. Missing trend data is unknown, not zero.
Without attention evidence, call it a timely update. Never invent view velocity, search demand, or popularity ranks.

## Verify before writing

Open original sources appropriate to the topic: release documentation, papers, creator examples, official statements, or original reporting.
Confirm event date separately from article date. Exclude future-dated evidence and identify renewed attention accurately.
For product claims, check names, versions, access, regional availability, API versus app behavior, and applicable limits.
For research, distinguish a paper's result from commentary. For creative examples, verify provenance and attribution.
Verify pricing, licensing, rollout details, and benchmark conditions only when relevant to the edition's claims.

Attribute vendor results as vendor-reported. Compare benchmarks only when conditions support the comparison.
Separate sourced fact, vendor claim, and Madhan's interpretation. Do not imply an independent test happened.
Resolve contradictory sources or narrow the claim. Hold unsupported central claims instead of filling gaps.
Read an available transcript before citing video content. Do not claim to have watched inaccessible footage.
Video commentary can explain interest or supply an attributed perspective. Primary technical sources must support product behavior.

Keep decisive source links, their dates, and a verification timestamp in the canonical post file. Two to four usually suffice.
Place material limitations beside the affected slide claim. Link sources in the PDF and in the post's source notes.
Recheck volatile claims within 24 hours before the intended publication. Mark older exports for refresh before use.
Create no separate research files, simulators, evidence dashboards, or claim ledgers unless requested.

## Choose the narrative and visuals

Set the sequence and page count from the topic. There is no mandatory page order or default page count.
The following are optional treatments, not checklists to fill:

| Topic shape | Possible treatment | Possible visuals |
|---|---|---|
| Tool, model, or feature | Discovery, demonstration, comparison, or release story | Annotated interface, use cases, comparison panels |
| Research idea | Question, result, explanation, or open problem | Concept diagram, sourced figure, labeled illustration |
| Creative AI trend | Visual story, example gallery, or cultural explanation | Attributed examples, original artwork, process frames |
| Industry event or debate | Timeline, perspectives, implications, or evidence review | Timeline, quote cards, actors and relationships |
| Robotics or multimodal demo | Capability story, sequence, or explanation | Permitted demo frames, process diagram, annotated scene |
| Connected tools or developments | Curated roundup organized by a clear theme | Consistent example cards or a comparison map |

Open with the topic's strongest honest hook. Finish with the ending that serves the story: insight, question, conclusion, or useful reference.
Do not force previous constraints, mechanisms, use cases, limitations pages, or a try/wait/skip verdict into every edition.
Keep relevant caveats beside their claims even when there is no dedicated limitations page.
Use clear language without assuming the reader has completed advanced course topics.
Give each page one main visual or idea. Vary compositions; avoid repeating the same headline-and-bullets layout.
Use a question only when it helps conversation. Avoid engagement bait.

## Apply Madhan's visual system

Read [style-ref-editorial](../style-ref-editorial/SKILL.md) and its design-system reference before production.
Use the existing warm-paper treatment by default; apply a different design system when the user selects one.
Use a quiet `AI UPDATE` series label, edition date, page count, and the exact public credit `madvibe.ai`.
Keep the series recognizable through typography and spacing; choose illustrations, examples, photos, charts, or diagrams for the story.

Design on a logical 1080 x 1350 canvas and render final PNGs at 2160 x 2700 from editable source at 2× scale.
Use the bundled fonts unless another treatment is selected. At logical size, use approximately 35–55 words per interior page, 34–42 px body text, and generous margins.
Keep essential caveats legible at mobile feed width. Do not hide qualifications in tiny footnotes.
Render labels, figures, and diagrams deterministically with SVG/HTML/CSS or equivalent tools.
Use generated artwork when it suits the story; retain exact labels as rendered type and identify illustrative examples where needed.
Do not fabricate product screenshots, benchmark charts, terminal output, or supplier endorsements.
Inspect every exported page at full size and roughly 360 px width for clipping and reading order.

## Deliver only the selected format

A request to plan or recommend returns a brief. A request to create the edition produces:

- One LinkedIn PDF retaining vector text and diagrams, plus ordered 2160 x 2700 Instagram PNGs with the same claim and sequence.
- One final PNG per page; add lower-resolution copies only when requested.
- Editable production source and page-specific alt text beside the chosen assets.
- One post file with separate canonical LinkedIn and Instagram captions plus the brief source notes.

Use the next unused `LI-###` ID. Set `format: document`, `instagram_format: carousel`, and `status: review` after validation.
Do not invent a course source for news. Record `content_series: ai_update`, the external primary source, and verification time.
Adapt captions to each platform; do not duplicate full captions in plans or the chat response.
Use the existing post validator when available. Check page order, PDF rendering, and source links.

## Cadence and handoff

Default to one news edition within the normal three-to-five-post week; preserve learning and humour posts.
Prepare Tuesday, recheck Wednesday, and suggest Wednesday at 4 PM IST for LinkedIn and 6 PM IST for Instagram.
These are starting hypotheses, not measured personal best times. The dated evidence and optional tools are in
[references/cadence-and-tools.md](references/cadence-and-tools.md); read it for timing or integration decisions.
Do not move an existing scheduled post. Use another free slot or begin the series the following week.

The user handles publishing and scheduling manually. Deliver a reviewable package without opening a composer or changing an account.
Invoking this skill does not start recurring execution, install integrations, or authorize future publication.
After publication, use the existing 24-hour and 72-hour measurement windows. Review four comparable editions before adjusting timing.
Use LinkedIn qualified comments/profile interest and Instagram saves/shares per reach where available; mark missing metrics `NA`.
Treat that review as directional evidence. Change one major variable at a time and avoid causal claims from a few posts.

## Reuse

> Use the ai-news-carousel skill for this week's trending AI topic. Choose a suitable story, narrative, and visual treatment, then create the LinkedIn PDF, Instagram pages, and both captions. Keep publishing manual.
