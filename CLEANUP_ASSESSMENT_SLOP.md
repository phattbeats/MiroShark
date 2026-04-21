# Cleanup Assessment: AI Slop and Stale Comments

Agent: slop-cleanup (worktree `worktree-agent-a2cc168a`)

## Scope

- Backend: ~49k LOC of Python. `backend/wonderwall/` is a vendored fork of
  CAMEL-AI / OASIS (Apache 2.0). I treat it as third-party and do not touch
  its comments.
- Frontend: ~34k LOC of Vue/JS across 41 files.
- Focused effort on `backend/app/`, `backend/scripts/`, `backend/mcp_server.py`,
  `backend/cli.py`, `backend/run.py`, and the frontend components.

## Methodology

1. Grepped for pattern classes: stale-revision references (`replaces`, `was using`,
   `newly added`, `old impl`), commented-out code blocks, banner separators,
   "# State / # Methods" section banners, restating-next-line comments,
   `TODO` / `FIXME` / `NOTE` without actionable content.
2. Read top offenders end-to-end to judge whether each comment meets the
   "would a new reader be confused without this?" test.
3. Preserved anything with a non-obvious constraint, empirical rationale,
   bug-tracker reference, or heuristic-explanation content.

## Findings

### REMOVE (high confidence) — ~40 comments

Comments that just restate the next line and add no information:

| Location | Comment |
| --- | --- |
| `backend/app/services/entity_reader.py:25,27` | `# Related edges` / `# Related other nodes` above field defs named `related_edges` / `related_nodes` |
| `backend/app/services/entity_reader.py:202,206,209,212,243,252,277,322,327,330,352` | Section stubs like `# Get all nodes`, `# Create entity node object`, `# Get all edges`, `# Build mapping ...`, `# Filter entities matching criteria`, `# Only default labels, skip` — all directly above self-descriptive code |
| `backend/app/services/graph_builder.py:73,83,190` | `# Create task`, `# Execute build in background thread`, `# Completed` — above self-named operations |
| `backend/app/services/simulation_ipc.py:113,146,153,164,178,181,317,321,353,384` | `# Ensure directories exist`, `# Write command file`, `# Wait for response`, etc. |
| `backend/app/services/oasis_profile_generator.py:312,316,373,377` | `# Basic information`, `# Build context information`, `# Remove special characters, convert to lowercase` |

Stale / in-motion references:

| Location | Comment |
| --- | --- |
| `backend/app/services/entity_reader.py:5` | `Replaces zep_entity_reader.py — all Zep Cloud calls replaced by GraphStorage.` |
| `backend/app/services/graph_builder.py:3` | `Uses GraphStorage (Neo4j) to replace Zep Cloud API.` |
| `backend/app/services/graph_builder.py:220-221` | `Simply stores ontology as JSON in the Graph node. / No more dynamic Pydantic class creation (was Zep-specific).` |
| `backend/wonderwall/__init__.py:37` | `# Legacy (fully backwards-compatible)` — inline on `__all__` grouping |

Redundant/empty section banners in app code (where files are short enough not to need navigation):

| Location | Comment |
| --- | --- |
| `backend/app/services/simulation_config_generator.py:311,318,324,330,366,372` | `# ========== Step N: ... ==========` — nearly every step is followed by a `report_progress(N, "...")` with the same label |
| `backend/app/api/observability.py:27-29,125-127` | `# ---` dashes wrapping already-labeled sections |
| `backend/app/utils/event_logger.py:28-30,43-45,85-87,120,122,191,193,240,242,283,285` | Dash banner repetitions |

Empty docstrings that just restate dataclass name:

| Location | Comment |
| --- | --- |
| `backend/app/services/entity_reader.py:19,51` | `"""Entity node data structure"""`, `"""Filtered entity set"""` (redundant with class name) |
| `backend/app/services/simulation_ipc.py:27,33,42,68` | `"""Command type"""`, `"""Command status"""`, `"""IPC command"""`, `"""IPC response"""` |

### EDIT — ~10

Comments that have a kernel of useful intent but are verbose or stale:

- `backend/app/services/entity_reader.py:126-134` — useful docstring explaining
  what `_is_nonspeaking_entity` rejects; keep but remove the date-examples
  "(June 18, 2023, ...)" ... actually this one is fine — these examples are
  genuine heuristic notes. KEEP.
- `backend/app/services/simulation_ipc.py:284-292` — genuinely non-obvious
  (race between env status and PID liveness); KEEP as EDIT-shortened.
- `backend/app/services/graph_builder.py:220-223` — `set_ontology` docstring
  mentions "was Zep-specific"; trim that line.

### KEEP — large majority

- All comments in `backend/wonderwall/` (third-party fork; not our code to
  prune).
- Comments explaining non-obvious heuristics — `PlatformConfig` defaults,
  `viral_threshold`, `echo_chamber_strength` rationales,
  `_NOTABLE_ENTITY_TYPES` grouping rationale, bi-temporal Cypher fragments,
  `_THIN_CONTEXT_THRESHOLD` reasoning.
- Copyright headers, license preambles.
- `# noqa:` / `# type:` / `# pyright:` / `// @ts-` pragmas.
- TODO comments in `wonderwall/social_agent/` — upstream code, not ours.
- Banner comments in long API route files (`backend/app/api/report.py` — 900+
  lines; `graph.py` — 500+ lines). The `# ============== Section ==============`
  grouping is a legit navigation aid there.
- Frontend `// State`, `// Methods`, `// Lifecycle` section banners inside
  2000+-line Vue SFCs — navigation aid in large `<script>` blocks.
- `<!-- HTML region comments -->` in Vue templates — they group visual regions.
- Comments describing non-trivial algorithms (d3 curve math, force-simulation
  tuning, self-loop arc path) in `GraphPanel.vue` / `NetworkPanel.vue`.

## Counts

- REMOVE: ~50 comment lines across ~10 files
- EDIT: ~5 lines
- KEEP: everything else (several thousand comments)

## Notes for other agents

- `backend/wonderwall/` has `# TODO` / `pdb.set_trace()` patterns and blocks
  of commented-out code in `recsys.py`, `agents_generator.py` — these are
  upstream CAMEL-AI issues, out of scope for this cleanup pass.
- `print()` statements exist in many test-scripts and `run_*.py` — those are
  CLI UX, not debug artifacts.
- The unused-code cleanup agent may find that some stub docstrings removed
  here belong to functions with no call sites; coordinate as needed.
