# LinkedIn Content Backlog

This is the durable idea queue. The active queue follows the learner's current course phase; IDs remain stable even when an idea is deferred.

## Current scope

Only Phase 0 — Engineering Foundations ideas are active. A later-phase topic can be retained below as a deferred record, but it cannot be scheduled or drafted until its phase is active.

## Status vocabulary

idea → researching → scheduled → drafting → review → published → measured → archived

deferred means the topic is valid but outside the active course phase.

## Phase 0 active candidates

| ID | Working idea | Pillar | Audience problem | Required proof | Source | Priority | Status |
|---|---|---|---|---|---|---:|---|
| LI-002 | Why I am beginning AI engineering with Phase 0 foundations | Narrative | Learners jump to frameworks without the systems judgment underneath them | Specific Phase 0-to-AI-product connections | Phase 0 course notes | 1 | scheduled |
| LI-008 | One blocking function can freeze a streaming AI endpoint | Build proof | Agent latency is blamed only on the model | Concurrency proof and event-loop trace | Phase 0.3 / 0.9 | 2 | idea |
| LI-009 | Retrying HTTP 400 is not resilience | Authority | Agent tools amplify bad retry policies | Fault-injection demo and retry decision tree | Phase 0.7 / 0.8 | 3 | idea |
| LI-011 | One AI product has at least three kinds of state | Authority | Postgres, pgvector, and Redis are treated as interchangeable | Storage-boundary architecture | Phase 0.15 | 3 | idea |
| LI-012 | NGINX can make token streaming arrive all at once | Build proof | Proxy buffering is mistaken for model latency | Before/after streaming trace | Phase 0.12 | 3 | idea |

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

An idea enters a dated week only when it belongs to the active course phase, has a specific audience problem, explains its AI-product consequence, and has a study source or evidence plan.
