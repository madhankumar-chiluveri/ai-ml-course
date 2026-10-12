# Evidence Gate

Apply this gate before drafting and again before marking a post final. The purpose is expert trust, not academic ornament.

## Classify every material claim

| Claim type | Minimum support | Required disclosure |
|---|---|---|
| Measured result | Reproducible experiment, benchmark, analytics export, or trace | Environment, versions, workload/data, concurrency, sample size, seed when relevant, measurement window, and limitations |
| Product or system behavior | Working demo, code path, trace, test, or authoritative documentation | Scope, configuration, observed vs expected behavior, and production-readiness limits |
| Causal claim | Controlled comparison or strong mechanism plus corroborating evidence | Alternative explanations and confidence |
| External fact | Current primary source; secondary source only when primary is unavailable | Source and date for time-sensitive facts |
| First-hand lesson | Specific event, decision, or artifact from the author's work or study | Context and what is observation versus interpretation |
| Hypothesis or opinion | Clear reasoning | Label as hypothesis, inference, expectation, or opinion |

## Gate sequence

1. Highlight precise numbers, superlatives, causal language, product behavior, quotes, and time-sensitive statements.
2. Link each claim to its source, experiment, trace, or first-hand observation in the research file.
3. Verify that the artifact supports the claim's exact scope—not a broader conclusion.
4. Add reproducibility context for measurements and benchmarks.
5. Separate observation from interpretation and measured result from hypothesis.
6. Narrow, qualify, or remove anything that fails the gate.
7. Sanitize secrets, customer data, employer-confidential details, and personal information.

## Decision outcomes

- **PASS:** support is direct, scoped, current enough, and reproducible where appropriate.
- **QUALIFY:** support is partial; state the condition, sample limit, uncertainty, or that this is an inference.
- **HOLD:** evidence could be collected safely before publication; create or complete the research task.
- **REMOVE:** the claim is unnecessary, unverifiable, confidential, or likely to mislead.

## Non-negotiable checks

- No fabricated benchmark, trace, quote, user result, work history, customer story, or credential.
- No unsupported percentages, latency/cost claims, “X× faster,” “best,” “always,” or “production-ready.”
- No conclusion from one run when variance matters; report sample size and distribution or qualify it as illustrative.
- No causal wording when evidence shows only association.
- No citation that merely mentions the subject; it must support the stated claim.
- No fake precision. Round or state a range when the method cannot justify exactness.
- No virality or reach promise. Historical format medians inform tests, not guarantees.

## Publication note

The post should show enough evidence for trust without dumping the full research ledger. Keep detailed sources, setups, rejected claims, and limitations in the linked research file; surface the decisive proof and material caveat in the post.
