---
name: claude-artifact-creator
description: Build visual-first HTML explainers, study notes, chapter pages and concept walkthroughs in the user's house style. The style is the Flexoki Inky Paper palette (#FFFCF0 canvas, #100F0F ink), Atkinson Hyperlegible type, box-and-pipe rails, side-by-side comparison splits, inline diagnostic cards, schematic SVG diagrams and to-scale charts. Everything sits on one continuous scroll, with nothing hidden behind clicks. Use this skill whenever the user asks for an HTML page, an .html file, an "artifact", an explainer, a visual explanation, or to turn notes, a markdown chapter, docs or a concept into something visual. Use it even when the wording is loose, such as "make this visual", "build a page for chapter 3" or "explain X as an artifact". Bundles the CSS design system, a chart engine, a stock-and-flow / architecture schematic engine, and build and verification scripts.
---

# Claude Artifact Creator

Produces pages for rapid conceptual onboarding. The reader should grasp the mechanism from the drawings first and read text second. Text exists to annotate visual nodes.

Bundled resources (paths relative to this skill's folder):

| Path | What it is | When to open it |
|---|---|---|
| `assets/base.css` | Full design system: tokens (light + dark), every component | Never edit per page. `build.py` inlines it. |
| `assets/defs.svg` | Arrow markers + cloud symbol used by the diagrams | Inlined by `build.py` |
| `assets/engine.js` | `AE.plot` / `AE.spark` charts, `AE.dg` schematics, `AE.spy` nav | Inlined by `build.py` |
| `references/components.md` | Markup for every HTML component | Before writing body markup |
| `references/engine-api.md` | Options for charts and schematics, with examples | Before writing the spec script |
| `scripts/build.py` | Assembles parts + assets into one file | Build step |
| `scripts/check.py` | Tag balance, script syntax, host ↔ spec cross-check | After every build |
| `scripts/browser-check.js` | In-browser overflow measurements | One look per page |

## Where the file goes

The user has a standing preference here, so do not ask:

- **The source is a file in a repo** (for example `chapters/chapter-02-x.md`): write `chapters/chapter-02-x.html` **next to it, with the same basename**. Make one `.html` per source file. When several sources are requested together, build one page per source and link the siblings from the header nav.
- **No source file or location**: write to the scratchpad and publish with the Artifact tool (`build.py --fragment`).
- Mermaid belongs only in `.md` files under `explanations/`. HTML pages draw diagrams with `AE.dg` or hand-written SVG, never Mermaid.

## Workflow

1. **Read every source file completely.** Make a content inventory: every fact, example, number, table, quote and warning. "Without losing content" means every item lands somewhere on the page. It may be compressed into a chain, a table cell or a node label, but it must be there.
2. **Audit the numbers before drawing them.** Recompute every table and worked example (use a quick script for anything non-trivial). A wrong number on a polished chart misleads more than a wrong number in prose, because the chart looks authoritative.
   - Fix errors and tag each one `⚑ Corrected`, stating what was wrong (`<aside class="ed fix">`).
   - Tag material you add `+ Added` (`<aside class="ed">`). This lets the user tell their notes from your additions.
   - Never change a source fact silently.
3. **Map content to components** using the table below. Then write one HTML body fragment per page section (see `references/components.md`).
4. **Write the spec script** for charts and schematics (see `references/engine-api.md`). Wrap each spec in its own `safe(function(){ … })` so one bad spec cannot blank the page.
5. **Build:**
   `python <skill>/scripts/build.py --title "Ch 2 · Systems Zoo" --out chapters/chapter-02-x.html --parts header.html hero.html body.html footer.html --script specs.js`
   Add `--fragment` only for an Artifact publish.
6. **Check:** `python <skill>/scripts/check.py <page.html>`. Fix until it prints OK.
7. **Look once.** Open the file in a browser (chrome-devtools `new_page` with a `file:///` URL). Run `scripts/browser-check.js` through `evaluate_script` and fix every non-empty array. At most one screenshot, of the densest diagram. Do not loop on screenshots; the measurements catch what matters.
8. **Deliver.** Give the file path(s), or publish. In the reply, list every correction and addition with confidence tags.

## Content → component map

| Content in the source | Component | Why |
|---|---|---|
| A concept defined against its opposite | `.split` with `.side bad/good` + `.vs` | The contrast is the meaning |
| A process, pipeline or causal sequence | `.rail` of `.node` + `.pipe` (add `.loop` + `.ret` if it feeds back) | Shows direction and stages |
| A short causal chain or vicious cycle | `.chain` (end with `↺` if it loops) | Compact, inline |
| Stocks, flows, feedback loops, architectures | `AE.dg` schematic | Geometry carries structure |
| A numeric table or worked example | `.tbl` **plus** an `AE.plot` chart drawn from the same numbers | The table gives precision, the chart gives shape |
| A behavior shape (growth, decay, oscillation) | `AE.spark` | Shape over numbers |
| A checklist or question set the reader will reuse | `.diag` diagnostic card | Reusable tool, visually distinct |
| A list of laws or principles | `.laws` grid | Scannable, numbered as in source |
| Low- vs high-leverage interventions | `.lev` | Wrong move vs right move side by side |
| Warnings, key insights, lessons | `.call` (`cau`, `imp`, `nte`, `wrn`, `tip`) | Typed by role |
| An author quote or definition | `.quote` | One per idea, not decoration |
| A formula | `.eq` with colored terms | Terms keep their semantic color |
| Layers or tiers | `.tiers` | Stacked, each with its own rail |
| Events vs hidden causes | `.berg` (waterline) | Above vs below the surface |
| Magnitudes spanning orders | `.hbars` (log widths) | Comparable at a glance |

## Writing rules for page text

- Follow ASD-STE100 style. Descriptive sentences ≤25 words, procedural steps ≤20. One idea per sentence. Active voice. Keep one term per concept for the whole page.
- No filler words ("delve", "tapestry", "crucial", "robust", "testament"), no em-dash asides, no stock phrases.
- Text annotates visuals. Keep a paragraph to 3 sentences at most; past that, convert it into a chain, rail or table.
- Explain the physical mechanism before code or syntax. Use exact production terms. Keep the source author's own analogies, such as a bathtub, but invent no childish ones.
- Use numbered markers only for real sequences.
- Use they/them for hypothetical people (the dealer, the manager).

## Visual rules

- **Color is semantic and comes only from tokens:**
  - stock = `--stock` (blue)
  - flow = `--flow` (cyan)
  - balancing / good = `--bal` (green)
  - reinforcing = `--rein` (orange)
  - delay = `--delay` (magenta)
  - risk = `--risk` (red)
  - editor note = `--note` (yellow)
  - control / info = `--info` (purple)
  - Never write a literal hex in page markup or specs. Dark mode works only because every color is a token.
- **Nothing click-gated.** No tabs, accordions, steppers or scrubbers. Ambient animation is fine if it renders a complete static frame under `prefers-reduced-motion` and pauses offscreen.
- **Charts are drawn to scale** through `AE.plot`. Every label names a value the chart actually reaches.
- **Mobile:** rails stack vertically on their own. Put wide SVG inside `.scroll` with `style="--minw:640px"` so it scrolls inside its box, never the page.

## Gotchas (each one broke a real page)

- **Atkinson Hyperlegible Mono is wide**, about 0.62em per character. Budget schematic boxes accordingly:
  - 13px bold title ≈ 8.1px per char
  - 11.5px line ≈ 7.2px per char
  - 11px label ≈ 6.9px per char
  - Add 12px of padding. A 124px box fits about 13 title characters.
- **Last x-axis tick:** set `m:{r:30}` or more when the last tick label is longer than 3 characters, or it clips.
- **Edge labels** sit on their line with a halo. Keep them 12px or more from node boxes; `browser-check.js` reports collisions as `labelOnBox`.
- **Class collisions:** do not reuse HTML utility classes inside SVG. `.lab` is uppercase and letter-spaced in HTML; base.css resets it inside `.dg` only.
- **Hidden defs:** the defs SVG must stay `width=0 height=0` with absolute positioning, never `display:none`, or the arrow markers vanish.
- **Full document vs fragment:** use full-document mode for repo files, or a page opened from disk renders in quirks mode. Use `--fragment` only for the Artifact tool.
- **CSP:** the Artifact CSP allows Google Fonts and a few CDNs. This design system needs no libraries; keep it that way.
