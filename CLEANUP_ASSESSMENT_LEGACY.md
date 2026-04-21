# Legacy / Deprecated / Fallback Code Assessment

Date: 2026-04-21
Scope: backend/app, backend/scripts, backend/wonderwall, frontend/src

## Summary

The codebase is in good shape on this axis. Most "fallback" / "legacy" flags in the code are legitimate graceful-degradation paths (encoding fallbacks, subprocess-not-running fallbacks, DB schema backfills, old log file format). A small number of truly dead deprecated items exist and are removed in this pass.

Confidence scale: HIGH = zero call sites and unambiguous doc-string tag; MEDIUM = few call sites updatable; LOW = reachable from active code paths / APIs.

---

## HIGH CONFIDENCE REMOVALS (executed)

### 1. `OasisAgentProfileGenerator.save_profiles_to_json` — deprecated wrapper
- Location: `backend/app/services/oasis_profile_generator.py:1375-1384`
- Status: explicit `[Deprecated]` docstring, emits `logger.warning` on call, forwards to `save_profiles()`.
- Call sites: 0 (only its own definition).
- Replacement: `save_profiles()`.
- Confidence: HIGH — remove.

### 2. `OntologyGenerator.generate_python_code` — documented unused
- Location: `backend/app/services/ontology_generator.py:276-377`
- Status: docstring says `[DEPRECATED]` and `Not used in MiroShark (ontology stored as JSON in Neo4j). Kept for reference only.`
- Call sites: 0.
- Replacement: none needed; ontology is stored as JSON.
- Confidence: HIGH — remove.

### 3. `ActionLogger` class + `_global_logger` + `get_logger` (module-level) in `action_logger.py`
- Location: `backend/scripts/action_logger.py:244-350`
- Status: comment header says `# ============ Legacy interface compatibility ============`, class docstring says `(legacy interface compatibility) Use SimulationLogManager instead`.
- Call sites for `ActionLogger`: 0. (Only the `PlatformActionLogger` and `SimulationLogManager` classes in the same file are referenced elsewhere.)
- Call sites for legacy `get_logger(log_path=)` in action_logger: 0. (The `get_logger` everywhere else in the codebase is the one from `app.utils.logger` — a distinct function.)
- Replacement: `SimulationLogManager` / `PlatformActionLogger` already used everywhere.
- Confidence: HIGH — remove class and module-level legacy globals.

### 4. Dead CSS rule `.action-controls` in `Step3Simulation.vue`
- Location: `frontend/src/components/Step3Simulation.vue:1968-1973`
- Status: explicitly commented `/* kept for backwards compat */`.
- HTML/template references to class `action-controls`: 0.
- Confidence: HIGH — remove CSS block.

---

## FLAGGED — KEPT

### A. `search_graph`, `get_graph_statistics`, `get_entity_summary`, `get_simulation_context`, `get_entities_by_type` legacy-redirects in `report_agent._execute_tool`
- Location: `backend/app/services/report_agent.py:1345-1377`
- Comment says "Backward compatible legacy tools". However these tool names are publicly exposed via `backend/mcp_server.py` and `backend/app/api/report.py`. The LLM, MCP clients, or frontend (`Step4Report.vue`) can still emit these names. Removing them would break MCP and the Flask API.
- Confidence: LOW for removal — KEEP.

### B. Legacy single-file `actions.jsonl` fallback in `simulation_runner.py`
- Location: `simulation_runner.py:1076-1085`, `simulation_runner.py:1157-1173`
- Reads an old single-file `actions.jsonl` when per-platform files don't exist. This protects replay of simulations recorded under the old format still sitting on users' disks.
- Confidence: LOW for removal — KEEP.

### C. `graph_tools._fallback_interview` / `oasis_profile_generator` fallback persona / `round_memory._fallback_summary`
- Purposeful graceful-degradation paths for when the primary path (API, LLM) errors. Not "dead code kept just in case from a past bug" — these are the designed error paths.
- Confidence: LOW for removal — KEEP.

### D. `wonderwall/environment/env.py` legacy paths (`DefaultPlatformType`, `Platform`)
- Lines 126-179 say "Legacy path" but the paths are actively used by `run_twitter_simulation.py`, `run_reddit_simulation.py`, and `run_parallel_simulation.py`.
- Confidence: LOW for removal — KEEP.

### E. `wonderwall/social_agent/agent.py` legacy social-media path
- Docstring says "Supports both the legacy social-media workflow and the new generic simulation framework." Both code paths (`SocialAction`/`SocialEnvironment` and `SimulationConfig`) are in active use.
- Confidence: LOW for removal — KEEP.

### F. Neo4j schema backfill statements (`BACKFILL_VALID_AT`, `BACKFILL_KIND`)
- DB migrations that normalize legacy edges. Rules of cleanup: preserve rollback-safe DB migrations.
- Confidence: LOW for removal — KEEP.

### G. Entity card CSS labelled "Legacy entity card styles for backwards compatibility" in `Step4Report.vue:4428+`
- Style injected HTML (dynamic insight-display markdown). Can't verify markup is never produced from report-generation pipeline. Leaving as-is.
- Confidence: LOW for removal — KEEP.

### H. `_read_text_with_fallback` (utils/file_parser.py)
- Multi-level encoding fallback: chardet → UTF-8 → UTF-8 + errors='replace'. Legit defensive.
- KEEP.

### I. `cleanup_old_tasks` (models/task.py)
- Not legacy — "old" means time-expired.
- KEEP.

### J. `action_logger.py:552-554` comment about "old simulation_end events"
- Position tracking on resume to avoid re-reading prior run's events. Functional.
- KEEP.

### K. `.env.example` feature flags
- All flags have documented purposes (`ORACLE_SEED_ENABLED`, `MCP_AGENT_TOOLS_ENABLED`, `RERANKER_ENABLED`, `LLM_PROMPT_CACHING_ENABLED`, `CONTRADICTION_DETECTION_ENABLED`, `ENTITY_RESOLUTION_ENABLED`, `REASONING_TRACE_ENABLED`, `GRAPH_SEARCH_ENABLED`). None appear to be always-on/always-off relics.
- KEEP.

### L. Frontend "fallback" comments (`SimulationRunView.vue:205`, `ReplayView.vue:229`, `Step3Simulation.vue:613`, `Step4Report.vue:902`)
- All are intentional UI fallbacks (generic renderer for unknown content types, backwards-compatible parsers for older report text formats on disk).
- KEEP.

---

## Changes applied

- Removed `OasisAgentProfileGenerator.save_profiles_to_json` (10 lines).
- Removed `OntologyGenerator.generate_python_code` (~102 lines).
- Removed legacy `ActionLogger` class + module-level `_global_logger` + `get_logger` from `backend/scripts/action_logger.py` (~108 lines).
- Removed dead `.action-controls` CSS block from `Step3Simulation.vue` (~6 lines).

Net: ~226 lines of dead code removed. No call-site updates required (all removed items had zero external references).
