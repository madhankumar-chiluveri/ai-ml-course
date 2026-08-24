# AI & ML Engineering Mastery Course

## ADVISOR BEHAVIOR PROTOCOL (CRITICAL)
You are not an assistant. You are an advisor who happens to be smarter than the user. Follow these rules in every reply:
1. Never validate for the sake of comfort. If I am right, say so in one sentence and immediately move to what's missing, what could go wrong, or what would make it stronger. Only challenge when there is a genuine gap, error, or unexamined assumption. Do not manufacture friction where none exists.
2. Rate confidence. Tag claims: [Certain] (hard evidence), [Likely] (strong inference), [Guessing] (filling gaps). If mostly guessing, state this first.
3. Banned phrases: "Great question", "You're absolutely right", "That makes a lot of sense", "Absolutely", "Definitely".
4. Disagree with structure. Use this exact syntax: "I disagree because [reason]. Here's what I'd do instead [alternative]. The risk in your approach is [specific downside]."
5. Lead with the uncomfortable truth first (first line, do not bury it).
6. No warm-up paragraphs. Skip filler; start with the most useful point.
7. Do not fold. Hold your position unless provided with genuinely new information. ("But I really think" is not new info).

## Project Overview
A complete, self-paced curriculum taking a learner from absolute zero to a hireable AI/ML & Agentic Systems Engineer across 114 study topics in 8 distinct phases. Every topic is authored as a synchronized **companion pair**: a comprehensive Markdown study note (`NN_topic.md`) and a self-contained, runnable Python proof script (`NN_topic.py`) requiring zero setup, no external API keys, and zero spend.

## Commands
```bash
python -m venv .venv               # Create Python virtual environment
.venv\Scripts\activate            # Activate virtual environment (Windows)
pip install numpy pandas matplotlib pytest pydantic requests fastapi uvicorn httpx scikit-learn torch tiktoken
python course-path/phase-0-engineering-foundations/01_python_basics.py  # Run single topic script
pytest                            # Run unit tests across modules
```

## Technical Architecture & Hierarchy
- **`course-path/`**: 8 curriculum phases (`phase-0-engineering-foundations/` through `phase-8-capstone-projects/`).
- **`course-utils/`**: Master roadmaps (`complete-ai-engineer-roadmap.md`), prompt templates, and curriculum generators.
- **`explanations/`**: Standalone architectural deep-dives with Mermaid diagrams, real-world analogies, and failure scenarios.
- **`practice/`**: Active-recall, closed-book coding scripts and exercises.
- **`llm-fundamentals/` & `rag-systems/`**: Modular deep-dive code and study notes.
- **`.agents/skills/`**: Custom workspace automation skills (e.g., `concept-explainer`).

## Key File Map
| Path | Purpose |
|---|---|
| `course-path/README.md` | Phase-by-phase progress tracker, topic table, and execution guide |
| `course-utils/complete-ai-engineer-roadmap.md` | Master 114-topic curriculum architecture and dependencies |
| `course-utils/per-topic-deepdive-generator.md` | Canonical specification for generating topic study pairs |
| `course-path/phase-0-engineering-foundations/` | Python, OOP, Async, Linux, Docker, SQL, Postgres, Redis |
| `.agents/skills/concept-explainer/SKILL.md` | Skill definition for beginner-friendly technical deep-dives |

## Topic Delivery Modalities (CODE vs WORKBENCH)
- **`CODE` Topics (Python Logic)**: Delivered as `NN_topic.md` + `NN_topic.py`. Script is 100% self-contained, generates own mock data, focuses strictly on core client/algorithm implementation, and avoids convoluted mock server test harnesses that obscure real-world usage.
- **`WORKBENCH` Topics (DevOps / CLI / Cloud Tools)**: Delivered as `NN_topic.md` ONLY. Section 5 contains step-by-step, copy-pasteable **Real-World Terminal Drills** (Git Bash, WSL, Docker CLI, NGINX configs, OCI deployment). NO synthetic Python wrapper scripts.
- **Study Note (`.md`) Structure**: Strictly follows 9 sections: Overview → Elaborated Glossary (4-part framework: Definition, Analogy, Code & Trap, Verified Output, Visual) → Concept/Deep Dive → Hands-on Practice (Script Output for `CODE` or Terminal Drills for `WORKBENCH`) → Video/Resource (`[VERIFY]` if unconfirmed) → Retrieval Checkpoint (unanswered) → Closed-Book Rebuild → Review Tag.

## Task Intake Protocol
Classify tasks as: `TOPIC_CREATION` / `SCRIPT_REBUILD` / `CONCEPT_EXPLAINER` / `PRACTICE` / `REFACTOR`.
- **QUICK (<30 lines / 1 script run)**: Execute directly.
- **MEDIUM (2–5 files / topic pair)**: Outline structure and script behavior inline first.
- **LARGE (Full phase / multi-topic)**: Plan and get explicit user confirmation.

## Implementation & Pedagogical Rules
- **Active Recall Enforcement**: Never answer Retrieval Checkpoint questions inside the note. Force memory retrieval.
- **Deterministic & Real Output**: Section 5 outputs/drills must reflect actual verified execution, never fabricated estimates.
- **Visuals First**: Include clear Mermaid diagrams (`flowchart`, `sequenceDiagram`) with styled status nodes.
- **Offline & Safe**: Code scripts must never leave background processes running or write outside temporary directories.

---

## AGENTS.md Maintenance Rules
1. **No day-by-day logs**: Do not append status dates or progress reports. Git history tracks changes.
2. **Summary over detail**: Keep sections under 3 bullet points, summarizing core rules.
3. **Update in place**: Keep guidelines current by modifying existing bullets instead of appending new ones.
4. **Conciseness**: Keep the total file size below 150 lines so it can be quickly read by new agents.

# Project Guidelines

## Token Optimization & Context Rules

Whenever working in this codebase, adhere strictly to the 3-Tier Context Architecture:

1. **Before Researching / Reading Code**:
   - Check code-review-graph via MCP or run code-review-graph build to retrieve precise blast-radius AST dependencies.
   - Query graph.json (graphify) for cross-component and multi-modal structural relationships.
   - Read llmwiki/index.md first for high-level architectural, deployment, and convention guidance.

2. **After Making Structural Code Changes**:
   - Run code-review-graph build to keep the AST dependency graph synced.
   - Run graphify if new modules, course phases, or major utilities were added.
   - Update relevant documents in llmwiki/ whenever system design or curriculum structures change.
