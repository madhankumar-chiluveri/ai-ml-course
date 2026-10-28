# Scenario Patterns

These are fictional concept seeds, not published copy or confirmed incidents. Refine the chosen seed for the current audience and evidence.

## What the supplied example contributes

The user's screenshot shows three familiar categories followed by an exaggerated engineering frustration in the fourth panel.
The repeated image establishes the visual rule. The final panel breaks its scale and supplies the punchline.
The caption leaves the joke to the image.

Reuse the mechanism: familiar setup, specific technical twist, visual escalation. Create new scenes and wording.
The screenshot is a composition reference, not evidence that humour caused its visible engagement.

## Useful comic mechanisms

| Mechanism | Technical tension | Possible composition |
|---|---|---|
| Deadpan reply | Engineer expects agreement; a system returns an inconvenient fact | Two speech bubbles plus one decisive output |
| Escalation | The same attempted fix repeats or creates more work | Repeated action with a growing queue or stack |
| Expectation versus mechanism | A label changes; execution behaviour does not | Aligned split showing the same underlying bottleneck |
| Confidence undercut | A success claim meets a test or observable failure | Confident message followed by a restrained failure signal |
| Hidden-state reveal | The deployed change does not reach the observed response | New state, hidden cache, old response |
| Delayed reveal | Work happens incrementally but its delivery is held | Timeline ending in one accumulated output |

## Candidate seeds from Phase 0

### 1. The persistent retry loop

- **Grounding:** [HTTP](../../../../course-path/phase-0-engineering-foundations/07_http_fundamentals.md) and [REST clients](../../../../course-path/phase-0-engineering-foundations/08_consuming_rest_apis.md).
- **Situation:** a tool repeats a confirmed invalid payload without changing it.
- **Setup:** API: “Invalid payload.”
- **Punchline:** Retry loop: “What if I ask more confidently?”
- **Mechanism:** personified persistence against a deterministic validation rule.
- **Scene:** unchanged request cards accumulate beside an unmoved validation response. The final request delivers the punchline.
- **AI-product consequence:** repeated invalid tool calls consume attempts without repairing the input.
- **Boundary:** classify the provider error. This joke does not claim every HTTP 400 is non-retryable.
- **Route:** community; practitioner recognition; one image; evidence needed only if adding a measured result or provider-specific claim.

### 2. The proxy's generous gift

- **Grounding:** [NGINX](../../../../course-path/phase-0-engineering-foundations/12_nginx_reverse_proxy.md).
- **Situation:** proxy buffering holds a stream before the user receives the accumulated output.
- **Setup:** Model: “One token at a time.”
- **Punchline:** Proxy: “I made you a paragraph.”
- **Mechanism:** a component proudly delivers the opposite of the intended experience.
- **Scene:** separate token tiles enter a proxy. One large text block leaves it. The proxy's speech bubble supplies the final line.
- **AI-product consequence:** the interface loses incremental delivery and can appear stalled.
- **Boundary:** verify the relevant buffering configuration before production. Do not imply every proxy buffers every stream.
- **Route:** community; practitioner recognition; one image; source verification before a production brief.

### 3. The independent reviewer

- **Grounding:** [pytest](../../../../course-path/phase-0-engineering-foundations/05_testing_with_pytest.md).
- **Situation:** a proposed code fix is declared complete before tests verify it.
- **Setup:** Coding assistant: “Fixed.”
- **Punchline:** pytest: “We need to talk.”
- **Mechanism:** confidence undercut by an independent check.
- **Scene:** an optimistic completion bubble sits above a small, clearly illustrated failing-test panel. The test runner gets the final reply.
- **AI-product consequence:** tool code and API regressions need executable checks beyond a completion message.
- **Boundary:** fictional dialogue. A failing test needs a concrete assertion if demonstrated. Do not generalise to model quality or agent evaluations.
- **Route:** community; practitioner recognition; one image; no invented failure counts or actual terminal capture.

### 4. The cache's editorial preference

- **Grounding:** [PostgreSQL, pgvector, and Redis](../../../../course-path/phase-0-engineering-foundations/15_postgres_pgvector_redis.md).
- **Situation:** cached output remains after a backend change because invalidation has not occurred.
- **Setup:** Backend: “I deployed the fix.”
- **Punchline:** Cache: “I preferred the old version.”
- **Mechanism:** personified hidden state resisting the visible change.
- **Scene:** a fresh response stops at a labelled cache boundary. An older cached response continues toward the interface.
- **AI-product consequence:** stale tool results or configuration can hide a deployed change.
- **Boundary:** show a cache hit with an active lifetime or missing invalidation. Do not imply that Redis ignores writes.
- **Route:** community; practitioner recognition; one image; check the chosen invalidation scenario before production.

### 5. The promotion that changed nothing

- **Grounding:** [async Python](../../../../course-path/phase-0-engineering-foundations/03_async_typehints_pydantic.html) and [FastAPI](../../../../course-path/phase-0-engineering-foundations/09_building_apis_with_fastapi.md).
- **Situation:** blocking work remains on the event loop after changing a handler to `async def`.
- **Setup:** Handler: “I got promoted to async.”
- **Punchline:** Request queue: “Congratulations. We're still waiting.”
- **Mechanism:** a new label meets an unchanged physical bottleneck.
- **Scene:** an `async def` label changes above the same blocking call. The request queue supplies the final line.
- **AI-product consequence:** the shared event loop cannot serve other work while that blocking call holds it.
- **Boundary:** specify blocking work inside the async handler. Do not claim async itself reduces concurrency.
- **Route:** community; practitioner recognition; one image; reuse the existing LI-008 proof if adding results.

## Selecting a seed

Prefer the concept the intended reader recognises fastest and whose visual already contains the joke.
Use the retry or proxy seed when following the current reliability series. Use pytest when code-verification friction is the stronger context.
Treat these as creative hypotheses. They do not establish relative engagement or a publishing order.
