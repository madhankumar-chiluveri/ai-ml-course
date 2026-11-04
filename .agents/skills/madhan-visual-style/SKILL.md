---
name: madhan-visual-style
description: Apply Madhan's default visual system to social cards, LinkedIn or Instagram assets, technical diagrams, carousels, posters, and educational graphics. Use whenever a visual is requested for this workspace and the user does not name another style, or when the user asks for the style-ref look, clear editorial visuals, exact readable text, pastel technical cards, or hand-annotated diagrams.
---

# Madhan Visual Style

Create original, mobile-legible technical visuals with a clear editorial headline, calm paper canvas, structured pastel evidence cards, and readable annotations. Treat the system as the workspace default unless the user explicitly supplies another style.

## Workflow

1. Read [references/style-system.md](references/style-system.md) before designing.
2. Identify the information shape: one result, comparison, architecture, sequence, failure, or takeaway.
3. Reduce the asset to one claim and the smallest supporting structure.
4. For each social post, follow the `linkedin-content-system` decision between image-generated character scenes and SVG cartoons and diagrams. Choose from the topic's storytelling and precision needs; announce and record the rationale before production. Specify exact text and readable spacing; verify every word and technical relationship.
5. Use HTML/CSS/SVG from [assets/base-card.html](assets/base-card.html) when exact charts, technical diagrams, or editable UI make a code-native approach suitable. Choose the medium for the asset's accuracy and editing needs.
6. Inspect every final PNG at full size and roughly 360 px feed width. Reject touching letters, merged words, closed counters, clipping, or ambiguous text. For code-native assets, use [scripts/render-card.ps1](scripts/render-card.ps1) at its default 2× scale.

## Non-negotiable gates

- Preserve exact wording, spelling, numbers, and technical relationships.
- Make the claim readable at feed width; body text must remain readable without zooming.
- Use normal-width type with visible separation between letters and words. Avoid compressed heavy headings, negative tracking, and glyphs that touch or overlap.
- Use one dominant headline, one reading direction, and no more than one handwritten annotation style.
- Keep evidence visually dominant; decoration must not compete with it.
- When characters serve the story, give each a clear role and action. Match expression, gaze, pose, and prop interaction to the situation. Add supporting characters only when they explain the idea; avoid detached avatar stickers. For social posts, follow the [social editorial guidance](../../../social-posts/skills/style-ref-editorial/SKILL.md) for Mad references, character frequency, and date treatment.
- Validate human anatomy and scene alignment in the final render. Trace limbs to their shoulders and inspect hands, prop contact, bubble tails, and connectors; regenerate visible mistakes.
- Meet WCAG AA contrast and add labels or shapes so color is never the only signal.
- Use `madvibe.ai` as the public visual credit. Never reproduce another creator's handle, signature composition, proprietary illustration, or recognizable brand identity.
- Treat supplied references as mood and design-principle inputs, not templates to clone.

## Output contract

- Default 4:5 social card: 2160 x 2700 PNG. For generated artwork, request suitable native detail and retain the generation source and prompt; for code-native artwork, render the editable 1080 x 1350 layout at 2× scale.
- Keep one final PNG per page and the selected production source. Preserve vector text and diagrams in carousel PDFs when the chosen source is code-native. Lower-resolution copies require a request.
- Include concise alt text describing the claim and evidence.
- Report the saved source and rendered asset paths.
- If a post system owns colors or evidence semantics, preserve those meanings while applying the layout and texture rules from this skill.
