# LinkedIn + Instagram Content Operating System

This directory is the durable planning context for Madhan Kumar Chiluveri's LinkedIn and Instagram content. Each platform remains the source of truth for its published posts; this repository stores shared strategy, evidence, platform-native drafts, assets, weekly execution, and normalized metrics.

Use the shared [`linkedin-content-system`](../.agents/skills/linkedin-content-system/SKILL.md) skill for topic routing, evidence checks, format/theme selection, drafting, review, and metric-driven iteration across Codex, Gemini, and Claude.

Keep delivery lightweight: chosen assets, platform captions, and brief source notes only when needed. Create research files, explanatory HTML, simulators, or claim ledgers only when explicitly requested. This project preference overrides research-generation steps in shared skills.

## Current course scope

Course-derived content is currently limited to **Phase 0 — Engineering Foundations**. Ground these posts in one of its 15 topics and connect it to a concrete AI-product consequence. Later-phase course ideas stay deferred until that phase becomes active.

The **AI Update** series is a separate, user-requested track for any trending AI topic: tools, research, creative trends, robotics, industry, policy, culture, or connected developments. It can cover topics beyond Phase 0 without implying completed study or hands-on testing. Use [ai-news-carousel](skills/ai-news-carousel/SKILL.md) to select and verify an audience angle, then create paired carousel assets. A product release or engineering decision is not required. Keep updates to one edition within the normal week; retain course and humour posts.

Each post file contains one chosen **LinkedIn** section and one chosen **Instagram** section. Choose the strongest native format for each platform from the topic and evidence; do not include unused image, carousel, or Reel alternatives.

### Cross-platform delivery rule

- Every production LinkedIn post request must produce its Instagram adaptation in the same attempt and store both under one post ID. Keep each platform's full publishable copy exactly once in the post file; omit Instagram only when explicitly requested.
- Preserve one central claim, proof boundary, limitation, audience outcome, and visual identity. Adapt hooks, length, CTA, SEO wording, hashtags, and native format instead of copying captions verbatim. Make LinkedIn final copy directly pasteable with sparse Unicode bold and no Markdown styling markers.
- Reuse one 4:5 single-image asset when it is complete and legible on both platforms. Create separate assets only when platform-native information shape or safe areas require them.

## Positioning

### Follow promise

> Helping full-stack engineers ship reliable AI products—from software foundations to production agents.

- **Current role:** AI Product Engineer
- **Core technologies:** LangGraph, MCP, React, Next.js, Flutter
- **Primary audience:** full-stack engineers moving into AI product and agent engineering
- **Secondary audience:** AI practitioners, product founders, engineering leaders, and hiring managers evaluating production readiness
- **Suggested headline:** AI Product Engineer | Shipping reliable AI agents and copilots | LangGraph, MCP, React, Flutter
- **Suggested banner:** Production AI systems explained through real failures, architecture diagrams, and working demos.

### Recurring series

1. **Production AI Failure Files** — one failure, its evidence, and the engineering fix.
2. **114 Topics → AI Product Engineer** — connect each learned foundation to an AI-product consequence.
3. **One Diagram, One Working Demo** — pair a mental model with a runnable proof.
4. **AI Update** — a trending AI topic explained through a suitable story, visual treatment, and useful audience angle.

## Content system

| Pillar | Target share | What belongs here |
|---|---:|---|
| Authority / production AI | 45–50% | Agent architecture, MCP, RAG, evaluations, memory, security, observability, cost |
| Build proof | 20–25% | Working demos, traces, benchmarks, failed runs, architecture decisions, before/after results |
| Personal learning narrative | 20–25% | Course progress, changed beliefs, mistakes, and why foundations matter |
| Community | 10–15% | Focused questions, practitioner comparisons, response posts, and peer spotlights |

No pillar should exceed 60% in one week. The normal cadence is three to five posts when enough briefs are ready. Choose the AI Update pillar for its topic and goal; it does not unlock deferred course posts or require filling every slot.

For each proposed publishing date, consult the [posting-time guide](strategy/posting-times.md). Its daily slots are population-based hypotheses, not established personal best times. For the regular news series, prepare Tuesday and recheck Wednesday. A topical follow-up can use another day; the active week's plan owns proposed dates and status. No recurring execution is configured.

### Format rules

- **Public credit and export quality:** use `madvibe.ai` on new social visuals. Render 4:5 PNGs at **2160 × 2700** from the editable 1080 × 1350 layout at 2× scale. Keep text and diagrams as vectors in carousel PDFs. Retain one final PNG per page; create lower-resolution copies only when requested. Enlarging a bitmap does not add image detail.
- **Visual treatment:** use the local [style-ref-editorial skill](skills/style-ref-editorial/SKILL.md) for warm paper, bold headlines, pastel technical diagrams, and blue handwritten notes. It includes saved internal reference images.
- **Generated PNG uploads:** apply the style skill's metadata-only preparation to every generated single-image post. Verify unchanged pixels, replace the older workspace copy, and keep one final PNG plus its prompt. Inspect the platform preview; labels and upload IDs cannot be guaranteed.
- **Humour treatment:** use [engineering-humour](skills/engineering-humour/SKILL.md) for relatable technical frustrations and original visual punchlines. Choose the scene before the layout; use one image when the joke fits.
- **AI update treatment:** use [ai-news-carousel](skills/ai-news-carousel/SKILL.md). Retain the editorial identity with a dated AI UPDATE label. Choose the narrative, page count, and main visuals for the topic; there is no fixed slide sequence or required verdict.
- **Single image:** default for one mental model, measured result, comparison, or architecture card.
- **Document/carousel:** use for a sequence, explanation, comparison, visual story, roundup, or another topic that benefits from multiple pages.
- **Text:** timely point of view, a personal learning narrative, or a concise field note.
- **Native video:** 45–60 second working demo, failure reproduction, or trace walkthrough.
- **Poll:** only when the choices expose a meaningful engineering decision.

### Editorial and evidence rules

For course and engineering posts, answer:

1. What failed, changed, or had to be decided?
2. Why does it matter when shipping an AI product?
3. What evidence can be shown?
4. What should the reader do differently?
5. What specific experience can the reader contribute?

Use one main idea, one audience, one goal, and one CTA. State benchmark environment, versions, workload, concurrency, sample size, seed, and limitations. Separate measured results from hypotheses. Qualify or remove unsupported numerical claims.

AI Update posts follow the audience question and evidence needs of their topic. They need not answer all five engineering questions or end with an implementation decision. This broader series scope overrides the shared content skill's required AI-product consequence. Keep sourcing and relevant caveats; make the CTA optional.

For humour, answer the technical and audience questions in the brief. Keep the public caption concise and let the visual deliver the joke. Verify the premise, distinguish fictional scenes from actual evidence, and use a CTA only when it adds value.

### Distribution rules

- Publish from the personal profile; tag Nalsoft only for genuinely relevant, publicly shareable company work.
- Prepare native LinkedIn and Instagram packages. The user handles posting and scheduling manually; preparing an asset does not authorize account actions.
- On posting days, leave 10–15 substantive comments: approximately 70% peers, 20% aspirational practitioners, and 10% relevant opportunities.
- Reply to every genuine comment and convert useful questions into backlog candidates.
- Use a soft follow CTA at most once per week.

## Directory architecture

```text
social-posts/
├── README.md                         # canonical positioning and operating rules
├── BACKLOG.md                        # active ideas with stable LI-### IDs
├── strategy/
│   ├── course-to-ai-content-map.md   # evergreen course-derived source map
│   └── metrics-framework.md          # metric definitions and experiment rules
├── audits/
│   └── 2026-09-27-linkedin-baseline.md
├── data/
│   └── linkedin-metrics.csv          # one row per post snapshot
├── weeks/
│   └── YYYY-MM-DD_to_YYYY-MM-DD/
│       ├── plan.md                   # schedule plus retrospective
│       ├── assets/                   # selected visuals and their production inputs
│       └── posts/                    # final copy, asset links, optional source notes
└── templates/
    ├── plan.md
    └── post.md
```

### Naming conventions

- Week: `YYYY-MM-DD_to_YYYY-MM-DD`
- Post file: `NN-day-post-title.md`, for example `01-tue-why-phase-zero-foundations.md`
- Every post receives a stable `LI-###` ID in front matter. The human-readable filename may change if the schedule changes; the ID never changes.

## Ownership rules

| Information | One source of truth |
|---|---|
| Positioning, pillars, formats, editorial rules | This README |
| Future candidates and status | `BACKLOG.md` |
| Course-derived angle library | `strategy/course-to-ai-content-map.md` |
| Metric definitions | `strategy/metrics-framework.md` |
| Raw numeric outcomes | `data/linkedin-metrics.csv` |
| Schedule and weekly status | The dated week's `plan.md` |
| Final copy, asset links, source notes, and material limitations | The post file |
| Long-term interpretation | Dated audits and weekly retrospectives |

Do not duplicate full post copy or raw analytics across files.

## Workflow

```text
Phase 0 topic or verified AI update → Chosen angle → LinkedIn + Instagram captions/assets
                                   → Review → User posts or schedules manually
                                   → Published → 24 h / 72 h metrics → Retrospective
```

1. Use recent account data when available; identify the date and limits of saved audits when live data is unavailable.
2. Select active-phase course ideas or a verified AI update, then place their IDs in a dated week. Check recent titles for duplicates.
3. Verify material claims when needed. Keep essential sources or limitations in the post file.
4. Create the post file from [the post template](templates/post.md). Keep it focused on the selected asset and both captions.
5. Record analytics in the CSV, not inside the post file.
6. Append a short retrospective to the week's `plan.md` after the 72-hour window.
7. Add a new immutable audit after approximately 12–16 published posts.

## Current references

- [Current week: 2026-10-26 to 2026-11-01](weeks/2026-10-26_to_2026-11-01/plan.md)
- [Course-to-AI content map](strategy/course-to-ai-content-map.md)
- [Metrics framework](strategy/metrics-framework.md)
- [2026-09-27 account baseline](audits/2026-09-27-linkedin-baseline.md)

## Legacy archive

The old generated content packs were removed on 2026-09-27 because live LinkedIn retrieval is now available. They remain recoverable at:

`../.remember/social-posts-archive/social-posts-before-account-strategy-2026-09-27.zip`
