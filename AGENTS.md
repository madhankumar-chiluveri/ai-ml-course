# AI & ML Engineering Mastery Course: Project Rules

## Rule Precedence
- Global rules apply in full: `~/.agent-rules/AGENTS.md` (advisor protocol, ASD-STE100 writing, visual-first explanations, 3-tier token workflow). Claude Code imports that file. Antigravity and Codex load synced copies.
- This file adds project rules only. It never restates or overrides a global rule. On any conflict, the global rule wins.
- `CLAUDE.md`, `GEMINI.md` and `CODEX.md` only point to this file. Keep every project rule here.

## Project Overview
A self-paced curriculum that takes a learner from zero to a hireable AI/ML and agentic-systems engineer. It holds 114 study topics in 8 phases, plus capstone briefs. Each topic is a companion pair: a study note (`NN_topic.md`) and a runnable proof script (`NN_topic.py`). Scripts need no setup, no API keys and no spend.

## Commands
```bash
python -m venv .venv               # Create a Python virtual environment
.venv\Scripts\activate             # Activate it (Windows)
pip install numpy pandas matplotlib pytest pydantic requests fastapi uvicorn httpx scikit-learn torch tiktoken
python course-path/phase-0-engineering-foundations/01_python_basics.py  # Run one topic script
pytest                             # Run the unit tests
```

## Repository Map
| Path | Purpose |
|---|---|
| `course-path/` | 8 curriculum phases (`phase-0-engineering-foundations/` to `phase-8-capstone-projects/`) |
| `course-path/README.md` | Phase tracker, topic table and execution guide |
| `course-utils/complete-ai-engineer-roadmap.md` | Master 114-topic curriculum and its dependencies |
| `course-utils/per-topic-deepdive-generator.md` | Canonical study-note spec: section order, glossary format, diagram palette |
| `explanations/` | Standalone architecture deep-dives (`.md` with Mermaid) and HTML explainers |
| `practice/` | Active-recall, closed-book coding exercises |
| `social-posts/` | LinkedIn and Instagram content. Its rules live in `social-posts/AGENTS.md` |
| `.agents/skills/` | Workspace skills: `concept-explainer`, `claude-artifact-creator` and others |

## Topic Modalities
- **CODE** (Python logic): `NN_topic.md` + `NN_topic.py`. The script is self-contained, makes its own mock data and shows the core client or algorithm. No mock-server test harnesses.
- **WORKBENCH** (CLI, DevOps, cloud): `NN_topic.md` only. Section 6 holds copy-paste terminal drills (Git Bash, WSL, Docker, NGINX, OCI). No synthetic Python wrappers.
- **CONCEPT**: `NN_topic.md` only, with one worked example by hand.

## Study-Note Format
- Follow `course-utils/per-topic-deepdive-generator.md` exactly.
- Sections: 1 Overview → 2 Glossary → 3 Skip Test — Answered → 4 Visual Concept Diagrams → 5 Core Technical Deep Dive → 6 Hands-On → 7 Video → 8 Retrieval Checkpoint — Unanswered → 9 Closed-Book Rebuild → Review again in.
- Glossary entry: Definition → 💡 Analogy (production-grade, never childish) → 💻 Code Example & ⚠️ Why It Matters → Verified Output → 🤖 AI/ML Use Case → 🎨 Visual Concept.

## Diagrams and Artifacts
- Mermaid appears only in persistent `.md` files: study notes and `explanations/`. Use the shared Flexoki `classDef` palette from the note spec. No per-node `style` lines.
- Chat uses ASCII box/pipe diagrams. HTML pages use the `claude-artifact-creator` skill (`~/.claude/skills/claude-artifact-creator`; `.agents/skills/` holds a synced copy). HTML pages never contain Mermaid.
- Save an HTML explainer next to its source `.md`, with the same basename.

## Task Intake
Classify each task as `TOPIC_CREATION`, `SCRIPT_REBUILD`, `CONCEPT_EXPLAINER`, `PRACTICE` or `REFACTOR`.
- **QUICK** (under 30 lines or 1 script run): execute directly.
- **MEDIUM** (2 to 5 files, or one topic pair): outline the structure and script behavior inline first.
- **LARGE** (a full phase or several topics): write a plan and get explicit user confirmation.

## Pedagogy and Safety
- **Active recall**: never answer Retrieval Checkpoint questions inside the note.
- **Real output only**: every quoted output and drill result comes from a real run. Never fabricate or estimate.
- **Offline and safe**: scripts leave no background processes. They write only beside themselves or to temporary directories.

## Token-Tier Status
- `.code-review-graph/` exists. `graphify-out/` and `llmwiki/` do not exist. Verify before use, then apply the global 3-tier workflow to the tiers that exist.

## AGENTS.md Maintenance
1. No day-by-day logs. Git history tracks changes.
2. Summary over detail: 3 bullets or fewer per section.
3. Update bullets in place. Do not append new ones.
4. Keep this file under 150 lines, so a new agent can read it fast.
