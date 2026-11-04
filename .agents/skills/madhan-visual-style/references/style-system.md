# Madhan Default Visual System

## Design intent

Make dense technical ideas feel obvious at first glance. Combine editorial hierarchy with readable annotation and accurate technical relationships. For social posts, follow the recorded per-post choice between image-generated character scenes and SVG cartoons and diagrams; keep the visual identity consistent in either medium.

The source references in `C:\Users\madhankumar.ch\Downloads\style-ref` contribute only broad traits: an off-white paper field, oversized black headlines, pastel explanatory cards, thin ink outlines, and occasional handwritten notes. Do not copy their creator identity, handle, slide numbering pattern, exact compositions, or proprietary illustrations.

## Core tokens

| Token | Value | Purpose |
|---|---|---|
| Paper | `#FBF8F1` | Warm primary canvas |
| Ink | `#111318` | Headlines and primary text |
| Note | `#2246A8` | Handwritten annotations and connectors |
| Mint | `#DDF6E9` | Durable/verified or safe state |
| Lilac | `#ECE6FF` | Semantic/model or transformation state |
| Butter | `#FFF1B8` | Decision, constraint, or takeaway |
| Rose | `#FFE2E8` | Risk, failure, or destructive outcome |
| Sky | `#DFF2FF` | Neutral system or input state |
| Muted | `#5D6470` | Secondary copy |
| Rule | `#CDD3DC` | Dividers and quiet borders |

Preserve semantic meaning when another project system already assigns colors. Use these pastels as surfaces, not as saturated full-canvas backgrounds.

## Typography

- Headline: normal-width Inter, Work Sans, Arial, or a similarly readable sans-serif, usually bold with line height around `1.05-1.15`. Avoid compressed heavy faces that close counters or fuse adjacent glyphs.
- Technical labels: Inter, Work Sans, Arial, or system sans, weights 600-700.
- Body: Inter, Arial, or system sans, weights 400-600 and line height `1.25-1.4`.
- Annotation: a readable normal-width sans-serif. Use handwriting only when explicitly requested.
- Keep clear separation between every letter and word. Avoid negative tracking, touching glyphs, overlapping text, and artificially compressed word spaces. Shorten or reflow copy instead of squeezing it to fit.

## Composition

- Use a 12-column grid and generous outer padding: 64-76 px on a 1080 px canvas.
- Reserve roughly the top 25-32% for the topic label, headline, and one-sentence framing.
- Use one dominant evidence object below: aligned cards, a single flow, a comparison, or one result.
- Prefer asymmetry in the header and strict alignment in the technical body.
- Use 20-28 px rounded corners, 2 px ink or tinted outlines, and either no shadow or one subtle paper-lift shadow.
- Add at most two small sketch marks, arrows, or underlines. They must clarify reading order.
- Finish with a quiet footer: series label on the left, the exact public credit `madvibe.ai` on the right.

## Information-shape patterns

### Architecture

Use one left-to-right or top-to-bottom reading direction. Give each boundary a verb-led label, then show the store, service, or component. Add a final decision strip with the governing questions.

### Comparison

Use aligned columns with identical row order. Highlight the decision criterion, not a winner. Avoid checkmark overload.

### Result

Make the measured output the largest object after the headline. Keep setup and limitation in separate short strips.

### Sequence

Use three to five numbered stages. Keep arrows simple and avoid crossing connectors.

## Mobile clarity gate

- Keep the headline under 12 words when possible.
- Keep a single-image card near 25-45 visible words; exceed this only for essential evidence.
- Use at least 34 px body text and 28 px secondary text on a 1080 x 1350 canvas.
- Check that no card contains more than three short lines beneath its label.
- For code-native assets, treat 1080 x 1350 as the logical layout and render at device scale 2 for final 2160 x 2700 PNGs. For generated social assets, request the strongest suitable native detail and retain the generation source and prompt.
- Preserve vector text and diagrams in carousel PDFs when the selected source is code-native. Keep one final PNG per page; add lower-resolution copies only when requested.
- Preserve generated artwork at supported native quality. Enlarging existing pixels does not add detail; verify text in the final export.
- Inspect the final PNG at full size and roughly 360 px width. Check word boundaries, letter separation, open counters, line spacing, and reading order without zooming.

## Rejection conditions

Reject the asset if it contains clipped text, generated gibberish, touching or overlapping letters, merged words, unreadable counters, more than one primary idea, decorative AI brains or robots, neon gradients, unclear arrows, borrowed handles, or a composition close enough to a reference that it could be mistaken for that creator's work.
