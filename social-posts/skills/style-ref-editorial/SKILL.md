---
name: style-ref-editorial
description: >-
  Create original LinkedIn and Instagram carousels or technical cards using Madhan's saved style-ref treatment: warm paper, oversized black headlines, pastel diagrams, and readable blue annotations. Use for social visuals in this workspace or an explicit style-ref request.
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
4. Follow the per-post visual decision from `linkedin-content-system`: image-generated character scenes or SVG cartoons and diagrams. Choose expressive generated scenes when human action carries the story; choose SVG when exact labels, geometry, or data paths carry the explanation. Reassess for each post and verify every word and technical relationship.
5. Use a readable sans-serif with clear gaps between letters and words. Choose normal-width type, open counters, and moderate weight. Avoid negative tracking, touching glyphs, compressed heavy headlines, and handwriting fonts unless explicitly requested. Inspect at feed size and regenerate cramped type.
6. Vary composition with the information: a causal path, aligned comparison, timeline, branching decision, or trace.
7. Use `madvibe.ai` as the public visual credit. Omit publication and edition dates from artwork and public captions unless explicitly requested; keep source dates and verification timestamps in internal source notes. Export the chosen assets and inspect their mobile readability and rendered boundaries.

## Mad character

- When the post benefits from a personal character, use [Mad's original portrait](../../assets/mad-character.png) or the [alternate mascot](../../assets/mad-mascot.png), according to the brief. Make Mad a participant in the story: give him a role and a visible action tied to the slide's idea. Avoid detached corner portraits or decorative stickers.
- Preserve the established character's illustration quality and identity. Do not substitute a crude geometric likeness merely because the surrounding diagram uses SVG. Choose direct image generation when it better preserves the character and integrates the scene.
- Keep character appearances below 50% of carousel pages, counting both Mad and supporting characters. A five-page carousel may use characters on at most two pages. Reserve those scenes for moments that benefit from human action or reaction.
- Adapt Mad's outfit to the post when useful. Preserve his recognizable hair, skin tone, facial hair, and identity using the existing character as a reference.
- Plan each appearance around the situation: what Mad sees, does, says, or reacts to. Match his gaze, facial expression, gesture, and pose to that action. Generate a suitable variation when the existing pose does not fit. Check facial features, hands, prop contact, and readability at feed size.
- Add original supporting characters when the story needs another participant, such as a teammate, reviewer, or clearly labeled agent. Give each one a useful role; omit characters that add no meaning. Compose characters, props, speech bubbles, and diagrams as one scene, with clear reading order and no text collisions. Keep labels and dialogue exact and readable.
- Inspect anatomy before accepting a scene: trace each visible arm from its own shoulder through elbow and wrist to its hand. Verify one anatomical left hand and one right hand, not just a count of two hands. Reject both hands appearing to emerge from the same side, duplicated handedness, detached wrists, or implausible connections. Prefer a simple pose with both arm chains visible when occlusion makes the anatomy ambiguous. Check fingers, gaze, prop contact, bubble tails, connectors, and alignment; regenerate faulty artwork rather than hiding it.

## Carousel guidance

- Use a sequence when the reader must follow diagnosis, evidence, mechanism, decision, and prevention. Do not force a fixed page count.
- Start with a concrete tension. Give each interior page one engineering question and one primary evidence object.
- Make explanatory pages self-contained: define new terms, annotate the causal steps with readable sentences, and show repetition or a worked example when needed. Increase text or page count when clarity requires it; do not reduce an explanation to hardware labels or rely on the caption to fill its gaps.
- Maintain typography, margins, color meanings, and author placement across the sequence. Vary the diagrams to avoid repeated card layouts.
- End with a usable decision rule or specific practitioner question. Use the goal from the post brief.
- Design on a logical 1080 × 1350 canvas. Render final PNG pages at 2160 × 2700 from editable source at 2× scale.
- Package generated slide artwork as an image-based LinkedIn PDF. Preserve vectors when a code-native diagram is selected. Keep native generated source, prompts, and one final PNG per page, without redundant lower-resolution copies.
- Keep editable source and accessible text beside the exports. Include page-specific alt text in the post file.

## Boundaries

- Do not reproduce another creator's handle, distinctive composition, signature badges, people, or proprietary artwork.
- Preserve meaningful detail from the references: pastel groupings, illustrated connectors, ink hierarchy, and short blue annotations in readable type.
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

> Apply the style-ref-editorial skill to this approved brief. Honor its recorded choice of image-generated character scenes or SVG cartoons and diagrams; decide and explain the treatment first if missing. Use warm paper, clearly spaced normal-width editorial type, pastel diagrams, thin ink outlines, and readable blue notes. Preserve exact labels and the evidence boundary. Use madvibe.ai as the public credit. Return 2160 × 2700 PNGs, the selected carousel PDF, selected production source, and page-specific alt text.
