# Coverage Gap Analysis: Legacy Graphene/Flask vs Strawberry/FastAPI POC Test Suites

**Date:** 2026-06-04  
**Scope:** `graphql_api/tests/` (legacy) vs `spike/strawberry_poc/tests/` (POC)

---

## 1. Summary Table

Legend: ✅ Full coverage  ⚠️ Partial coverage  ❌ Not yet ported  N/A (infrastructure/skip)

### Top-level legacy test files

| Legacy test file | Tests | POC test file | POC tests | Status |
|---|---|---|---|---|
| `test_general_task_schema.py` | 7 | `test_general_task.py` | 11 | ✅ |
| `test_automation_task_schema.py` | 6 | `test_smoketest_ab.py` (partial) | — | ⚠️ |
| `test_rupture_generation_schema.py` | 6 | `test_smoketest_ab.py` + `test_rupture_set.py` | — | ⚠️ |
| `test_inversion_solution_schema.py` | 4 | `test_inversion_solution.py` + `test_inversion_solution_interface.py` | 10+10 | ✅ |
| `test_table_schema.py` | 3 | `test_table.py` | 6 | ✅ |
| `test_table_schema_fix_252.py` | 3 | — | — | ❌ |
| `test_sms_schema.py` | 6 | `test_smoketest_ab.py` (partial) | — | ⚠️ |
| `test_sms_file_link_schema.py` | 2 | `test_sms_file.py` + `test_smoketest_ab.py` | 4+partial | ⚠️ |
| `test_task_task_relations_db.py` | 1 | `test_general_task.py` + `test_smoketest_ab.py` | — | ⚠️ |
| `test_file_relation_bugfix_126.py` | 5 | `test_file_relation.py` | 3 | ⚠️ |
| `test_file_relation_compression.py` | 3 | `test_file_relation_compression.py` | 6 | ✅ |
| `test_nodes_bugfix_220.py` | 3 | `test_inversion_solution.py` (partial) | — | ⚠️ |
| `test_general_task_bugfix_29.py` | 1 | `test_general_task.py` | — | ⚠️ |
| `test_general_task_bugfix_217.py` | 1 | — | — | ❌ |
| `test_schema.py` | 5 | `test_smoketest_ab.py` | 19 | ⚠️ |
| `test_search_manager.py` | 9 | `test_smoketest_ab.py` (`@pytest.mark.integration`) | 5 integration | ⚠️ |
| `test_dynamo_and_s3_queries.py` | 9 | `test_s3_fallback.py` (partial) | 7 of 16 | ⚠️ |
| `test_s3_fallback.py` | 2 | `test_s3_fallback.py` | 16 | ✅ |
| `test_api_init.py` | 3 | — | — | N/A |
| `test_create_file_bugfix_159.py` | 4 | — | — | ❌ |
| `test_inversion_solution_bug_93.py` | 1 | — | — | ❌ |
| `test_automation_task_mutation_deep.py` | 1 | — | — | ❌ |
| `test_file_download_url_bugfix_211.py` | 1 | — | — | ❌ |
| `test_source_solution_bugfix_214.py` | 1 | — | — | ❌ |
| `test_thing_relation_bugfix_95.py` | 1 | — | — | ❌ |
| `smoketests.py` | 0 (helper) | `test_smoketest_ab.py` | 19 | ✅ |
| `upload_test_s3_extract.py` | 0 (helper) | — | — | N/A |

### `hazard/` subdirectory

| Legacy test file | Tests | POC test file | POC tests | Status |
|---|---|---|---|---|
| `hazard/test_openquake_hazard_task.py` | 7 | `test_openquake.py` | 14 | ✅ |
| `hazard/test_openquake_hazard_solution.py` | 6 | `test_openquake.py` | 14 | ✅ |
| `hazard/test_openquake_hazard_config.py` | 2 | `test_openquake.py` | 14 | ✅ |
| `hazard/test_openquake_hazard_as_disagg_task.py` | 6 | — | — | ❌ |
| `hazard/test_openquake_sources_nrml_solution.py` | 8 | — | — | ❌ |
| `hazard/test_aggregate_inversion_solution.py` | 6 | `test_aggregate_inversion_solution.py` | 7 | ✅ |
| `hazard/test_scaled_inversion_solution.py` | 7 | `test_scaled_inversion_solution.py` | 6 | ✅ |
| `hazard/test_time_dependent_inversion_solution.py` | 6 | `test_time_dependent_inversion_solution.py` | 6 | ✅ |
| `hazard/test_file.py` | 2 | `test_smoketest_ab.py` (partial) | — | ⚠️ |
| `hazard/test_inversion_solution.py` | 2 | `test_inversion_solution.py` | 10 | ✅ |
| `hazard/test_bugfix_167_missing_fileunion.py` | 1 | — | — | ❌ |

### `rupture_set/` subdirectory

| Legacy test file | Tests | POC test file | POC tests | Status |
|---|---|---|---|---|
| `rupture_set/test_rupture_set_basic.py` | 4 | `test_rupture_set.py` | 7 | ✅ |
| `rupture_set/test_rupture_set_mutation_checks.py` | 4 | — | — | ❌ |
| `rupture_set/test_rupture_set_upload.py` | 1 | — | — | ❌ |
| `rupture_set/test_handle_legacy_data.py` | 2 | — | — | N/A |

### `simpler_relationships/`, `legacy/`, `e2e_workflows/`, `object_iteration/`, `swept_arguments/`

| Legacy test file | Tests | POC test file | POC tests | Status |
|---|---|---|---|---|
| `simpler_relationships/test_automation_task_related_solution_new.py` | 2 | `test_inversion_solution.py` (partial) | — | ⚠️ |
| `simpler_relationships/test_inversion_solution_file_migration_bug_new.py` | 3 | — | — | ❌ |
| `simpler_relationships/test_rupture_generation_related_files_new.py` | 1 | `test_smoketest_ab.py` | — | ⚠️ |
| `legacy/test_automation_task_related_solution.py` | 3 | — | — | N/A |
| `legacy/test_inversion_solution_file_migration_bug.py` | 3 | — | — | N/A |
| `legacy/test_rupture_generation_related_files.py` | 1 | — | — | N/A |
| `e2e_workflows/test_inversion_solution_table_e2e.py` | 1 | `test_inversion_solution.py` | — | ⚠️ |
| `object_iteration/test_divine_basedata_class_from_schema_name.py` | 3 | — | — | N/A |
| `object_iteration/test_iterate_items.py` | 2 | — | — | ❌ |
| `object_iteration/test_iterate_schema_types.py` | 1 | — | — | ❌ |
| `swept_arguments/test_baseline_swept_arguments.py` | 2 | `test_general_task.py` (partial) | — | ⚠️ |
| `swept_arguments/test_automation_task_swept_arg_validation.py` | 4 | — | — | ❌ |

**Totals:**
- Legacy total tests: ~178 (across all directories)
- POC total tests: ~115 (across all POC test files, excluding integration-only)

---

## 2. API Surface Map

### GeneralTask

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_general_task` | Yes | Yes | Yes | Yes |
| Mutation: `update_general_task` | Yes | Yes | Yes | Yes |
| Mutation: `create_task_relation` (GT→child) | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Query: `general_tasks` (list) | Yes | Yes | Yes | Yes |
| Field: `id` | Yes | Yes | Yes | Yes |
| Field: `title` | Yes | Yes | Yes | Yes |
| Field: `description` | Yes | Yes | Yes | Yes |
| Field: `agent_name` | Yes | Yes | Yes | Yes |
| Field: `created` | Yes | Yes | Yes | Yes |
| Field: `updated` | Yes | Yes | Yes | Yes |
| Field: `notes` | Yes | Yes | Yes | Yes |
| Field: `meta [k v]` | Yes | Yes | Yes | Yes |
| Field: `argument_lists [k v]` | Yes | Yes | Yes | Yes |
| Field: `swept_arguments` | Yes | Yes | Yes | Yes |
| Field: `subtask_count` | Yes | Yes | Yes | Yes |
| Field: `subtask_type` | Yes | Yes | Yes | Yes |
| Field: `subtask_result` | Yes | Yes | Yes | Yes |
| Field: `model_type` | Yes | Yes | Yes | Yes |
| Field: `children` (connection) | Yes | Yes | Yes | Yes |
| Field: `parents` (connection) | Yes | Yes | Yes | Yes |
| Field: `files` (connection) | Yes | Yes | Yes | Yes |

### AutomationTask

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_automation_task` | Yes | Yes | Yes | Yes |
| Mutation: `update_automation_task` | Yes | Yes | **No** | No |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Query: `automation_tasks` (list) | Yes | implicit | Yes | Yes |
| Field: `id` | Yes | Yes | Yes | Yes |
| Field: `task_type` | Yes | Yes | Yes | Yes |
| Field: `state` | Yes | Yes | Yes | Yes |
| Field: `result` | Yes | Yes | Yes | Yes |
| Field: `created` | Yes | Yes | Yes | Yes |
| Field: `duration` | Yes | Yes | Yes | Yes |
| Field: `arguments [k v]` | Yes | Yes | Yes | Yes |
| Field: `environment [k v]` | Yes | Yes | Yes | Yes |
| Field: `metrics [k v]` | Yes | Yes | Yes | Yes |
| Field: `model_type` | Yes | Yes | Yes | Yes |
| Field: `parents` (connection) | Yes | Yes | Yes | Yes |
| Field: `children` (connection) | Yes | Yes | Yes | Yes |
| Field: `files` (connection) | Yes | Yes | Yes | Yes |
| DateTime validation (timezone required) | Yes | Yes | **Yes (handled by Strawberry)** | Partial |
| DateTime validation (ISO format) | Yes | Yes | **Yes (handled by Strawberry)** | Partial |

### RuptureGenerationTask

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_rupture_generation_task` | Yes | Yes | Yes | Yes |
| Mutation: `update_rupture_generation_task` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Query: `rupture_generation_tasks` (list) | Yes | Yes | Yes | Yes |
| Field: `id`, `state`, `result`, `created`, `duration` | Yes | Yes | Yes | Yes |
| Field: `arguments [k v]` | Yes | Yes | Yes | Yes |
| Field: `environment [k v]` | Yes | Yes | Yes | Yes |
| Field: `metrics [k v]` | Yes | Yes | Yes | Yes |
| Field: `task_type` | Yes | Yes | Yes | Yes |
| Legacy field migration (`git_refs` → `environment`) | Yes | Yes | **No** | No |
| Field: `parents`, `children`, `files` | Yes | Yes | Yes | Yes |

### InversionSolution

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_inversion_solution` | Yes | Yes | Yes | Yes |
| Mutation: `append_inversion_solution_tables` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Query: `inversion_solutions` (list) | Yes | implicit | Yes | implicit |
| Field: `id`, `file_name`, `md5_digest`, `file_size`, `created` | Yes | Yes | Yes | Yes |
| Field: `meta [k v]` | Yes | Yes | Yes | Yes |
| Field: `metrics [k v]` | Yes | Yes | Yes | Yes |
| Field: `tables` (LabelledTableRelation list) | Yes | Yes | Yes | Yes |
| Field: `mfd_table_id` | Yes | Yes | Yes | Yes |
| Field: `mfd_table` (resolved Table) | Yes | Yes | Yes | Yes |
| Field: `hazard_table_id` | Yes | Yes | Yes | Yes |
| Field: `hazard_table` (resolved Table) | Yes | Yes | Yes | Partial (null case only) |
| Field: `produced_by` (union) | Yes | Yes | Yes | Yes |
| Field: `predecessors` | Yes | Yes | Yes | Yes |
| Field: `relations` (total_count) | Yes | Yes | Yes | Yes |
| Interface: `InversionSolutionInterface` fragment | Yes | Yes | Yes | Yes |
| Field: `post_url` (S3 pre-signed) | Yes | implicit | Yes (model field) | Not tested |

### ScaledInversionSolution

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_scaled_inversion_solution` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Field: `id`, `file_name`, `md5_digest`, `file_size`, `created` | Yes | Yes | Yes | Yes |
| Field: `source_solution` (union) | Yes | Yes | Yes | Yes |
| Field: `produced_by` (union) | Yes | Yes | Yes | Yes |
| Field: `predecessors` | Yes | Yes | Yes | Yes |
| Field: `post_url` | Yes | implicit | Yes (model field) | Not tested |
| Interface: `InversionSolutionInterface` via fragment | Yes | Yes | Yes | Yes |

### AggregateInversionSolution

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_aggregate_inversion_solution` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Field: `source_solutions` (union list) | Yes | Yes | Yes | Yes |
| Field: `common_rupture_set` | Yes | Yes | Yes | Yes |
| Field: `aggregation_fn` | Yes | Yes | Yes | Yes |
| Field: `produced_by` (union) | Yes | Yes | Yes | Yes |
| Field: `predecessors` | Yes | Yes | Yes | Yes |

### TimeDependentInversionSolution

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_time_dependent_inversion_solution` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Field: `source_solution`, `produced_by`, `predecessors` | Yes | Yes | Yes | Yes |
| Field: `id`, `file_name`, `md5_digest`, `file_size`, `created` | Yes | Yes | Yes | Yes |

### InversionSolutionNrml

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_inversion_solution_nrml` | Yes | Yes (8 tests) | Yes | **No** |
| Query: `node(id)` | Yes | Yes | Yes | **No** |
| Field: `source_solution` (from IS / ScaledIS / TDIS) | Yes | Yes | Yes | **No** |
| Field: `predecessors` | Yes | Yes | Yes | **No** |

### RuptureSet

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_rupture_set` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Query: `rupture_sets` (list) | Yes | Yes | Yes | Yes |
| Field: `id`, `file_name`, `md5_digest`, `file_size`, `created` | Yes | Yes | Yes | Yes |
| Field: `fault_models` | Yes | Yes | Yes | Yes |
| Field: `metrics [k v]` | Yes | Yes | Yes | Yes |
| Field: `produced_by` (union) | Yes | Yes | Yes | Yes |
| Mutation checks (fault model validation, etc.) | Yes | Yes (4 tests) | **No** | No |
| Presigned upload URL (`post_url`, `post_url_v2`) | Yes | Yes (1 test) | **No** | No |

### Table

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_table` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Field: `id`, `object_id`, `created`, `column_headers`, `column_types`, `rows` | Yes | Yes | Yes | Yes |
| Field: `meta [k v]` | Yes | Yes | Yes | Yes |
| Field: `dimensions [k v]` | Yes | Yes | Yes | Yes |
| Field: `table_type` | Yes | Yes | Yes | Yes |
| Field: `name` | Yes | Yes (bugfix 252) | **No** | No |
| Exception handling for un-serializable types (bugfix 252) | Yes | Yes | **No** | No |

### ToshiFile (generic File)

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_file` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Query: `files` (list) | Yes | implicit | Yes | implicit |
| Field: `id`, `file_name`, `md5_digest`, `file_size` | Yes | Yes | Yes | Yes |
| Field: `meta [k v]` | Yes | Yes | Yes | Yes |
| Field: `post_url` (S3 pre-signed) | Yes | Yes | Yes (model field) | Not tested |
| Field: `relations` (connection) | Yes | Yes | Yes | Yes |
| Field: `predecessors` | Yes | Yes | Yes | Not explicitly |
| BigInt file_size validation | Yes | Yes (4 tests: bigint/float/int/string) | **No separate test** | No |
| Download URL (bugfix 211) | Yes | Yes | **No** | No |

### SmsFile

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_sms_file` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Query: `sms_files` (list) | Yes | implicit | Yes | Yes |
| Field: `id`, `file_name`, `file_type`, `md5_digest`, `file_size`, `created` | Yes | Yes | Yes | Yes |
| Field: `relations` (connection) | Yes | Yes | Yes | Yes |
| `create_sms_file_link` mutation | Yes | Yes (commented out in legacy) | **No** | No |

### StrongMotionStation

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_strong_motion_station` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Query: `strong_motion_stations` (list) | Yes | Yes | Yes | Yes |
| Field: `id`, `created`, `site_code`, `site_class`, `site_class_basis` | Yes | Yes | Yes | Yes |
| Field: `Vs30_mean` | Yes | Yes | Yes | Yes |
| Field: `liquefiable` | Yes | implicit | Yes | implicit |
| Field: `files` (connection) | Yes | implicit | Yes | Yes |
| Mutation: `update_strong_motion_station` | Yes | skipped | **No** | No |
| DateTime validation (timezone required) | Yes | Yes | **Yes (Strawberry)** | Partial |

### OpenquakeHazardTask

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_openquake_hazard_task` | Yes | Yes | Yes | Yes |
| Mutation: `update_openquake_hazard_task` (with hazard_solution) | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Field: `id`, `state`, `result`, `task_type`, `created`, `duration` | Yes | Yes | Yes | Yes |
| Field: `arguments [k v]`, `environment [k v]`, `metrics [k v]` | Yes | Yes | Yes | Yes |
| Field: `srm_logic_tree` (JSONString) | Yes | Yes | Yes | Not tested |
| Field: `gmcm_logic_tree` (JSONString) | Yes | Yes | Yes | Not tested |
| Field: `openquake_config` (JSONString) | Yes | Yes | Yes | Not tested |
| Field: `config` (OpenquakeHazardConfig) | Yes | Yes | Yes | Not tested |
| Field: `hazard_solution` | Yes | Yes | Yes | Yes |
| Field: `executor` | Yes | Yes | Yes | Yes |
| Field: `model_type` | Yes | Yes | Yes | Not tested |
| `task_type: DISAGG` (disagg variant) | Yes | Yes (6 tests) | Yes (enum) | **No** |
| Legacy task default `task_type` handling | Yes | Yes | **No** | No |

### OpenquakeHazardSolution

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_openquake_hazard_solution` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Field: `id`, `created`, `task_type` | Yes | Yes | Yes | Yes |
| Field: `metrics [k v]` | Yes | Yes | Yes | Yes |
| Field: `produced_by` | Yes | Yes | Yes | Yes |
| Field: `csv_archive` | Yes | Yes | Yes | Not tested |
| Field: `hdf5_archive` | Yes | Yes | Yes | Not tested |
| Field: `task_args` | Yes | Yes | Yes | Not tested |
| Field: `predecessors` | Yes | Yes | Yes | Not tested |
| Required field validation (`task_type` required) | Yes | Yes (error case) | Yes | **No** |

### OpenquakeHazardConfig

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_openquake_hazard_config` | Yes | Yes | Yes | Yes |
| Query: `node(id)` | Yes | Yes | Yes | Yes |
| Field: `id`, `created` | Yes | Yes | Yes | Yes |
| Field: `template_archive` (resolved File) | Yes | Yes | Yes | Yes |
| Field: `source_models` (union list: NRML or File) | Yes | Yes | Yes | Yes (ToshiFile case only) |
| `source_models` resolving to `InversionSolutionNrml` | Yes | Yes | Yes | **No** |

### FileRelation

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_file_relation` | Yes | Yes | Yes | Yes |
| Query: file.relations.edges.node | Yes | Yes | Yes | Yes |
| Query: thing.files.edges.node | Yes | Yes | Yes | Yes |
| Field: `role` | Yes | Yes | Yes | Yes |
| Field: `file_id` | Yes | Yes | Yes | implicit |
| Field: `file` (resolved) | Yes | Yes | Yes | Yes |
| Field: `thing` (resolved) | Yes | Yes | Yes | Yes |
| Relation compression (>100 relations stored as compressed string) | Yes | Yes (3 tests) | Yes | Yes (6 tests) |

### TaskTaskRelation

| Item | Legacy defined | Legacy tested | In POC schema | POC tested |
|---|---|---|---|---|
| Mutation: `create_task_relation` | Yes | Yes | Yes | Yes |
| Query: thing.parents / thing.children | Yes | Yes | Yes | Yes |
| Field: `parent_id`, `child_id` | Yes | Yes | Yes | Yes |
| Field: `parent`, `child` (resolved union) | Yes | Yes | Yes | Yes |
| Data-layer ThingRelationData test (DB only) | Yes | Yes | **No test** | No |

---

## 3. Coverage Gap Detail

### Gap 1: `update_automation_task` mutation missing from POC

- **Legacy file:** `test_automation_task_schema.py` — `test_update_with_metrics`; also `test_automation_task_mutation_deep.py` — `test_update_with_metrics`
- **What it exercises:** `update_automation_task` mutation with `duration`, `metrics`, `state`, `result` fields; verifies ES re-indexing is called on update
- **Closest POC equivalent:** `update_rupture_generation_task` exists; `UpdateAutomationTaskInput` exists in POC models but no corresponding `update_automation_task` resolver or mutation in `schema.py`
- **Gap severity:** **Critical** — production pipelines (nzshm-runzi) call `update_automation_task` to record metrics and state transitions for every INVERSION task

### Gap 2: `InversionSolutionNrml` — no POC tests at all

- **Legacy files:** `hazard/test_openquake_sources_nrml_solution.py` — 8 tests covering: create NRML from IS, ScaledIS, TDIS; with predecessors; node lookup; with predecessors node; source_solution union resolution
- **What it exercises:** `create_inversion_solution_nrml` mutation; `source_solution` field resolving to `SourceSolutionUnion`; `InversionSolutionNrml` node lookup; `PredecessorsInterface` on NRML
- **Closest POC equivalent:** Schema and model are fully implemented in POC; no test file exists
- **Gap severity:** **Critical** — InversionSolutionNrml is a required intermediate object in the OpenquakeHazardConfig.source_models chain; weka and runzi create these as part of every hazard run

### Gap 3: DISAGG task type not tested in POC

- **Legacy files:** `hazard/test_openquake_hazard_as_disagg_task.py` — 6 tests: create disagg task, node lookup, `task_type: DISAGG` returned correctly; also `test_legacy_hazard_task_has_default_task_type`
- **What it exercises:** `create_openquake_hazard_task` with `task_type: DISAGG`; verifying returned `task_type` is `DISAGG`; legacy objects where task_type field is absent default gracefully
- **Closest POC equivalent:** `DISAGG` enum value exists in POC `OpenquakeTaskType`; `test_openquake.py` only tests `HAZARD` variant
- **Gap severity:** **High** — disaggregation runs are a distinct and regular production workflow

### Gap 4: Rupture set mutation validation and upload not tested

- **Legacy files:** `rupture_set/test_rupture_set_mutation_checks.py` (4 tests: fault model field validation); `rupture_set/test_rupture_set_upload.py` (1 test: S3 presigned URL upload workflow with `post_url` / `post_url_v2`)
- **What it exercises:** Validation of `fault_models` field; S3 pre-signed POST URL generation and upload using `requests` library; `post_url_v2` format
- **Closest POC equivalent:** `test_rupture_set.py` tests basic create/lookup; no validation or upload tests
- **Gap severity:** **High** — rupture set upload is the first step in every production inversion run; `post_url` is the mechanism clients use to transfer files

### Gap 5: Table `name` field and exception handling (bugfix 252)

- **Legacy file:** `test_table_schema_fix_252.py` — 3 tests: `test_create_252_example_table` (uses `name` field in input); `test_create_one_table` (full moto-backed); `test_new_logging_exception_handling` (verifies `json_serialised` error surfaced correctly)
- **What it exercises:** `name` field in `create_table` input; logging/error propagation when a DynamoDB write fails due to non-serialisable object
- **Closest POC equivalent:** `test_table.py` tests create/lookup but does not use `name` and has no error case test
- **Gap severity:** **High** — the `name` field is used by nzshm-runzi when creating tables; the error handling test protects a regression introduced by bugfix 252

### Gap 6: File relation compression — **CLOSED**

- **Legacy file:** `test_file_relation_compression.py` — 3 tests: counting relations in a 390k-relation scenario; adding with compression; round-trip with compression
- **Storage shape:** Both legacy and POC store relations as an embedded array under `ToshiFileObject.object_content.relations`. Storage shape is **identical** — only the compression behaviour differed.
- **Original concrete bugs this would have introduced:**
  1. **Read failure on legacy data.** Any production File with >100 relations is stored as a base64-encoded zlib string (`compress_string(json.dumps(relations))`). The POC's Pydantic validation on `ToshiFileData.relations: list[dict] | None` rejected strings — propagating as "Unexpected error" on every field of the affected node.
  2. **Write failure at DynamoDB's 400KB item-size limit.** Without compression, a list of `{"id": "...", "role": "read"}` entries (~40 bytes each in JSON) hits the limit at roughly 10,000 entries. Legacy fits ~80,000 in the same space via compression.
- **Closed in this PR (`strawberry-poc-compression`, commit 47bd09a):**
  - Ported `nzshm_common.util.compress_string` / `decompress_string` into `data/dynamo.py` (`_ensure_decompressed`, `_decompress_file_relations` helpers wired into `get_file`, `list_files`, `create_file_relation`).
  - Write-side threshold: `relations` is compressed to a string once `len(relations) > UNCOMPRESSED_LIMIT=100`, matching legacy semantics.
  - Added `tests/test_file_relation_compression.py` (6 tests): legacy compressed-row decompression, GraphQL round-trip of >100-relation files, the threshold flip, and a 1000-relation stress test.

### Gap 7: S3 fallback and DynamoDB + S3 combined queries

- **Legacy files:** `test_s3_fallback.py` (2 tests); `test_dynamo_and_s3_queries.py` (9 tests)
- **What it exercises:** Reading legacy objects from S3 when not found in DynamoDB; combined queries that retrieve both DynamoDB and S3-backed objects in the same request; parent/child traversal with mixed storage.
- **Severity (corrected from earlier analysis):** **High**, not "Low / Low for new data". Two reasons the earlier classification was wrong:
  1. **The deployed `/graphql-v2` Lambda is silently broken for pre-DynamoDB-era data.** `data/dynamo.py` has `_from_s3()` wired into `get_thing` and `get_file`, but PR #297's serverless.yml doesn't set `S3_BUCKET_NAME` on the function env, and the function role doesn't grant `s3:GetObject`/`s3:ListBucket`. With `S3_BUCKET_NAME=""`, the helper short-circuits and any query for an ID below FIRST_DYNAMO_ID (100000) returns null — same "Unexpected error on every field" failure mode as the GeneralTask enum incident.
  2. **`legacy_object_identities` is structurally broken even with the deploy fix.** The resolver returns `{object_type: "Thing" | "File" | "Table"}` instead of the concrete `clazz_name`, so clients can't construct relay GlobalIDs that `node()` will dispatch. It also lacks the `FIRST_DYNAMO_ID` watermark filter that legacy uses to avoid double-yielding File-prefixed IDs already in DynamoDB.
- **POC state before this PR:**
  - `data/dynamo._from_s3` existed, called from `get_thing` and `get_file` only (not `get_table`).
  - `data/s3.scan_s3_paginated` listed `CommonPrefixes` but didn't fetch object JSON, so `object_type` was the store bucket instead of the class name.
  - Zero test coverage on any of these paths.
- **Closed in this PR (`strawberry-poc-s3-fallback`):**
  - `data/s3.scan_s3_paginated` now fetches `clazz_name` from each candidate's `object.json` and applies the FIRST_DYNAMO_ID watermark for FileData (matches `graphql_api/data/base_data.py:178-187`).
  - `data/dynamo.get_table` now mirrors `get_thing`/`get_file` for the S3-miss path.
  - `tests/test_s3_fallback.py` adds 16 tests using moto: `_from_s3` round-trip, `get_thing`/`get_file`/`get_table` fallback, the `_is_pre_dynamo_file_id` watermark helper, `scan_s3_paginated` clazz_name surfacing, the FileData watermark filter, ThingData absence of watermark, and StartAfter pagination.
- **Still deferred (separate concern, belongs in PR #297):**
  - `/graphql-v2` Lambda env must set `S3_BUCKET_NAME` and IAM must grant `s3:GetObject`+`s3:ListBucket` on the bucket. Without this, the code fixed here never executes in deployment.
  - First-touch write-back migration (`create_file_relation` against an S3-only file should materialise the file into DynamoDB before patching, like `graphql_api/data/file_relation_data.py:48-58`). Currently the POC raises `ValueError`. Read-only POC stage doesn't hit this; promote to High once the POC moves to read-write.
- **Reference tests (legacy parity):** the test file mirrors `test_s3_fallback.py` + key cases from `test_dynamo_and_s3_queries.py`. Full DynamoDB+S3 mixed-traversal coverage (parent/child walking across both stores) is still open as a smaller follow-up.

### Gap 8: Elasticsearch search manager tests

- **Legacy file:** `test_search_manager.py` — 9 tests including `SearchManager` unit tests, `test_query_with_mock_requests`, `total_count` from ES response, and `traversing_into_s3_api_call` (ensures search doesn't trigger expensive S3 reads)
- **Closest POC equivalent:** `test_smoketest_ab.py` has 5 integration tests (`@pytest.mark.integration`) that run against live ES; no unit tests of the search layer with mocked HTTP
- **Gap severity:** **Medium** — the POC search layer is thin (`data/search.py`) and works differently; unit tests would catch regressions in the `_dispatch_search` dispatch table

### Gap 9: File download URL (bugfix 211)

- **Legacy file:** `test_file_download_url_bugfix_211.py` — 1 test: calling a resolver that previously made a direct S3 API call is now handled without an `UploadPartCopy` error
- **What it exercises:** That querying `file_name` on a file object does not incidentally trigger an S3 download
- **Closest POC equivalent:** None — the POC does not perform S3 API calls for metadata reads
- **Gap severity:** **Low** — architecture-specific to legacy S3 data access pattern

### Gap 10: `create_file` BigInt / type coercion (bugfix 159)

- **Legacy file:** `test_create_file_bugfix_159.py` — 4 tests: `file_size` as BigInt, float, int, string
- **What it exercises:** That the `file_size` scalar correctly coerces or rejects non-integer inputs
- **Closest POC equivalent:** None — POC uses Python's native `int` type; Strawberry handles coercion but no explicit tests exist
- **Gap severity:** **Medium** — clients in the wild (nzshm-runzi) may send float `file_size` values

### Gap 11: `srm_logic_tree`, `gmcm_logic_tree`, `openquake_config` JSON fields not tested in POC

- **Legacy file:** `hazard/test_openquake_hazard_task.py` — `test_get_openquake_hazard_task_node` and `test_create_oq_hazard_task` verify these JSONString round-trips
- **What it exercises:** That serialised JSON strings survive the DynamoDB round-trip and are returned correctly
- **Closest POC equivalent:** POC `test_openquake.py` creates an `OpenquakeHazardTask` but does not set or verify these fields
- **Gap severity:** **High** — these fields are required by the hazard workflow; every production OpenquakeHazardTask carries all three

### Gap 12: OpenquakeHazardSolution `csv_archive`, `hdf5_archive`, `task_args`, predecessors not tested

- **Legacy file:** `hazard/test_openquake_hazard_solution.py` — `test_create_openquake_hazard_solution_with_predecessors` and `test_get_oq_hazard_solution_with_pred` exercise all three file references and predecessors depth/relationship
- **Closest POC equivalent:** `test_openquake.py` creates a solution but does not set or verify `csv_archive`, `hdf5_archive`, `task_args`, or predecessors
- **Gap severity:** **High** — both archives are required inputs in production

### Gap 13: `nodes(id_in: [...])` multi-fetch and interface expansion

- **Legacy file:** `test_nodes_bugfix_220.py` — 3 tests covering `nodes` query with `ScaledInversionSolution` result; interface expansions (`InversionSolutionInterface`, `FileInterface`, `AutomationTaskInterface` with parents navigation)
- **Closest POC equivalent:** POC `schema.py` implements `nodes` query and it is exercised through individual mutations, but there is no dedicated test for the multi-fetch query with interface fragment expansion including parent traversal
- **Gap severity:** **Critical** — weka uses `nodes(id_in: [...])` with deep `AutomationTaskInterface.parents` expansion as its primary batch data-retrieval pattern

### Gap 14: Swept argument validation on AutomationTask creation

- **Legacy files:** `swept_arguments/test_automation_task_swept_arg_validation.py` (4 tests) — verifies that AutomationTask arguments must align with the parent GeneralTask's swept arguments; error cases when required swept arg is missing or value not in GT's list
- **Closest POC equivalent:** `test_general_task.py::test_swept_arguments` tests the GT swept_arguments computation; no AT argument validation against GT exists in POC
- **Gap severity:** **Medium** — validation was added to prevent malformed experiment data; clients set arguments explicitly so this rarely fails in practice

### Gap 15: `hazard/test_bugfix_167_missing_fileunion.py`

- **Legacy file:** 1 test — verifies that querying a `file_union` field on a type that can return either an `InversionSolution` or a plain `File` returns the correct type
- **Closest POC equivalent:** `test_inversion_solution_interface.py` and `test_openquake.py` exercise union fields but do not specifically test the "missing file union" scenario
- **Gap severity:** **Low** — narrow regression test for a specific legacy bug

---

## 4. Mutations Gap Table

| Mutation (legacy) | In POC schema | POC unit test | Notes |
|---|---|---|---|
| `create_general_task` | ✅ | ✅ | — |
| `update_general_task` | ✅ | ✅ | — |
| `create_automation_task` | ✅ | ✅ | — |
| `update_automation_task` | ❌ **MISSING** | ❌ | `UpdateAutomationTaskInput` exists in model; mutation not wired in `schema.py` |
| `create_rupture_generation_task` | ✅ | ✅ | — |
| `update_rupture_generation_task` | ✅ | ✅ | — |
| `create_rupture_set` | ✅ | ✅ | — |
| `create_file` | ✅ | ✅ | — |
| `create_sms_file` | ✅ | ✅ | — |
| `create_sms_file_link` | ❌ **MISSING** | ❌ | Legacy also had commented-out test |
| `create_strong_motion_station` | ✅ | ✅ | — |
| `update_strong_motion_station` | ❌ **MISSING** | ❌ | Legacy test was skipped |
| `create_table` | ✅ | ✅ | `name` field not in POC input |
| `create_task_relation` | ✅ | ✅ | — |
| `create_file_relation` | ✅ | ✅ | — |
| `create_inversion_solution` | ✅ | ✅ | — |
| `append_inversion_solution_tables` | ✅ | ✅ | — |
| `create_scaled_inversion_solution` | ✅ | ✅ | — |
| `create_aggregate_inversion_solution` | ✅ | ✅ | — |
| `create_time_dependent_inversion_solution` | ✅ | ✅ | — |
| `create_inversion_solution_nrml` | ✅ | ❌ **NOT TESTED** | Mutation in schema; model complete; zero tests |
| `create_openquake_hazard_config` | ✅ | ✅ | InversionSolutionNrml source_models case untested |
| `create_openquake_hazard_solution` | ✅ | ⚠️ | `csv_archive`, `hdf5_archive`, `task_args`, predecessors not tested |
| `create_openquake_hazard_task` | ✅ | ⚠️ | `srm_logic_tree`, `gmcm_logic_tree`, `openquake_config` fields not tested; DISAGG variant not tested |
| `update_openquake_hazard_task` | ✅ | ✅ | — |
| `reindex` | ✅ | ✅ | POC addition; no legacy equivalent |

---

## 5. Fields Gap Table

Fields present in legacy schema but absent or different in POC model classes.

### AutomationTask / RuptureGenerationTask (POC: `models/automation_task.py`)

| Legacy field | POC model field | Status |
|---|---|---|
| `model_type` (ModelType enum) | `model_type` | ✅ present |
| `task_type` (TaskSubType enum) | `task_type` | ✅ present |
| `state`, `result` | `state`, `result` | ✅ present |
| `duration`, `created`, `updated` | `duration`, `created`, `updated` | ✅ present |
| `arguments`, `environment`, `metrics` | `arguments`, `environment`, `metrics` | ✅ present |
| `parents`, `children`, `files` (connections) | `parents`, `children`, `files` | ✅ present |
| `git_refs` (legacy field, migrated to `environment`) | Not present | ⚠️ legacy migration path untested |

### GeneralTask (POC: `models/general_task.py`)

| Legacy field | POC model field | Status |
|---|---|---|
| All core fields | All present | ✅ |

### InversionSolution (POC: `models/inversion_solution.py`)

| Legacy field | POC model field | Status |
|---|---|---|
| `mfd_table_id`, `mfd_table` | ✅ present | ✅ |
| `hazard_table_id`, `hazard_table` | ✅ present | ✅ |
| `tables` (LabelledTableRelation list) | ✅ present | ✅ |
| `produced_by` | ✅ present | ✅ |
| `post_url` | ✅ present (not tested) | ⚠️ |
| `relations` (total_count, edges) | ✅ present | ✅ |

### Table (POC: `models/table.py`)

| Legacy field | POC model field | Status |
|---|---|---|
| `name` | **Not present** | ❌ missing — used by nzshm-runzi bugfix 252 |
| `column_headers`, `column_types`, `rows` | ✅ present | ✅ |
| `meta`, `dimensions`, `table_type`, `object_id` | ✅ present | ✅ |

### OpenquakeHazardTask (POC: `models/openquake_hazard_task.py`)

| Legacy field | POC model field | Status |
|---|---|---|
| `srm_logic_tree`, `gmcm_logic_tree`, `openquake_config` | ✅ present | ✅ (not tested) |
| `model_type` | ✅ present | ✅ (not tested) |
| `config` (resolved) | ✅ present | ✅ (not tested) |
| `hazard_solution` (resolved) | ✅ present | ✅ |
| `executor` | ✅ present | ✅ |

### OpenquakeHazardSolution (POC: `models/openquake_hazard_solution.py`)

| Legacy field | POC model field | Status |
|---|---|---|
| `csv_archive`, `hdf5_archive`, `task_args` | ✅ present | ✅ (not tested) |
| `predecessors` | ✅ present | ✅ (not tested) |
| `task_type` | ✅ present | ✅ |
| `metrics` | ✅ present | ✅ |
| `modified_config` | **Not in legacy tests** | N/A |

### RuptureSet (POC: `models/rupture_set.py`)

| Legacy field | POC model field | Status |
|---|---|---|
| `fault_models` | ✅ present | ✅ |
| `post_url`, `post_url_v2` | `post_url` present; `post_url_v2` not present | ⚠️ `post_url_v2` missing |
| `metrics` | ✅ present | ✅ |

### SmsFile (POC: `models/sms_file.py`)

| Legacy field | POC model field | Status |
|---|---|---|
| `file_type` (SmsFileType enum) | ✅ present | ✅ |
| `relations` | ✅ present | ✅ |
| `post_url` | ✅ present (not tested) | ⚠️ |

### StrongMotionStation (POC: `models/strong_motion_station.py`)

| Legacy field | POC model field | Status |
|---|---|---|
| `site_code`, `site_class`, `site_class_basis` | ✅ present | ✅ |
| `Vs30_mean` | ✅ present | ✅ |
| `liquefiable` | ✅ present | ✅ (not explicitly tested) |
| `updated` | ✅ present | ✅ |

### InversionSolutionNrml (POC: `models/inversion_solution_nrml.py`)

| Legacy field | POC model field | Status |
|---|---|---|
| `source_solution` (SourceSolutionUnion) | ✅ present | ✅ (not tested) |
| `predecessors` | ✅ present | ✅ (not tested) |
| `file_name`, `md5_digest`, `file_size` | ✅ present | ✅ (not tested) |

---

## 6. Priorities for New POC Tests

The following gaps represent the highest-value work to close, ordered by severity.

### Closed in this round (PRs #296–#298)

1. ~~**`update_automation_task` mutation**~~ — done. Resolver + payload type wired in `schema.py`; `tests/test_automation_task.py` covers create + update + ES re-index monkeypatch.
2. ~~**`nodes(id_in: [...])` with deep interface expansion**~~ — done. `tests/test_nodes_query.py` mirrors the weka batch traversal pattern (ScaledIS → produced_by → AutomationTask → parents → GeneralTask).
3. ~~**`InversionSolutionNrml` test file**~~ — done. `tests/test_inversion_solution_nrml.py`: 6 tests covering all three source types + predecessors.
4. ~~**DISAGG task type**~~ — done. New fixture in `tests/test_openquake.py`.
5. ~~**JSON logic tree round-trips**~~ — done.
6. ~~**`OpenquakeHazardSolution` archives**~~ — done.
7. ~~**Table `name` field**~~ — done.
8. ~~**`create_file` type coercion**~~ — done; BigInt scalar landed in `models/common.py` so >2GB file_size values now round-trip correctly.
9. **Rupture set upload / `post_url`** — schema-level test only (post_url returns null in POC; real S3 wiring deferred).
10. ~~**`update_automation_task` ES re-indexing**~~ — done; automatic via existing `update_thing` → `index_document` path, asserted via monkeypatch in test.

11. ~~**File relation compression (Gap 6)**~~ — done in `strawberry-poc-compression` (commit 47bd09a, folded into #310). `nzshm_common.util.compress_string`/`decompress_string` wired into `get_file`/`list_files`/`create_file_relation`; write threshold at `UNCOMPRESSED_LIMIT=100` matches legacy. 6 tests in `tests/test_file_relation_compression.py`.

### Open — needs follow-up work

The genuinely-open items after #310 + #313 are lower priority than the above:

- **Gap 4** — Rupture set mutation-validation tests (4) and real S3 presigned-POST upload workflow (1).
- **Gap 8** — Elasticsearch search-manager unit tests (9). Integration smoketests cover the path; unit-level regression coverage on `_dispatch_search` is missing.
- **Gap 14** — Swept-argument validation on AutomationTask creation (4 legacy tests).
- Low priority: Gap 9 (download URL bugfix 211; architecture-specific), Gap 15 (bug 167 fileunion regression), `post_url`-family field coverage on multiple types.
