# Cleanup Assessment: Weak Types

Scope: `backend/app/`, `backend/scripts/`, `backend/wonderwall/`, plus a JSDoc pass of `frontend/src/`.

Totals surveyed (raw grep for `Any`, `Dict[str, Any]`, bare `Optional[Any]`, `object`):
- `backend/app/`: ~208 occurrences across 26 files
- `backend/scripts/`: ~61 occurrences across 9 files
- `backend/wonderwall/`: ~62 occurrences across 12 files
- `frontend/src/`: no `{*}` or `{any}` JSDoc tags; all occurrences of `{Object}` have an inline shape comment and are informational rather than load-bearing

The dominant pattern in this repo is **`Dict[str, Any]` used to describe a Neo4j row / JSON blob / Pydantic-free LLM output**. In the vast majority of cases this is legitimate — the data is genuinely dynamic, comes back with driver-level typing (`neo4j.Record` materialized to dict), or is validated field-by-field downstream rather than via a Pydantic model. Replacing these en masse with `TypedDict` would add hundreds of lines for little safety gain unless we first refactored the read path to use Pydantic or Neo4j record-class projection — out of scope here.

I therefore classify each file below into one of:

- **Keep** — `Any`/`Dict[str, Any]` is correct for this site (genuinely dynamic JSON, Neo4j row, `kwargs` forward). These are noted as "intentionally Any".
- **Strengthen now** — high-confidence replacement visible from evidence in the file itself. Implemented in the companion commit.
- **Flag** — would be a good improvement but requires cross-file refactor and/or new TypedDict definitions. Recommended as a follow-up.

---

## Strengthened (high confidence, implemented)

### `backend/app/services/simulation_runner.py`
- L236–237: `_stdout_files: Dict[str, Any]` / `_stderr_files: Dict[str, Any]` described as "Store stdout file handles". The assignment at L485 uses `open(main_log_path, log_mode, encoding='utf-8')` (text mode) and L511 sets the stderr dict values to `None`. Confidence: **high**. Replaced with `Dict[str, Optional[TextIO]]`.

### `backend/app/utils/retry.py`
- L9 imports `Any` but it is only used in `def wrapper(*args, **kwargs) -> Any` (decorated wrappers — cannot be strengthened without `ParamSpec` + `TypeVar` machinery that the rest of the codebase does not use). Leaving those alone but dropping the unused-looking `Any` from the top-level `call_with_retry` would regress behaviour. **Kept.**

### `frontend/src/`
- No `{*}` / `{any}` / `{*}` JSDoc annotations found. All `@param {Object} data` tags already document the shape inline. **Nothing to strengthen.**

---

## Flagged for human review

### `backend/app/models/project.py`
- L40 `ontology: Optional[Dict[str, Any]]`: The ontology has a well-defined structure (see `services/ontology_generator.py`: `entity_types`, `edge_types`, `analysis_summary`, each with further inner keys). Would be worth a `TypedDict` in `models/ontology.py`:
  ```python
  class EntityTypeAttribute(TypedDict):
      name: str
      type: str
      description: str
  class EntityTypeDef(TypedDict):
      name: str
      description: str
      attributes: list[EntityTypeAttribute]
      examples: list[str]
  class Ontology(TypedDict):
      entity_types: list[EntityTypeDef]
      edge_types: list[EdgeTypeDef]
      analysis_summary: str
  ```
  Confidence: **medium-high**. Deferred because ontology is round-tripped through JSON and downstream code often tolerates missing keys (`.get(...)` everywhere), so a strict TypedDict may cause friction without a broader migration.

- L76 `from_dict(cls, data: Dict[str, Any])`: this is a classic deserialization entrypoint and `Dict[str, Any]` is the *right* type here — the data is raw JSON. **Keep.**

### `backend/app/models/task.py`
- L32 `result: Optional[Dict]` and L34 `metadata: Dict`, L35 `progress_detail: Dict`: Parameterless `Dict`. Concrete schemas depend on task_type, so `Dict[str, Any]` would be the correct annotation (parameterless `Dict` is equivalent but should be spelled explicitly). Confidence **high** for the lint-level rewrite; **low** for a TypedDict because there's no single shape.

### `backend/app/storage/neo4j_storage.py`
- Return types like `List[Dict[str, Any]]` for `get_all_nodes`, `get_all_edges`, `get_graph_data` etc. match the dict conversion in `_node_to_dict`/`_edge_to_dict`. A `NodeDict`/`EdgeDict` TypedDict would be a strict improvement (they have stable keys: `uuid`, `name`, `labels`, `summary`, `attributes`, `created_at` for nodes; plus temporal & lineage fields for edges). Confidence **medium** — the serialized dicts flow to Flask `jsonify` and to the frontend where the same shape is implicitly relied on. A proper TypedDict pair would make that contract explicit.
- `set_ontology(ontology: Dict[str, Any])` — same ontology shape as above.
- `_call_with_retry(self, func, *args, **kwargs)` — `Callable[..., T]` with `TypeVar` would be better but this runs 100+ times per ingest; changing the signature would ripple through. **Flag.**

### `backend/app/storage/graph_storage.py`
- Abstract base exposes the same `Dict[str, Any]` contracts as Neo4jStorage — they should evolve together.

### `backend/app/storage/ner_extractor.py`
- `extract(text, ontology: Dict[str, Any]) -> Dict[str, Any]`: the return dict has shape `{"entities": list[EntityRow], "relations": list[RelationRow]}` — a `NerExtraction` TypedDict would help downstream `neo4j_storage.add_text` which immediately does `.get("entities", [])`. Confidence **high** for the shape; **deferred** because `add_text` also defensively accepts missing keys.

### `backend/app/services/ontology_generator.py`
- Multiple `Dict[str, Any]` for ontology dicts — same story, should be `Ontology` TypedDict.

### `backend/app/services/graph_tools.py`
- L31, 32, 64, 150, 332, 1408, 1472, 1532, 1578, 1648 etc. use `Dict[str, Any]` for search results, entity rows, agent profiles, etc. These are built-from-Neo4j rows or parsed JSON. Recommend one `AgentProfile` TypedDict and one `EntityRow` TypedDict. Confidence **medium**.

### `backend/app/services/report_agent.py`
- `details: Dict[str, Any]` in `ReportLogger.log` is correct — the logger's contract is truly free-form structured data. **Keep.**
- 17 other `Dict[str, Any]` uses mostly carry section/step records through ReACT loops. `ReasoningStep`/`Section` dataclasses already exist in `storage/reasoning_trace.py`; the in-memory ones in report_agent.py could share them. **Flag** as a dedup opportunity rather than a type fix.

### `backend/app/services/simulation_ipc.py`
- `IPCCommand.args: Dict[str, Any]` and `IPCResponse.result: Optional[Dict[str, Any]]` — the arg schema depends on the `command_type` enum. Could be a discriminated union (`InterviewArgs | BatchInterviewArgs | CloseEnvArgs`) but that's a sizeable refactor of the command dispatcher. **Flag.**

### `backend/app/utils/llm_client.py`
- `messages: List[Dict[str, str]]` is already as strong as the OpenAI SDK contract (role+content strings). The `response_format: Optional[Dict]` could be the stricter `Optional[ResponseFormat]` from `openai.types.chat` but that couples us to the SDK's internal types. `extra_body: Dict[str, Any]` is OpenRouter passthrough and is genuinely free-form. **Keep.**
- `chat_json(...) -> Dict[str, Any]`: the return is raw user JSON. This is *correct* `Any`; add a `# Intentionally Any` comment if we want to mark it. **Keep.**

### `backend/app/utils/event_logger.py`
- `data: Dict[str, Any]` on `emit` — free-form structured payload by design. **Keep.**

### `backend/app/utils/run_summary.py`
- `by_model: Dict[str, Dict[str, Any]] = defaultdict(lambda: {...})` — this is an aggregator with well-known fields (`calls`, `tokens_in`, `tokens_out`, `cost`, `latency_ms`, `errors`). A `ModelAggregate = TypedDict(...)` would be cleaner. Confidence **high**; deferred because the defaultdict factory makes the TypedDict enforcement awkward without an explicit initializer.

### `backend/scripts/round_memory.py`, `belief_integration.py`, `cross_platform_digest.py`, `market_media_bridge.py`, `run_parallel_simulation.py`
- `Dict[str, Any]` for agent configs, round results, profile dicts. These all live at the JSON file boundary (agents.json, config.json, trajectory.json) and replacing them would require a parallel set of TypedDicts in the scripts package. **Flag** — recommend aligning with the `wonderwall` module's own types first.

### `backend/wonderwall/**`
- `recsys.py` (21), `social_agent/agent_graph.py` (10), `social_agent/round_analyzer.py` (8), others: these are part of a re-used OASIS/Wonderwall social-agent simulation engine. Strengthening types here would require understanding the external contract and should be done as a dedicated pass (possibly upstream). **Flag; do not touch in this pass.**

### `backend/app/services/simulation_runner.py` (remaining Dict[str, Any] sites)
- L1181–1906: large aggregation / query methods that read events.jsonl and return assembled stat dicts. Candidates for `RoundStats` / `AgentStats` / `CleanupResult` TypedDicts. Confidence **medium**; deferred as these shapes are consumed by the Flask API layer and frontend — needs coordinated typing on both sides.

### `backend/app/services/push_notification_service.py`, `ner_extractor.py`, `entity_resolver.py`, `graph_memory_updater.py`, `oasis_profile_generator.py`, `simulation_config_generator.py`, `oracle_seed.py`, `entity_reader.py`, `report_agent.py`, `graph_builder.py`
- All follow the same pattern: results from LLM JSON calls. Strengthening them requires matching Pydantic/TypedDict to the prompt contracts, which would also improve JSON-schema prompting. **Flag** as a promising follow-up.

---

## Intentionally `Any` (do not change)

- `backend/app/utils/llm_client.py`: `chat_json` return, `response_format`, `extra_body`, `messages` (OpenAI SDK contract). These are the boundary with external APIs.
- `backend/app/utils/event_logger.py`: `data` payload on events (structured logging is free-form by design).
- `backend/app/utils/retry.py`: decorator `-> Any` on wrapper (cannot preserve callee's return type without `ParamSpec`/`TypeVar` refactor that the codebase does not use).
- All `from_dict(cls, data: Dict[str, Any])` class methods — deserialization entry points must accept raw JSON.
- `backend/app/utils/logger.py`: `*args, **kwargs` forwarded to `logging.Logger.*` — stdlib contract.
- `backend/app/storage/neo4j_storage.py` `_call_with_retry(self, func, *args, **kwargs)` — wraps arbitrary callables.

---

## Summary

- 1 file strengthened in-commit (simulation_runner file handle dicts).
- Most `Dict[str, Any]` uses are legitimate or require broader refactors to replace meaningfully (ontology/agent-profile/Neo4j-row TypedDicts).
- Frontend JSDoc is clean.
- Recommend a follow-up cleanup pass focused on (in priority order): (1) Ontology TypedDict in `models/`, (2) Neo4j `NodeDict`/`EdgeDict` for the storage layer, (3) LLM response Pydantic models per prompt template.
