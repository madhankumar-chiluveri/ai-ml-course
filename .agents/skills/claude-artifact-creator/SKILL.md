---
name: claude-artifact-creator
description: Generates high-end, research-backed interactive visual explainer artifacts in single self-contained HTML files with animated SVG state machines, interactive step-by-step scrubbers, live telemetry inspectors, and diagnostic sandboxes. Supports the Flexoki + Atkinson Hyperlegible reading engine (maximum cognitive legibility) and the Anthropic Warm Editorial aesthetic. Trigger whenever the user asks to build an artifact, visual explainer, concept visualizer, educational HTML tool, or interactive artifact.
---

# Visual Explainer & Cognitive Artifact Skill

Use this skill whenever asked to build an artifact, visual explainer, concept simulator, educational HTML tool, or interactive visual explainer.

---

## 1. Aesthetic & Readability Standard: Flexoki + Atkinson Hyperlegible

[Certain] Research from the Braille Institute of America and colorimetry studies (Steph Ango) demonstrates that pure black-on-white causes optical halation, while standard serifs suffer from letterform ambiguity (confusing `l`, `1`, `I`, or `O`, `0`). 

By default, every artifact uses the **Flexoki Inky Paper + Atkinson Hyperlegible** reading engine (with fallback to Anthropic Warm Editorial).

### Mandatory `:root` Design Tokens (Flexoki Engine)

```css
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700&display=swap');

:root {
  /* Flexoki Light Theme Tokens (Analog Pulp & Ink Standard) */
  --canvas: #FFFCF0;               /* Flexoki Paper (Warmest analog pulp background) */
  --surface: #FFFFFF;              /* Pure white elevated container */
  --surface-subtle: #F2F0E5;       /* Flexoki Base-50 (Card wash / toolbar) */
  --surface-muted: #E6E4D9;        /* Flexoki Base-100 (Subtle dividers & pill tags) */
  --border: #DAD8CE;               /* Flexoki UI-2 (Warm hairline border) */
  --border-dark: #CECDC3;          /* Flexoki UI-3 (Structural border) */

  /* Text Ink (18:1 contrast, zero optical halation) */
  --ink: #100F0F;                  /* Flexoki Black (Carbon ink, primary headers) */
  --ink-secondary: #575653;        /* Flexoki Tx-2 (Readable body charcoal) */
  --ink-tertiary: #878580;         /* Flexoki Tx-3 (Muted metadata & tags) */

  /* Flexoki Mineral Accents */
  --accent-primary: #BC5215;       /* Flexoki Rust Orange (Key CTA / active step) */
  --accent-primary-light: #FBEFE8;
  --accent-primary-border: #F3D2BF;

  --accent-transport: #205EA6;     /* Flexoki Deep Blue */
  --accent-transport-light: #EDF3FA;
  --accent-transport-border: #BBD2EA;

  --accent-auth: #AD8301;          /* Flexoki Warm Ochre / Amber */
  --accent-auth-light: #FAF5E6;
  --accent-auth-border: #E8D397;

  --accent-conn: #66800B;          /* Flexoki Forest Sage */
  --accent-conn-light: #F3F6E8;
  --accent-conn-border: #CFDC9C;

  --accent-danger: #AF3029;        /* Flexoki Crimson (Failure state) */
  --accent-danger-light: #FAECEB;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --shadow-sm: 0 1px 3px rgba(16, 15, 15, 0.04);
  --shadow-md: 0 4px 16px rgba(16, 15, 15, 0.06);

  /* Typography Stack: Atkinson Hyperlegible with bulletproof system fallback */
  --font-body: 'Atkinson Hyperlegible', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, "JetBrains Mono", Menlo, Monaco, Consolas, monospace;
}
```

### Alternative Preset: Anthropic Warm Editorial (On Request)
If the user explicitly requests Claude's native editorial brand palette:
- Canvas: `#FAF9F5` (Warm Ivory)
- Ink: `#141413` (Slate Ink)
- Accent: `#D97757` (Terracotta)
- Display font: `Georgia` / literary serif.

---

## 2. The 4-Part Pedagogical Architecture

Every visual explainer must contain these four sequential modules:

### Module 1: The Mental Model Invariant (Hero Card)
- 1 crisp sentence explaining the core constraint or physical mechanism.
- Styled as a callout card with `--accent-primary-light` background and border.
- Banned: Childish analogies. Use production mechanics.

### Module 2: The Interactive Simulation Stage
- Interactive SVG canvas with explicit `viewBox` (e.g. `viewBox="0 0 880 260"`).
- Top toolbar with:
  - `[← Previous]` button
  - Dynamic `Step X of N` indicator
  - `[Next →]` primary button
  - `[Auto-Play / Pause]` toggle button
- SVG nodes that illuminate as data advances along connection paths.
- Clickable nodes so the user can jump directly to any state.

### Module 3: Dynamic Telemetry Inspector
- Placed directly beneath the SVG canvas.
- Renders 3 to 4 live key-value metrics (e.g. `Active Layer`, `Encryption Cipher`, `Security State`) that dynamically update whenever the user changes steps.
- Accompanying 2-sentence breakdown of what is happening under the hood in that specific step.

### Module 4: The Diagnostic Sandbox ("Break It" Scenarios)
- 3 clickable scenario buttons exposing real-world failure modes.
- Clicking a scenario demonstrates which layer aborts, what exact error is emitted, and why.

---

## 3. Technical Constraints (Zero Failures)

1. **Strict Single-File Self-Containment**:
   - Write 100% of HTML, CSS (`<style>`), and JavaScript (`<script>`) in one single file.
   - Include Google Fonts `@import` for typography, but ensure font fallbacks to system fonts (`-apple-system`, `Segoe UI`, `ui-monospace`) are bulletproof when running completely offline.
2. **Diagram-First: Text Annotates Nodes**:
   - Ban long walls of prose. Text exists solely to annotate the visual nodes and state transitions.
3. **Dual File Delivery**:
   - Save the primary artifact in `<appDataDir>\brain\<conversation-id>\<artifact_name>.html` with `ArtifactMetadata`.
   - Also save a persistent copy in the workspace under `explanations/<topic-slug>.html`.
   - Provide clickable file links in chat.
