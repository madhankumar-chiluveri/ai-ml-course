---
post_id: LI-011
status: review
scheduled_at: 2026-10-15T08:30:00+05:30
timezone: Asia/Kolkata
pillar: authority
format: single_image
instagram_format: single_image
primary_goal: saves
instagram_primary_goal: saves
audience: full-stack engineers moving into AI product engineering
course_source: ../../../../course-path/phase-0-engineering-foundations/15_postgres_pgvector_redis.md
asset: ../assets/LI-011-three-state-decisions.png
asset_source: ../assets/LI-011-three-state-decisions.html
published_url:
instagram_published_url:
---

# Three State Decisions for an AI Product

## Shared strategy

- **Topic:** Separate durable relational state, semantic vector retrieval, and expiring operational state by workload.
- **Evidence and limits:** Topic 0.15 plus current pgvector and Redis primary documentation. This is a design heuristic, not a benchmark or a universal rule; pgvector runs inside PostgreSQL, while Redis persistence remains configurable.
- **AI-product connection:** The boundary affects crash recovery, retrieval behavior, cache invalidation, and rate limiting.

## Shared asset

- **File:** `../assets/LI-011-three-state-decisions.png`
- **Editable source:** `../assets/LI-011-three-state-decisions.html`
- **Canvas:** 1080 × 1350 portrait, shared across LinkedIn and Instagram.
- **Alt text:** Architecture decision card separating three AI-product state jobs: PostgreSQL for state that must survive restart, pgvector inside PostgreSQL for similarity search, and Redis for short-lived cache and rate-limit state. The decision rule is query shape plus durability plus lifetime.

## LinkedIn

### Chosen format

Single-image architecture card plus concise technical copy. The visual makes the three boundaries scannable, while the copy explains that pgvector is inside PostgreSQL and qualifies the heuristic.

### Working hook

See the first line under **Final copy**. It is the single canonical hook.

### Reader promise

Choose a storage boundary by query shape, durability, and lifetime instead of treating every form of AI state as interchangeable memory.

### Draft structure

1. Name the false equivalence between the three tools.
2. Separate the three workload questions.
3. Clarify that pgvector is a PostgreSQL extension.
4. Give the three-part selection rule.
5. Invite a concrete architecture comparison.

### Asset brief

Show one AI backend divided into three state decisions: must survive, must match, and may expire. Label pgvector as “inside PostgreSQL.” Use the Madhan default editorial style with exact code-native text, warm paper, bold black headline, pastel technical cards, and restrained blue handwritten annotation. Do not imitate the reference creator’s exact composition or identity.

### CTA

Ask readers where they draw the boundary between durable history, semantic retrieval, and short-lived operational state.

### Final copy

𝐏𝐨𝐬𝐭𝐠𝐫𝐞𝐬, 𝐩𝐠𝐯𝐞𝐜𝐭𝐨𝐫 𝐚𝐧𝐝 𝐑𝐞𝐝𝐢𝐬 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐭𝐡𝐫𝐞𝐞 𝐢𝐧𝐭𝐞𝐫𝐜𝐡𝐚𝐧𝐠𝐞𝐚𝐛𝐥𝐞 “𝐦𝐞𝐦𝐨𝐫𝐲” 𝐨𝐩𝐭𝐢𝐨𝐧𝐬.

They answer three different questions.

𝟏. 𝐖𝐡𝐚𝐭 𝐦𝐮𝐬𝐭 𝐬𝐭𝐢𝐥𝐥 𝐛𝐞 𝐭𝐫𝐮𝐞 𝐚𝐟𝐭𝐞𝐫 𝐚 𝐫𝐞𝐬𝐭𝐚𝐫𝐭?

PostgreSQL: users, documents, run history and durable agent checkpoints.

𝟐. 𝐖𝐡𝐚𝐭 𝐦𝐮𝐬𝐭 𝐛𝐞 𝐟𝐨𝐮𝐧𝐝 𝐛𝐲 𝐬𝐢𝐦𝐢𝐥𝐚𝐫𝐢𝐭𝐲?

pgvector: embeddings and nearest-neighbour search. It is an extension inside PostgreSQL, not automatically another database.

𝟑. 𝐖𝐡𝐚𝐭 𝐨𝐧𝐥𝐲 𝐦𝐚𝐭𝐭𝐞𝐫𝐬 𝐟𝐨𝐫 𝐚 𝐥𝐢𝐦𝐢𝐭𝐞𝐝 𝐭𝐢𝐦𝐞?

Redis: rate-limit counters, short-lived caches and keys with explicit expiry.

𝐓𝐡𝐞 𝐏𝐡𝐚𝐬𝐞 𝟎 𝐫𝐮𝐥𝐞 𝐈 𝐚𝐦 𝐤𝐞𝐞𝐩𝐢𝐧𝐠:

𝐂𝐡𝐨𝐨𝐬𝐞 𝐬𝐭𝐨𝐫𝐚𝐠𝐞 𝐛𝐲 𝐪𝐮𝐞𝐫𝐲 𝐬𝐡𝐚𝐩𝐞, 𝐝𝐮𝐫𝐚𝐛𝐢𝐥𝐢𝐭𝐲 𝐚𝐧𝐝 𝐥𝐢𝐟𝐞𝐭𝐢𝐦𝐞—𝐧𝐨𝐭 𝐛𝐲 𝐰𝐡𝐢𝐜𝐡𝐞𝐯𝐞𝐫 𝐭𝐨𝐨𝐥 𝐢𝐬 𝐚𝐥𝐫𝐞𝐚𝐝𝐲 𝐢𝐧 𝐭𝐡𝐞 𝐬𝐭𝐚𝐜𝐤.

A cache entry can be rebuilt.
A lost checkpoint can break recovery.
A similarity query needs a vector distance operation, not a normal relational lookup.

These are workload defaults, not universal laws. PostgreSQL can hold temporary data, and Redis can be configured for persistence.

Where do you draw this boundary in your AI backend?

#AIEngineering #PostgreSQL #Redis

### AI assistant prompt

~~~~text
You are editing one evidence-led LinkedIn single-image post for full-stack engineers moving into AI product engineering.

Use only this brief and its linked course source:
- Topic: storage boundaries for durable state, semantic retrieval, and expiring operational state
- Reader outcome: choose storage by query shape, durability, and lifetime
- Evidence and limit: Topic 0.15 plus current pgvector and Redis documentation; this is a design heuristic, not a benchmark or universal law
- AI-product connection: recovery, retrieval, cache invalidation, and rate limiting
- CTA: ask where the reader draws these storage boundaries

Produce only the chosen format. Open with the false equivalence between the tools, explain that pgvector is an extension inside PostgreSQL, and give the practical three-question framework. Make the result directly pasteable in LinkedIn: use sparse Unicode bold for intentional emphasis and no Markdown emphasis markers or backticks. Do not invent proof, production experience, metrics, external citations, or claims about “most developers.” Do not add a different LinkedIn format. Use no more than three relevant hashtags. Store the full final copy only once.
~~~~

## Instagram

### Chosen format

One 4:5 single-image architecture card. The decision model is complete on one mobile-readable canvas and does not need a carousel sequence.

### Production plan

- **Eyebrow:** `AI PRODUCT STORAGE · PHASE 0`
- **Headline:** `One AI product. Three state decisions.`
- **Annotation:** `same backend ≠ same job`
- **Card 1:** `MUST SURVIVE` / `PostgreSQL` / `Users · run history · checkpoints` / `What must still be true after restart?`
- **Card 2:** `MUST MATCH` / `pgvector` / `Embeddings · semantic retrieval` / `Inside PostgreSQL` / `What is similar?`
- **Card 3:** `MAY EXPIRE` / `Redis` / `Rate limits · short-lived cache` / `What only matters right now?`
- **Decision strip:** `Choose by QUERY SHAPE + DURABILITY + LIFETIME`
- **Footer:** `RELIABLE AI PRODUCT ENGINEERING` / `Madhan Kumar`
- **Visual direction:** Use the workspace default style from `$madhan-visual-style`: warm paper, editorial black headline, structured pastel bands, thin ink lines, one blue handwritten annotation, and exact code-native labels.

### Caption

PostgreSQL, pgvector and Redis solve different AI product storage jobs.

PostgreSQL holds state that must survive. pgvector adds similarity search inside PostgreSQL. Redis fits short-lived counters, caches and expiring keys.

The practical decision is not “Which database is best?”

Ask instead:
• What query must this support?
• Can the state be lost?
• How long should it live?

Save this architecture boundary for your next AI backend design.

#AIEngineering #PostgreSQL #pgvector #Redis #SystemDesign

Alt text: Architecture decision card separating PostgreSQL for durable state, pgvector inside PostgreSQL for vector similarity search, and Redis for short-lived cache and rate-limit state.

### AI assistant prompt

~~~~text
Create exactly one Instagram single-image post for full-stack engineers moving into AI product engineering about storage boundaries across PostgreSQL, pgvector, and Redis.

Use only this brief and its linked course source:
- Main idea: choose storage by query shape, durability, and lifetime
- Evidence and limit: Topic 0.15 plus current primary documentation; this is a workload heuristic, not a universal law
- AI-product connection: crash recovery, semantic retrieval, cache behavior, and rate limiting
- Desired action: save the architecture boundary

Use one 4:5 card with exact mobile-readable labels. Include only the production plan, publishable caption, three to five relevant hashtags, and alt text for the selected format. Preserve the evidence boundary. Do not invent a benchmark, screenshot, production incident, or external authority. Do not offer a Reel or carousel alternative.
~~~~

### Visual style prompt

~~~~text
Use `$madhan-visual-style` as the default system. Build the card deterministically in HTML/CSS/SVG so every technical label is exact and readable. Use warm paper, an oversized black editorial headline, pastel technical surfaces, thin ink outlines, and one restrained blue handwritten annotation. Preserve semantic status through labels as well as color. Do not reproduce another creator’s handle, exact composition, signature numbering system, or proprietary illustration. Avoid AI brains, robots, neon circuits, gradients, and microcopy.
~~~~
