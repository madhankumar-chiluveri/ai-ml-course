---
name: engineering-humour
description: >-
  Develop relatable engineering humour for Madhan's LinkedIn and Instagram content, pairing a technically sound scenario with an original visual punchline. Use for funny posts, engineering memes, developer frustrations, or humorous treatments of course concepts. Supports ideas, design briefs, and explicitly requested production assets.
---

# Engineering Humour

Turn a recognisable engineering frustration into one visual joke. The reader should recognise the situation before reading an explanation.

## Fit the content system

Read [the social content rules](../../README.md) for the active course phase, audience, and publishing workflow.
Use the workspace `linkedin-content-system` skill for positioning, evidence, platform adaptation, and production delivery.
Humour is an editorial treatment. Keep the existing pillar and goal; community content is a common fit.

For a humour-first brief, keep the joke structure intact. Do not automatically expand it into a serious failure-file or field-note template.
Use those archetypes when humour supports an actual technical breakdown or confirmed learning story.

## Find the joke

1. Identify a specific situation the target engineer could recognise: input, action, expected result, and actual result.
2. Connect it to a concept in the active course phase and an AI-product consequence.
3. Identify the mismatch: misplaced confidence, repeated failure, hidden state, delayed output, or an inconvenient system response.
4. Choose one comic mechanism and write the shortest setup and punchline that preserve it.
5. Choose the visual scene after the mechanism. Use [scenario patterns](references/scenario-patterns.md) for grounded examples.
6. Test the premise and joke separately. Correct technical errors without adding an explanation to the punchline.

The premise must be specific enough that replacing the engineering terms with unrelated words would weaken the joke.
The humour should survive without a caption explaining why it is funny.

## Evidence without killing the joke

- Verify the technical premise through a course source, runnable example, confirmed experience, or primary documentation. Verify current product claims before production.
- Treat invented dialogue and exaggerated frustration as fictional scenes. Never present them as actual conversations, incidents, measurements, or personal experience.
- Keep essential source context in a short post note. Add an asset label when a realistic trace, screenshot, or figure could imply measured evidence.
- A clearly illustrated joke does not need a benchmark footer. A technical claim still needs support.
- Do not generalise a conditional failure into “AI always breaks code,” “async is slower,” or “all retries are bad.”
- Keep the joke aimed at the situation, the author's assumptions, or system friction. Avoid blaming an identifiable colleague or customer.

## Choose the design for the scene

Read [the design router](references/design-router.md) when choosing a layout or creating a visual brief.
Apply [style-ref-editorial](../style-ref-editorial/SKILL.md) for the default paper, typography, pastel surfaces, and blue notes.
Let the scenario determine the illustration: a queue, conversation, timeline, stale response, expectation split, or escalating sequence.

One joke often fits one image. Several panels within one image are still a single-image format.
Use a carousel only when revealing successive beats across pages materially improves the joke.
Do not turn every humorous post into the same four-panel grid or the previous technical carousel.

Use deterministic text and diagram rendering for exact labels. Use image generation when original characters, expressions, or illustrative scenes materially carry the joke.
When image generation applies, use the available imagegen workflow and preserve technical text through exact labels or a deterministic text layer.

## Match the requested mode

**Thoughts, ideas, or skill creation:** return a few relevant concepts and their proposed designs. Do not create finished post assets or assign publishing slots.

**Brief:** lock the situation, concept, technical premise, comic mechanism, exact on-image wording, visual scene, chosen format, goal, and evidence boundary.

**Production post:** use the project post template and stable ID. Deliver LinkedIn plus its Instagram adaptation unless the user requests LinkedIn only.
Keep the situation and visual punchline shared. Adapt captions and the reader action for each platform.
Store each complete caption once in the post file. Include brief source notes only when needed.
Create research files, explanatory HTML, simulators, or claim ledgers only when explicitly requested.

Keep captions short enough to let the image deliver the joke. Add one useful engineering sentence only when it improves the post.
A question or CTA is optional. Never require “comment a keyword,” tagging colleagues, or a long explanation of the punchline.

## Output for an idea or brief

Return the following, compactly:

- **Situation and grounding:** reader frustration, course concept, AI-product connection, and source or evidence needed.
- **Joke:** setup, punchline, and comic mechanism. Label invented scenes in the working brief.
- **Design:** exact on-image wording, visual action, composition, chosen native format, and alt-text direction.
- **Route:** pillar, primary goal, evidence confidence, and remaining work before production.

## Review before delivery

- **Recognition:** does the target engineer recognise the situation without reading a lesson first?
- **Timing:** does the strongest line or visual arrive last, without competing jokes?
- **Accuracy:** does the real mechanism support the premise, including its conditions?
- **Visual fit:** do the expressions, objects, or system states carry the punchline instead of decorating it?
- **Readability:** is the joke legible at feed width, with a clear reading order and concise alt text?
- **Originality:** is the scene original, without copied creator marks, artwork, or wording?

If the concept needs several explanatory paragraphs, simplify the joke or return it to a technical explainer.

## Learn from results

Treat broader appeal as a hypothesis. A supplied screenshot's reactions do not establish a reach or conversion advantage.
Use the existing metrics framework to assess relevant responses and profile interest across several comparable posts.
Keep humour occasional until actual results support a cadence. Do not replace the engineering series or promise virality.

## Invocation example

> Use the engineering-humour skill to suggest three original jokes from the current course phase. Give each a technical premise, short setup and punchline, suitable visual scene, and evidence boundary. Recommend one concept. Return briefs only.
