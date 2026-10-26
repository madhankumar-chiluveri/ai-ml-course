---
post_id: LI-###
status: brief
scheduled_at: YYYY-MM-DDTHH:MM:SS+05:30
timezone: Asia/Kolkata
pillar: authority
format: text
instagram_format: carousel
primary_goal: saves
instagram_primary_goal: saves
audience:
research: ../research/LI-###-topic.html
course_source:
published_url:
instagram_published_url:
---

# Working Post Title

## Shared strategy

- **Topic:** The one concept both platform versions will teach.
- **Evidence and limits:** Link the interactive HTML research artifact (`../research/LI-###-topic.html`), proof, trace, or confirmed experience. State the boundary that keeps the claim honest.
- **AI-product connection:** Explain the component, failure, trade-off, or decision this concept changes.

## LinkedIn

### Chosen format

Name exactly one LinkedIn format and why it fits the information shape. Do not list alternatives.

### Working hook

Reference the first line under **Final copy**; do not duplicate it here.

### Reader promise

State what the intended reader will understand, decide, or do differently.

### Draft structure

1. Hook and stakes.
2. Evidence or concrete example.
3. Explanation or decision framework.
4. Practical takeaway.
5. Specific CTA.

### Asset brief

For an image, document, or video, describe only what the chosen native asset must communicate. For text, say why no asset strengthens the post.

### CTA

Ask for one specific experience, a decision, or a technical counterexample.

### Final copy

Write the sole canonical publishable LinkedIn copy here. Make it directly pasteable: use sparse Unicode bold for intentional emphasis, not Markdown `**`/`__` markers, and do not use backticks as visual formatting. Keep code identifiers, URLs, and hashtags in plain ASCII. Do not repeat the final copy elsewhere in the repository or assistant response.

### AI assistant prompt

~~~~text
You are editing one evidence-led LinkedIn [chosen format] post for [audience].

Use only this brief and its linked study/research note:
- Topic: [topic]
- Reader outcome: [reader promise]
- Evidence and limit: [evidence / limitation]
- AI-product connection: [connection]
- CTA: [CTA]

Produce only the chosen format. Open with a concrete tension, result, failure, or decision; explain the engineering consequence; then give the practical takeaway. Make the result directly pasteable in LinkedIn: use sparse Unicode bold for intentional emphasis and no Markdown emphasis markers or backticks. Do not invent proof, production experience, metrics, external citations, or a claim about "most developers." Do not add a different LinkedIn format. Use 0–3 relevant hashtags only if they improve discovery. Store the full final copy only once.
~~~~

## Instagram

### Chosen format

Name exactly one Instagram format and why it best carries the same idea for a visual-first, mobile audience. Do not list alternatives.

### Production plan

For a carousel: write every slide's exact copy and visual direction. For a Reel: write timestamps, on-screen text, voiceover, and capture direction. For a single image: write the exact card copy, visual hierarchy, and alt text. For a text-led Story sequence: write each frame and interaction sticker.

### Caption

Write the publishable caption with one save, comment, or share action; three to five relevant hashtags; SEO keywords in the opening lines; and concise alt text.

### AI assistant prompt

~~~~text
Create exactly one Instagram [chosen format] for [audience] about [topic].

Use only this brief and its linked study/research note:
- Main idea: [main idea]
- Evidence and limit: [evidence / limitation]
- AI-product connection: [connection]
- Desired action: [save, comment, or share]

Use a clear first-frame hook and one idea per visual unit. Include only the production plan, publishable caption, 3–5 relevant hashtags, and alt text for the selected format. Preserve the evidence boundary. Do not invent a demo, screenshot, result, or external authority. Do not offer a Reel, image, or carousel alternative.
~~~~

### Visual style prompt

Include only when the chosen Instagram format has a visual asset.

~~~~text
Use the personal AI Product Engineer visual system: #0B1220 ink, #F8FAFC paper, #94A3B8 secondary labels, #38BDF8 signal, #22C55E verified state, #F59E0B constraint, and #F43F5E failure. Use a modern sans-serif, left alignment, generous margins, simple solid shapes, and 2 px connectors. Make the evidence the main visual object. Avoid stock AI brains, robots, neon circuits, generic gradients, unreadable microcopy, and another creator's signature layout. Keep contrast accessible and make every key label readable on a phone.
~~~~
