---
name: style-ref-editorial
description: >-
  Create original LinkedIn and Instagram carousels or technical cards using Madhan's saved style-ref treatment: warm paper, oversized black headlines, pastel diagrams, and blue handwritten annotations. Use for social visuals in this workspace or an explicit style-ref request.
---

# Style Ref Editorial

Use the supplied references as a visual vocabulary. Build original compositions for Madhan's technical content.

## Reference material

Read [the design system](references/design-system.md) before creating an asset. View the relevant saved examples when composition matters:

- [Comparison](references/comparison.jpg): aligned pastel panels and a strong headline.
- [Decision primitives](references/primitives.jpg): grouped examples and labeled connectors.
- [Architecture](references/architecture.jpg): system boundaries, branching paths, and short annotations.

The examples are internal study material from the user's `Downloads/style-ref` folder. Their claims and figures are not technical evidence.
Use [the source manifest](references/source-manifest.json) to identify the original files and verify the saved copies.
Bundled OFL fonts and their licenses live in `assets/fonts/` for reproducible offline exports.

## Apply the treatment

1. Take the topic, evidence, platform, and chosen format from the post brief. This skill controls visual treatment.
2. Identify the physical mechanism or engineering decision. Make that the dominant diagram.
3. Use warm paper, a heavy black headline, pastel surfaces, thin ink strokes, and restrained blue notes.
4. Keep technical labels exact. Use SVG, HTML/CSS, or another deterministic renderer for text and diagrams.
5. Use handwriting for short annotations. Keep body text, code, figures, and essential labels in a readable sans-serif.
6. Vary composition with the information: a causal path, aligned comparison, timeline, branching decision, or trace.
7. Use `madvibe.ai` as the public visual credit. Export the chosen assets and inspect their mobile readability and rendered boundaries.

## Carousel guidance

- Use a sequence when the reader must follow diagnosis, evidence, mechanism, decision, and prevention. Do not force a fixed page count.
- Start with a concrete tension. Give each interior page one engineering question and one primary evidence object.
- Maintain typography, margins, color meanings, and author placement across the sequence. Vary the diagrams to avoid repeated card layouts.
- End with a usable decision rule or specific practitioner question. Use the goal from the post brief.
- Design on a logical 1080 × 1350 canvas. Render final PNG pages at 2160 × 2700 from editable source at 2× scale.
- Retain vector text and diagrams when packaging the sequence as a LinkedIn PDF. Keep one final PNG per page, without redundant lower-resolution copies.
- Keep editable source and accessible text beside the exports. Include page-specific alt text in the post file.

## Boundaries

- Do not reproduce another creator's handle, distinctive composition, signature badges, people, or proprietary artwork.
- Preserve meaningful detail from the references: pastel groupings, illustrated connectors, ink hierarchy, and short handwritten explanations.
- Do not reduce this treatment to plain corporate cards or add unrelated decorative AI imagery.
- Label simulations and illustrative data. Never draw a fake terminal capture, benchmark, or production incident.
- Keep delivery to the selected assets and captions. Add source notes in the post only when useful; separate study artifacts require explicit request.
- This skill grants no permission to publish or schedule. Keep original reference images out of publishing packages.

## Generated PNG upload preparation

Apply this metadata-only export by default to each generated PNG single-image post. Keep one final PNG and its generation prompt.
Use [scripts/prepare-png-upload.ps1](scripts/prepare-png-upload.ps1) to remove the PNG `caBX` Content Credentials chunk without changing raster data or other chunks.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File social-posts/skills/style-ref-editorial/scripts/prepare-png-upload.ps1 -InputPng <original.png> -OutputPng <upload-copy.png>
```

Verify matching dimensions, identical decoded pixels, and absence of a parsed `caBX` chunk in the prepared PNG.
Inspect PNG chunks with a format-aware parser; a raw byte search can match compressed image data.
After verification, replace the older workspace PNG with the prepared copy under the canonical filename. Remove the temporary duplicate.
Keep additional original versions only when the user requests them. Do not delete imagegen cache files outside the workspace.
Use the single final PNG in both platform sections and the post's asset field.
This preserves the artwork, canonical filename, and local post ID; the file hash changes when metadata is removed.
Do not promise an unchanged platform upload ID or a missing platform label. Check the fresh upload preview before scheduling.
The image remains AI-generated; metadata cleanup does not establish a different origin.

## Reusable prompt

> Apply the style-ref-editorial skill to this approved brief. Use warm paper, oversized black editorial type, pastel technical diagrams, thin ink outlines, and a few blue handwritten notes. Preserve exact technical labels and the evidence boundary. Use madvibe.ai as the public credit. Return 2160 × 2700 PNGs, vector carousel PDFs when selected, editable source, and page-specific alt text.
