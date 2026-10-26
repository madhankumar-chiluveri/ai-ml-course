---
name: linkedin-content-system
description: Plan, research, theme, draft, adapt, review, and improve evidence-led LinkedIn and paired Instagram content for an AI Product Engineer. Use when turning course lessons, engineering work, experiments, product news, or audience questions into social posts; selecting platform-native text, single-image, document/carousel, video, Reel, Story, or poll formats; creating a LinkedIn post with its Instagram adaptation in one pass; choosing editorial and visual treatments; coordinating writer, hook, humanizer, or repurposing skills; creating or updating weekly social-post files; auditing claims, positioning, voice, and assets; or learning from post metrics. Do not publish or schedule without explicit user approval.
---

# LinkedIn Content System

Build a recognizable evidence-led body of work, not generic “viral tech” content. Optimize for the intended audience's trust, qualified conversation, profile interest, and follower conversion. Treat impressions as one diagnostic, not the objective.

## Establish context

1. Search the current project for `social-posts/README.md`.
2. When present, read it before making content decisions. It owns positioning, audiences, pillars, format rules, evidence standards, naming, and workflow.
3. Read only the additional context needed for the task:
   - `social-posts/BACKLOG.md` for idea state and stable post IDs.
   - The active `social-posts/weeks/<date-range>/plan.md` for schedule and weekly hypotheses.
   - The selected post and research files for drafting or review.
   - `social-posts/audits/` and `strategy/metrics-framework.md` when interpreting performance.
4. If no content system exists, gather or infer the audience, positioning, topic, goal, firsthand insight, and available evidence. Do not create repository files unless the user asks.

Project context outranks generic platform heuristics. Label any unsupported recommendation as a hypothesis to test.

## Route every topic

Apply these gates in order:

### 1. Positioning gate

Require the topic to help the target reader build, debug, evaluate, secure, operate, or choose something related to reliable AI products. Reframe a foundation through its real AI consequence. Reject decorative “AI” framing and unrelated topic scatter.

Use this bridge for course material:

```text
learned concept
  → AI product component that depends on it
  → failure, trade-off, or decision
  → proof or source
  → practical engineering consequence
```

### 2. Evidence gate

Read [references/evidence-gate.md](references/evidence-gate.md) for any technical, numerical, comparative, personal, or time-sensitive claim.

- Never invent experience, incidents, benchmarks, customer results, or quotes.
- Require a reproducible experiment, trace, demo, primary source, or confirmed firsthand account for the central claim.
- Verify current framework, model, API, product, price, policy, or platform claims against primary documentation.
- State limitations near the result, not in a defensive footnote.
- Create a research file when the claim is not yet publication-ready.

### 3. Archetype gate

Read [references/post-archetypes.md](references/post-archetypes.md), then choose one structure based on the reader's problem and the available evidence. Do not force every post into hook → analogy → takeaways → infographic callout → CTA.

### 4. Format and theme gate

Read [references/topic-theme-router.md](references/topic-theme-router.md) before selecting a format or theme.

- Choose one default native format from the information shape: finding, sequence, behavior, point of view, or meaningful choice.
- Generate a visual only when it improves understanding or proves the claim.
- Prefer a real result card, chart, code/trace screenshot, annotated product screen, or architecture boundary over generic generated imagery.
- If an asset is appropriate, read [references/visual-brand-system.md](references/visual-brand-system.md). Preserve a consistent personal design system while varying only the topic treatment.

## Execute the requested task

### Idea or research recommendation

Return a routing card with:

- audience problem;
- AI-product connection;
- post pillar and primary goal;
- evidence required and current confidence;
- chosen archetype, editorial treatment, native format, and visual theme;
- working hook and specific CTA;
- next action required before drafting.

Do not write a full post unless requested.

### Weekly planning

Use three to five posts and at least three pillars. Vary goals across saves, comments, reposts, and likes without manufacturing engagement bait. Link stable `LI-###` IDs to the dated week's post files. Keep raw analytics out of the plan; append only a qualitative retrospective after the measurement window.

### Research

Generate research notes strictly as self-contained interactive HTML artifacts (`LI-###-topic.html`) using the `claude-artifact-creator` Flexoki + Atkinson Hyperlegible standard. Never use plain `.md` files for research explanations. Every research artifact must embed:
1. Mental model invariant hero card;
2. Interactive SVG simulation stage with step scrubber;
3. Dynamic telemetry inspector updating on step change;
4. Diagnostic sandbox with clickable real-world "break it" failure scenarios;
5. Interactive Claim Ledger maintaining confidence ratings, primary sources, proof limits, and publication rules.

### Drafting

Create or update the selected post file using the project's post template.

- Treat a production LinkedIn post request as a request for its Instagram adaptation in the same pass unless the user explicitly asks for LinkedIn only. Store both under the same stable post ID and research note.
- Lock the topic, central claim, evidence, limitation, audience outcome, and visual identity across platforms. Adapt the hook, length, CTA, hashtags, SEO wording, and native format without changing the underlying claim.
- Choose exactly one native format per platform. Reuse one 4:5 single-image asset when it remains legible and complete on both platforms; create platform-specific assets only when the information shape or safe area requires them.
- Write in the user's demonstrated voice and at the target reader's technical level.
- Simplify without flattening mechanisms or trade-offs.
- Use an analogy only when it clarifies more than code, a trace, or a diagram.
- Use the shortest length that completes the idea; respect LinkedIn's 3,000-character hard limit.
- Make LinkedIn final copy directly pasteable: do not use Markdown emphasis markers or backticks for visual formatting. Apply Unicode bold sparingly to the hook, key result, or takeaway; keep code identifiers, URLs, and hashtags in plain ASCII.
- Keep each platform's full publishable copy in exactly one canonical section of the post file. Do not repeat that copy in working hooks, prompts, plans, research notes, or the final assistant response; link to the canonical section instead.
- Make the opening specific and defensible. Never manufacture a statistic or use deficit framing such as “most developers” without evidence.
- Make the CTA goal-dependent and optional. Prefer a concrete experience, counterexample, decision, or next-breakdown choice.
- Use zero to three relevant hashtags only when they add discovery value.
- Output only the chosen platform assets. The paired Instagram adaptation is part of a production LinkedIn deliverable, but do not add unused alternative formats such as a second carousel, Reel, or infographic.
- Treat `recommend`, `propose`, `plan`, `brief`, `preview`, and `no edits` as non-production modes. Return copy or an asset brief only; do not invoke image/design tools or create files unless the user explicitly asks for the finished artifact without a conflicting preview-only constraint.

### Review

Audit positioning, evidence, voice, structure, format fit, accessibility, and AI-tell density. Report findings without rewriting unless the user asks for changes. If `scripts/validate_post.py` is available, run it on post files before declaring them ready.

### Measurement and iteration

After publication, record consistent 24-hour and 72-hour snapshots in the project's metrics dataset. Use `NA` for unavailable data; zero means measured zero. Update the weekly retrospective with interpretation and promote audience questions to the backlog. Do not declare a format, theme, hook, or posting-time winner from a single post.

## Hard rules

- Do not omit the paired Instagram adaptation from a production LinkedIn deliverable unless the user explicitly requests LinkedIn-only output.
- Do not claim to be a “top 1% influencer,” imitate a named creator's voice, or promise virality, reach, or follower growth.
- Do not use fabricated authority, borrowed brand identity, or another creator's signature layout.
- Do not force an infographic, carousel, analogy, CTA, hashtag count, length range, or posting time on every topic.
- Do not publish, schedule, comment, message, or tag anyone without explicit user approval.
- Do not expose employer, customer, repository, credential, or trace data that has not been approved for public use.
- Do not turn certificate completion or generic learning progress into a post unless it demonstrates changed engineering judgment.
- Do not let a downstream writer, humanizer, image generator, or publisher override this skill's positioning, evidence, and format decisions.
- When instructions conflict, a proposal-only or no-edit constraint outranks an embedded request to generate the asset; surface the proposed deliverable instead.

## Handoffs

- Use a LinkedIn account connector for bounded account/profile/post reads when the user requests live analysis.
- Before invoking any LinkedIn planner, writer, interviewer, hook, humanizer, or repurposing skill, read [references/downstream-skill-handoff.md](references/downstream-skill-handoff.md) and pass its locked route envelope. Treat the downstream skill as a bounded renderer, not a second strategy router.
- Use a specialized writer or humanizer only after routing the topic; pass it the selected audience, evidence, archetype, editorial treatment, format, visual theme, goal, and voice constraints.
- Use image generation only after selecting a visual asset and writing an evidence-grounded asset brief.
- Use a publisher only after showing the final copy, asset, account, and schedule and receiving explicit approval.

## Validation command

```powershell
python .agents/skills/linkedin-content-system/scripts/validate_post.py <post-file>
```

Use `--json` for machine-readable output and `--strict` when warnings must fail a review gate.
