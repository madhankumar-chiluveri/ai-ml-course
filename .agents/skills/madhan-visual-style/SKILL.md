---
name: madhan-visual-style
description: Apply Madhan's default visual system to social cards, LinkedIn or Instagram assets, technical diagrams, carousels, posters, and educational graphics. Use whenever a visual is requested for this workspace and the user does not name another style, or when the user asks for the style-ref look, clear editorial visuals, exact readable text, pastel technical cards, or hand-annotated diagrams.
---

# Madhan Visual Style

Create original, mobile-legible technical visuals with a strong editorial headline, calm paper canvas, structured pastel evidence cards, and restrained hand-drawn annotations. Treat the system as the workspace default unless the user explicitly supplies another style.

## Workflow

1. Read [references/style-system.md](references/style-system.md) before designing.
2. Identify the information shape: one result, comparison, architecture, sequence, failure, or takeaway.
3. Reduce the asset to one claim and the smallest supporting structure.
4. For exact technical text, diagrams, tables, or charts, build in HTML/CSS/SVG from [assets/base-card.html](assets/base-card.html). Do not rely on generated raster text.
5. Use image generation only for a photographic or illustrative element that cannot be represented clearly with code-native shapes. Keep all labels code-native.
6. Render with [scripts/render-card.ps1](scripts/render-card.ps1), inspect the PNG at full resolution, and reject any clipped, tiny, or ambiguous text.

## Non-negotiable gates

- Preserve exact wording, spelling, numbers, and technical relationships.
- Make the claim readable at feed width; body text must remain readable without zooming.
- Use one dominant headline, one reading direction, and no more than one handwritten annotation style.
- Keep evidence visually dominant; decoration must not compete with it.
- Meet WCAG AA contrast and add labels or shapes so color is never the only signal.
- Use the user's name or project series mark only. Never reproduce another creator's handle, signature composition, proprietary illustration, or recognizable brand identity.
- Treat supplied references as mood and design-principle inputs, not templates to clone.

## Output contract

- Default social card: 1080 x 1350 PNG, with its editable HTML/SVG source retained beside it.
- Include concise alt text describing the claim and evidence.
- Report the saved source and rendered asset paths.
- If a post system owns colors or evidence semantics, preserve those meanings while applying the layout and texture rules from this skill.
