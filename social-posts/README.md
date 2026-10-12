# LinkedIn Content Operating System

This directory is the durable planning context for Madhan Kumar Chiluveri's LinkedIn account. LinkedIn remains the source of truth for published posts; this repository stores strategy, evidence, weekly execution, post drafts, and normalized metrics.

Use the shared [`linkedin-content-system`](../.agents/skills/linkedin-content-system/SKILL.md) skill for topic routing, evidence checks, format/theme selection, drafting, review, and metric-driven iteration across Codex, Gemini, and Claude.

## Current course scope

Content is currently limited to **Phase 0 — Engineering Foundations**. Every active post must be grounded in one of its 15 topics and connect that topic to a concrete AI-product consequence. Ideas from later phases stay deferred in the backlog until that phase becomes active; they must not fill empty publishing slots.

Each post file contains one chosen **LinkedIn** section and one chosen **Instagram** section. Choose the strongest native format for each platform from the topic and evidence; do not include unused image, carousel, or Reel alternatives.

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

## Content system

| Pillar | Target share | What belongs here |
|---|---:|---|
| Authority / production AI | 45–50% | Agent architecture, MCP, RAG, evaluations, memory, security, observability, cost |
| Build proof | 20–25% | Working demos, traces, benchmarks, failed runs, architecture decisions, before/after results |
| Personal learning narrative | 20–25% | Course progress, changed beliefs, mistakes, and why foundations matter |
| Community | 10–15% | Focused questions, practitioner comparisons, response posts, and peer spotlights |

No pillar should exceed 60% in one week. The normal cadence is three to five posts per week once enough Phase 0 briefs are ready; do not fill gaps with material from a later course phase.

### Format rules

- **Single image:** default for one mental model, measured result, comparison, or architecture card.
- **Document/carousel:** only for a sequence, decision tree, teardown, or checklist that needs several steps.
- **Text:** timely point of view, a personal learning narrative, or a concise field note.
- **Native video:** 45–60 second working demo, failure reproduction, or trace walkthrough.
- **Poll:** only when the choices expose a meaningful engineering decision.

### Editorial and evidence rules

Every technical post must answer:

1. What failed, changed, or had to be decided?
2. Why does it matter when shipping an AI product?
3. What evidence can be shown?
4. What should the reader do differently?
5. What specific experience can the reader contribute?

Use one main idea, one audience, one goal, and one CTA. State benchmark environment, versions, workload, concurrency, sample size, seed, and limitations. Separate measured results from hypotheses. Qualify or remove unsupported numerical claims.

### Distribution rules

- Publish from the personal profile; tag Nalsoft only for genuinely relevant, publicly shareable company work.
- Prefer native LinkedIn formats and use the native scheduler.
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
│       ├── research/                 # study notes, post intent, proof limits
│       └── posts/                    # briefs, prompt packs, final copy
└── templates/
    ├── plan.md
    ├── research.md
    └── post.md
```

### Naming conventions

- Week: `YYYY-MM-DD_to_YYYY-MM-DD`
- Post file: `NN-day-post-title.md`, for example `01-tue-why-phase-zero-foundations.md`
- Study-note file: `LI-###-topic.md`
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
| Study explanation, proof limits, and sources | The linked research file |
| Final copy, asset brief, and AI assistant prompts | The post file |
| Long-term interpretation | Dated audits and weekly retrospectives |

Do not duplicate full post copy, raw analytics, or research notes across files.

## Workflow

```text
Phase 0 topic → Study note and post intent → Proof/limits → Brief and prompt pack
              → Draft → Review → Scheduled on LinkedIn → Published
              → 24 h / 72 h metrics → Retrospective
```

1. Refresh recent account data directly from LinkedIn before each new weekly plan.
2. Select only ideas whose source is in the active course phase, then place their IDs in a dated week.
3. Create a study note explaining what will be posted; record proof and limits when a claim needs verification.
4. Create the post file from [the post template](templates/post.md), including the reusable AI assistant prompt pack.
5. Record analytics in the CSV, not inside the post file.
6. Append a short retrospective to the week's `plan.md` after the 72-hour window.
7. Add a new immutable audit after approximately 12–16 published posts.

## Current references

- [Current week: 2026-09-28 to 2026-10-04](weeks/2026-09-28_to_2026-10-04/plan.md)
- [Course-to-AI content map](strategy/course-to-ai-content-map.md)
- [Metrics framework](strategy/metrics-framework.md)
- [2026-09-27 account baseline](audits/2026-09-27-linkedin-baseline.md)

## Legacy archive

The old generated content packs were removed on 2026-09-27 because live LinkedIn retrieval is now available. They remain recoverable at:

`../.remember/social-posts-archive/social-posts-before-account-strategy-2026-09-27.zip`
