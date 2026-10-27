# LinkedIn Content Backlog

This is the durable idea queue. Course ideas follow the learner's current phase; the separate AI Update series covers sourced trending AI topics. IDs remain stable when an idea is deferred.

## Current scope

Only Phase 0 — Engineering Foundations course ideas are active. Later-phase course ideas remain deferred until their phase is active. The [AI Update series](skills/ai-news-carousel/SKILL.md) can cover any sourced trending AI topic beyond Phase 0 without presenting it as completed study or a tested result. A product release or engineering consequence is not required.

## Status vocabulary

idea → brief → draft → review → scheduled → published → measured → archived

deferred means the topic is valid but outside the active course phase.

## Phase 0 active candidates

| ID | Working idea | Pillar | Audience problem | Source / evidence | Source | Priority | Status |
|---|---|---|---|---|---|---:|---|
| LI-002 | Why I am beginning AI engineering with Phase 0 foundations | Narrative | Learners jump to frameworks without the systems judgment underneath them | Specific Phase 0-to-AI-product connections | Phase 0 course notes | 1 | scheduled |
| LI-008 | One blocking function can freeze a streaming AI endpoint | Build proof | Agent latency is blamed only on the model | Concurrency proof and event-loop trace | Phase 0.3 / 0.9 | 2 | review |
| LI-009 | Retrying the same invalid request is not resilience | Authority | Agent tools amplify bad retry policies | Executed offline policy simulation and seven-page decision carousel | Phase 0.7 / 0.8 | 3 | review |
| LI-011 | One AI product has at least three kinds of state | Authority | Postgres, pgvector, and Redis are treated as interchangeable | Storage-boundary architecture | Phase 0.15 | 3 | idea |
| LI-012 | NGINX can make token streaming arrive all at once | Build proof | Proxy buffering is mistaken for model latency | Before/after streaming trace | Phase 0.12 | 3 | idea |
| LI-013 | AI says Fixed; pytest asks for a word | Community | A confident completion message arrives before executable checks | Fictional comic grounded in the testing lesson | Phase 0.5 | 1 | scheduled |

## AI Update candidates

| ID | Working idea | Pillar | Audience angle | Source | Status |
|---|---|---|---|---|---|
| LI-014 | Before you add another agent, check what it adds | Authority | Follow the testing comic with a sourced comparison of handoffs, shared context, and useful agent boundaries | Anthropic guide, 22 October 2026 | review |

## Deferred until their course phase is active

| ID | Working idea | Source | Status |
|---|---|---|---|
| LI-001 | Dot product versus cosine can rank embeddings differently | Phase 1.4 | deferred |
| LI-003 | A working LangGraph demo is not a production agent | Phases 6–7 | deferred |
| LI-004 | Flutter should call an authenticated agent API, not tools directly | Current work + Phase 6 | deferred |
| LI-005 | A prompt improved by 3.43 points but was not statistically better | Phase 1.10 | deferred |
| LI-006 | Rank-8 LoRA is small, but rank 8 is not always enough | Phase 1.3 | deferred |
| LI-007 | Naive softmax returns NaN while stable softmax works | Phase 1.12 | deferred |
| LI-010 | Unit tests are not agent evaluations | Phase 0.5 / Phases 7.4–7.5 | deferred |

## Intake rule

An idea enters a dated week when it is an active-phase course topic or a sourced AI Update with a clear audience angle. Course posts need an AI-product consequence; AI Updates can explain, compare, tell a story, discuss, or curate. Select updates near publication; do not reserve a future headline or change deferred course IDs into news posts.
