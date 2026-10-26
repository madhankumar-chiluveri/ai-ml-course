# Madhan Default Visual System

## Design intent

Make dense technical ideas feel obvious at first glance. Combine editorial hierarchy with human annotation, while keeping every diagram deterministic and exact.

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

- Headline: Arial Black, Inter Black, or system heavy sans; tight line height around `0.92-1.00`.
- Technical labels: Inter, Arial, or system sans, weights 600-800.
- Body: Inter, Arial, or system sans, weights 400-600 and line height `1.25-1.4`.
- Annotation: Segoe Print or a restrained handwritten fallback, used only for short clarifiers.
- Never use handwriting for data, code, long paragraphs, or accessibility-critical labels.

## Composition

- Use a 12-column grid and generous outer padding: 64-76 px on a 1080 px canvas.
- Reserve roughly the top 25-32% for the topic label, headline, and one-sentence framing.
- Use one dominant evidence object below: aligned cards, a single flow, a comparison, or one result.
- Prefer asymmetry in the header and strict alignment in the technical body.
- Use 20-28 px rounded corners, 2 px ink or tinted outlines, and either no shadow or one subtle paper-lift shadow.
- Add at most two small sketch marks, arrows, or underlines. They must clarify reading order.
- Finish with a quiet footer: series label on the left, `Madhan Kumar` on the right.

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
- Export at device scale 1 to preserve exact 1080 x 1350 dimensions.
- Inspect the final PNG, not only the HTML source.

## Rejection conditions

Reject the asset if it contains clipped text, generated gibberish, more than one primary idea, decorative AI brains or robots, neon gradients, unclear arrows, borrowed handles, or a composition close enough to a reference that it could be mistaken for that creator's work.
