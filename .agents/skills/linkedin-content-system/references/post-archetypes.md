# Post Archetypes

Archetypes control the reasoning and carry a topic-specific editorial treatment—not a mandatory prose template or borrowed persona. Editorial treatment varies register, point of view, cadence, and evidence diction. Use only the sections needed to make one idea credible and useful.

## AI Lab Notebook

**Use for:** benchmarks, evaluations, math behavior, model comparisons, or measured trade-offs.

**Core movement:** question → setup → observed result → interpretation → limitation → reader action.

**Editorial treatment:** Calm and analytical. Use first person only for firsthand experiments; otherwise stay neutral. Favor “measured,” “observed,” “under this setup,” and “suggests.” Pair concise result statements with explicit caveats.

**Required proof:** measured artifact plus environment, versions, workload, sample size, seed when relevant, and limitations. Label hypotheses separately.

**Avoid:** turning a toy run into a universal rule or showing precise numbers without reproducible context.

## Production Blueprint

**Use for:** architecture, data flow, agent state, MCP/RAG integration, decision trees, or system boundaries.

**Core movement:** product constraint → options or components → chosen design → trade-off → failure boundary.

**Editorial treatment:** Pragmatic and constraint-led. Use causal language such as “because,” “therefore,” and “at the cost of.” Emphasize boundaries, dependencies, and trade-offs without presenting context-dependent choices as universal best practices.

**Required proof:** architecture/code artifact, explicit assumptions, and at least one operational consequence such as latency, cost, observability, security, or recovery.

**Avoid:** decorative box-and-arrow diagrams with no decision or boundary.

## Production AI Failure File

**Use for:** incidents, failed runs, bad outputs, debugging, evaluation misses, or reliability lessons.

**Core movement:** symptom → evidence → root cause → fix → verification → prevention.

**Editorial treatment:** Forensic, calm, and blame-free. Move one causal step at a time. Favor “reproduced,” “traced,” “isolated,” “verified,” and “remains unknown.” Keep drama and certainty below the evidence.

**Required proof:** sanitized trace, output, test, diff, or reproduction. State what remains unknown.

**Avoid:** manufactured drama, invented incidents, blame, or claiming causality from correlation.

## Product Proof

**Use for:** a working app, feature, integration, prototype, or before/after behavior.

**Core movement:** user problem → live behavior → relevant implementation choice → constraint → next test.

**Editorial treatment:** Concrete and behavior-first. Describe user action and observable system response with active verbs and minimal adjectives. Prefer inputs, outputs, state changes, and constraints over feature-tour or hype language.

**Required proof:** working capture or artifact. Distinguish prototype behavior from production readiness.

**Avoid:** UI tours that never show the product claim working.

## Engineering Field Notes

**Use for:** changed beliefs, course-to-product connections, mistakes, and first-hand learning.

**Core movement:** prior assumption → concrete trigger → changed judgment → application to AI product work → focused invitation.

**Editorial treatment:** Candid, first-person, and low-ego. Contrast the prior judgment with the evidence that changed it and the behavior that changes next. Keep the lesson specific rather than motivational or guru-like.

**Required proof:** honest first-hand detail or a linked artifact; citations when the lesson depends on an external fact.

**Avoid:** certificate announcements without changed judgment, generic motivation, or borrowed authority.

## Technical Analysis Brief

**Use for:** timely named-product, model, framework, or platform changes.

**Core movement:** what changed → source-backed fact → practical consequence → who should act → uncertainty/watch item.

**Editorial treatment:** Concise, dated, and conditional. Separate documented facts, practical implications, and watch items. Favor “as of,” “if,” “depends on,” and “not yet known.” Avoid urgency or FOMO unsupported by product impact.

**Required proof:** current primary source and, when possible, a direct test. Date time-sensitive claims.

**Avoid:** release-note paraphrases, speculation presented as fact, or urgency without product impact.

## Drafting constraints

- Write for full-stack engineers becoming AI Product Engineers.
- Keep one main idea, one audience, one goal, and one CTA.
- Lead with the concrete tension, result, failure, or decision—not a generic audience judgment.
- End with a question only when a practitioner's experience could materially extend the post.
- Use analogies only when they reduce conceptual distance; never require one.
- Use a soft follow CTA at most once per week.
- Never claim or simulate a “top 1%” persona, copy an influencer's signature style, or guarantee performance.
