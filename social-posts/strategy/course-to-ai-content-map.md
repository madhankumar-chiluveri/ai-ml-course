# Course-to-AI Content Map

This map converts the local [114-topic curriculum](../../course-utils/complete-ai-engineer-roadmap.md) into a coherent LinkedIn series. A topic should not be labelled “AI” merely to make it sound current; the connection must change the reliability, quality, cost, latency, security, or operability of an AI product.

## The bridge from learning to content

For every course topic, complete this chain:

```text
Course concept
  → AI product component that depends on it
  → failure caused by misunderstanding it
  → runnable proof or measurable comparison
  → one practical decision for the reader
```

Example:

```text
Dot product and cosine similarity
  → embedding retrieval and vector search
  → vector magnitude changes the ranking
  → controlled synthetic ranking experiment
  → choose and normalize for the intended metric
```

## Course-derived angle library

This table is evergreen. Active priority and status belong in [`../BACKLOG.md`](../BACKLOG.md); detailed evidence work belongs in a dated week's research file.

| Suggested order | Course topic | AI-product connection | Evidence to produce | Best first format |
|---:|---|---|---|---|
| 1 | 1.4 Dot product and cosine | Embedding similarity, vector magnitude, and retrieval ranking | Rerun the 20,000-trial proof plus a toy retrieval example | Single-image result card |
| 2 | 1.10 hypothesis testing | Deciding whether a prompt or evaluation gain is real | Reproduce the course A/B calculation and confidence interval | Text + chart |
| 3 | 1.3 SVD | The low-rank condition behind LoRA and embedding compression | Rank-versus-error experiment | Carousel |
| 4 | 1.12 Numerical stability | Softmax overflow, mixed precision, and inference failures | Naive versus stable softmax; FP16/BF16 comparison | Code/result card |
| 5 | 0.3 Async + 0.9 FastAPI | Streaming agent tools, concurrency, cancellation | Concurrency benchmark and event-loop trace | Single image + video |
| 6 | 0.7 HTTP + 0.8 REST clients | 429s, timeout budgets, retries, idempotency, and agent retry storms | Fault-injection decision tree | Carousel |
| 7 | 0.9 FastAPI + 0.12 NGINX | Blocking endpoints and proxy buffering that break LLM streaming | Before/after request and network traces | Failure-file series |
| 8 | 0.5 pytest | Unit tests versus trajectory and outcome evaluations | Same agent tested at three layers | Carousel |
| 9 | 0.15 Postgres, pgvector, Redis | Retrieval, durable checkpoints, semantic cache, and rate limits | Three-state architecture plus measured behavior | Diagram |
| 10 | 1.13 entropy, KL, and perplexity | Temperature, uncertainty, decoding, and distribution shift | Reproduce the temperature/entropy experiment | Animated plot |
| 11 | 1.6 chain rule and computational graphs | Gradient accumulation and silent training bugs | Fan-out `+=` versus overwrite proof | Diagram carousel |
| 12 | 0.14 SQL + 0.15 parameterization | Tenant-safe MCP tools, auditability, and write protection | Threat flow and rejection demo | Carousel |
| 13 | 2.1 data leakage | Contaminated LLM evaluation and misleading benchmark gains | Clean versus leaked evaluation | Single image |
| 14 | 2.7 metrics/calibration | Why accuracy alone fails and how to validate LLM judges | Calibration/reliability plot | Carousel |
| 15 | 2.10 ensembles + 6.15 agent judgment | When a tabular model or deterministic rule should replace an LLM | Cost/quality/latency decision table | Text POV |
| 16 | 5.3 chunking + 5.6 reranking | Retrieval quality versus latency and cost | Ablation table on one real corpus | Carousel |
| 17 | 6.14 failure modes + 7.7 cost | Infinite loops, silent tool errors, context overflow, and run budgets | Failed trace plus hard cost ceiling | Video/teardown |

## Phase-level series map

| Curriculum phase | LinkedIn series angle | Questions the content should answer |
|---|---|---|
| 0 — Engineering foundations | **The software foundations agents quietly depend on** | What breaks in an AI product when async, HTTP, Docker, SQL, or caching is misunderstood? |
| 1 — Math foundations | **The math behind embeddings, training, and evaluation** | What does the equation help an engineer decide or debug? |
| 2 — Classical ML | **When not to use an LLM** | When is a simpler model cheaper, more stable, interpretable, or measurable? |
| 3 — Deep learning | **Debugging a model instead of guessing** | Why did training diverge, stall, overfit, or become unstable? |
| 4 — LLM fundamentals | **What happens below an LLM API call** | How do tokenization, attention, decoding, caching, quantization, and tool calls affect product behavior? |
| 5 — RAG | **Retrieval decisions with measured consequences** | Which change improved retrieval, faithfulness, latency, or cost—and compared with what baseline? |
| 6 — Agentic systems | **Production AI Failure Files** | How does the system recover from bad state, tool failure, loops, restarts, or unsafe actions? |
| 7 — Production/evals/LLMOps | **The receipt layer** | How is quality, trajectory, cost, latency, drift, security, and safety measured? |
| 8 — Capstones | **Building a production AI portfolio in public** | What decision was made, what evidence supported it, and what failed before it worked? |

## From map to backlog

This file is an evergreen source map, not an execution queue. Promote a selected angle to [`../BACKLOG.md`](../BACKLOG.md), assign a stable post ID, and create research or a post file only when it enters a dated week.

## Topic-selection gate

Publish only when at least four answers are “yes”:

- Does it reinforce reliable AI product engineering?
- Is there a specific failure, trade-off, or decision?
- Can a real proof or source be shown?
- Can the conclusion be stated without inflated numbers?
- Does it help the target reader build, debug, or choose something?
- Is the angle different from the last two posts?
