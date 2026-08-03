# COURSE PATH — Per-Topic Deep Dives

A complete, self-paced course for anyone going from **absolute zero to a hireable AI/ML Engineer**. No prior AI, ML or mathematics background is assumed.

Generated from [`../course-utils/complete-ai-engineer-roadmap.md`](../course-utils/complete-ai-engineer-roadmap.md).

**114 study topics across 8 phases.** Phase 8 holds project briefs rather than study topics.

---

## How each file works

Every topic ships as a **pair**:

| File | What it is |
|---|---|
| `NN_topic.md` | The study note — concept, diagrams, deep dive, checkpoints, glossary |
| `NN_topic.py` | A **runnable** script proving the concept. Self-contained: generates its own data, no setup, no API keys |

Each note follows the same nine sections:

1. **Overview** — what the topic is, and which topics it connects to upstream and downstream
2. **Skip Test — Answered** — a gate *before* studying. Both correct from memory → skip the topic entirely
3. **Visual Concept Diagrams** — rendered Mermaid diagrams, not descriptions of diagrams
4. **Core Technical Deep Dive** — the mechanics, in tables you can revisit
5. **Hands-On Script & Verified Output** — the companion script's **actual captured output**, plus modify-and-re-run exercises
6. **Video** — one vetted video where a good one was confirmed live, otherwise **[VERIFY]** and an authoritative documentation pointer. No title, channel or URL is ever invented
7. **Retrieval Checkpoint — Unanswered** — a gate *after* studying. Answers deliberately withheld
8. **Closed-Book Rebuild** — what to reproduce from scratch with everything closed
9. **Glossary** — every term the note introduced

### On the numbers in these notes

Every figure quoted in §5 came from actually running that script, not from estimation. Where a
measurement moves between runs, the note says so and states which part of it is the claim — the
ratio and the direction, not the millisecond. Several notes deliberately show a **wrong** approach
beside the right one, because the traps that matter in practice are the ones that return plausible
numbers instead of raising an error.

### The two gates, and why they differ

The **Skip Test** comes with answers, because its job is to let you skip work you have already done. The **Retrieval Checkpoint** has no answers anywhere in the file, because its job is to force retrieval from memory. Reading a note and nodding along is not learning it. Rebuilding the script with the file closed is.

**The workflow this is built for:** read once → close the file → rebuild from memory → only then move on.

---

## Tiers

| Tier | Meaning |
|---|---|
| **CORE** | Hire-blocking. Missing it will be found in an interview. |
| **DEPTH** | Differentiator. Do not start any DEPTH topic until every CORE phase is done. |

---

## Progress

- [x] **Phase 0 — Engineering Foundations** · 15 topics · **written** · [`phase-0-engineering-foundations/`](phase-0-engineering-foundations/)
- [ ] **Phase 1 — Math Foundations** · 15 topics · [`phase-1-math-foundations/`](phase-1-math-foundations/)
- [ ] **Phase 2 — Classical ML** · 15 topics · [`phase-2-classical-ml/`](phase-2-classical-ml/)
- [ ] **Phase 3 — Deep Learning Fundamentals** · 15 topics · [`phase-3-deep-learning-fundamentals/`](phase-3-deep-learning-fundamentals/)
- [ ] **Phase 4 — GenAI and LLM Fundamentals** · 13 topics · [`phase-4-genai-llm-fundamentals/`](phase-4-genai-llm-fundamentals/)
- [ ] **Phase 5 — RAG Systems** · 11 topics · [`phase-5-rag-systems/`](phase-5-rag-systems/)
- [ ] **Phase 6 — Agentic Systems** · 15 topics · [`phase-6-agentic-systems/`](phase-6-agentic-systems/)
- [ ] **Phase 7 — Production, Evals, LLMOps** · 15 topics · [`phase-7-production-evals-llmops/`](phase-7-production-evals-llmops/)
- [ ] **Phase 8 — Capstones** · 5 project briefs · [`phase-8-capstone-projects/`](phase-8-capstone-projects/)

### Phase 0 — Engineering Foundations · 120 hours

| # | Topic | Hours | What its script proves |
|---|---|---|---|
| 0.1 | [Python Basics](phase-0-engineering-foundations/01_python_basics.md) | 25 | `.get()` never fires on CSV data — a missing column is `''`, not absent |
| 0.2 | [OOP, Modules, venvs](phase-0-engineering-foundations/02_oop_modules_virtualenvs.md) | 10 | a mutable class attribute is shared across every instance |
| 0.3 | [Async, Type Hints, Pydantic](phase-0-engineering-foundations/03_async_typehints_pydantic.md) | 12 | 3.02x speedup from `gather`; reducer merge vs clobber |
| 0.4 | [Git and GitHub](phase-0-engineering-foundations/04_git_and_github.md) | 5 | a deleted secret is still one command away from any clone |
| 0.5 | [Testing with pytest](phase-0-engineering-foundations/05_testing_with_pytest.md) | 8 | fixture scope, shown by observation; one deliberate failure |
| 0.6 | [NumPy, Pandas, Matplotlib](phase-0-engineering-foundations/06_numpy_pandas_matplotlib.md) | 14 | 17.2x vectorization; `.loc[3]` and `.iloc[3]` return different rows |
| 0.7 | [HTTP Fundamentals](phase-0-engineering-foundations/07_http_fundamentals.md) | 2 | a key in the query string lands in the server log; one in a header does not |
| 0.8 | [Consuming REST APIs](phase-0-engineering-foundations/08_consuming_rest_apis.md) | 3 | retrying a `400` costs 5 requests for 0 results; jitter cuts a retry spike 24 → 5 |
| 0.9 | [Building APIs with FastAPI](phase-0-engineering-foundations/09_building_apis_with_fastapi.md) | 10 | blocking inside `async def` is **5.8x slower** than plain `def` |
| 0.10 | [Linux CLI](phase-0-engineering-foundations/10_linux_cli.md) | 6 | `cut` on padded columns miscounts silently; `du -sh */` hides `.venv` |
| 0.11 | [Docker and Compose](phase-0-engineering-foundations/11_docker_and_compose.md) | 10 | one image id, three container ids; layer-cache order timed for real |
| 0.12 | [NGINX Reverse Proxy](phase-0-engineering-foundations/12_nginx_reverse_proxy.md) | 4 | a buffering proxy destroys streaming the upstream did correctly |
| 0.13 | [OCI Compute Deployment](phase-0-engineering-foundations/13_oci_compute_deployment.md) | 4 | cloud security list **and** host firewall must both permit — the two-layer trap |
| 0.14 | [SQL Fundamentals](phase-0-engineering-foundations/14_sql_fundamentals.md) | 6 | `INNER JOIN` drops 60 vendors from a report; `HAVING` misuse runs and lies |
| 0.15 | [Postgres, pgvector, Redis](phase-0-engineering-foundations/15_postgres_pgvector_redis.md) | 8 | SQL injection defeated live, then blocked by one placeholder |

---

## Running the scripts

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Phase 0
pip install numpy pandas matplotlib pytest pydantic requests fastapi uvicorn httpx
# Phase 2 onward additionally:
pip install scikit-learn
# Phase 3 onward additionally:
pip install torch tiktoken
```

Several Phase 0 scripts need **nothing beyond the standard library** — 0.7, 0.10 and 0.14 included.
Each script names its own requirements in its docstring.

Then run any script directly:

```bash
python phase-0-engineering-foundations/01_python_basics.py
```

Scripts in Phases 4–7 that would otherwise call a paid model API **run offline against a mock provider by default**, so the whole course is runnable without an API key or any spend. Where a live call adds something, the script exposes an explicit opt-in flag and says so in its docstring.

### Every script is offline and safe to run

No script requires internet access. Ones that need a server start their own on `127.0.0.1` on a
random free port and shut it down afterwards. Ones that need files write to a system temp
directory and delete it in a `finally` block. No script writes outside its own temp directory,
and none needs a real credential.

**0.11 is the only script that touches Docker.** It builds throwaway images from a base image
already present on your machine — it never pulls — tags everything with a per-run nonce,
disables networking inside every build and container, and removes only the resources it created.
If no usable local base image exists, the Docker demos print `SKIPPED` rather than downloading
anything, and the remaining demos still carry the lesson.

---

## File naming

`phase-N-<slug>/NN_<topic_slug>.{md,py}` — `NN` is the topic's position within its phase, matching the roadmap numbering exactly. Roadmap topic 2.10 lives at `phase-2-classical-ml/10_ensembles_and_boosting.md`.
