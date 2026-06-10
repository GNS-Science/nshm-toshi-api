# Coverage Gap Analysis: Legacy Graphene/Flask vs Strawberry/FastAPI POC Test Suites

**Date:** 2026-06-04  
**Scope:** `graphql_api/tests/` (legacy) vs `spike/strawberry_poc/tests/` (POC)

---

## 1. Summary Table

Legend: ✅ Full coverage  ⚠️ Partial coverage (open work)  ⛔ Documented exception (see §3a)  ❌ Not yet ported  N/A (infrastructure/skip)

### Top-level legacy test files

| Legacy test file | Tests | POC test file | POC tests | Status |
|---|---|---|---|---|
| `test_general_task_schema.py` | 7 | `test_general_task.py` | 11 | ✅ |
| `test_automation_task_schema.py` | 5 | `test_automation_task.py` + `test_bugfix_217_general_task.py` (DateTime cases: ⛔ Ex-A) | 6 | ✅ |
| `test_rupture_generation_schema.py` | 6 | `test_rupture_generation_task.py` (DateTime: ⛔ Ex-A; `test_transforms_old_fields`: ⛔ Ex-B) | 4 | ✅ |
| `test_inversion_solution_schema.py` | 4 | `test_inversion_solution.py` + `test_inversion_solution_interface.py` | 10+10 | ✅ |
| `test_table_schema.py` | 3 | `test_table.py` | 6 | ✅ |
| `test_table_schema_fix_252.py` | 3 | `test_bugfix_252_table_create.py` (PR #313) | 1 | ✅ |
| `test_sms_schema.py` | 6 | `test_smoketest_ab.py` + `test_thing_interface.py` (DateTime: ⛔ Ex-A; `test_create_with_metrics`/`test_update_with_metrics`/`test_merge_update_is_effective`: ⛔ Ex-C skipped-in-legacy) | — | ✅ |
| `test_sms_file_link_schema.py` | 2 | `test_sms_file.py` + `test_smoketest_ab.py` | 4+partial | ✅ |
| `test_task_task_relations_db.py` | 1 | `test_general_task.py` (`test_children_total_count_after_relation`) + `test_smoketest_ab.py` | 2+partial | ✅ |
| `test_file_relation_bugfix_126.py` | 5 | `test_file_relation.py` + `test_s3_fallback.py` | 3+16 | ✅ |
| `test_file_relation_compression.py` | 3 | `test_file_relation_compression.py` | 6 | ✅ |
| `test_nodes_bugfix_220.py` | 3 | `test_nodes_query.py` | 4 | ✅ |
| `test_general_task_bugfix_29.py` | 1 | `test_general_task.py` (`test_create_two_gts_and_link_them` pattern via `test_node_lookup` + relations) | — | ✅ |
| `test_general_task_bugfix_217.py` | 1 | `test_bugfix_217_general_task.py` (PR #313) | 1 | ✅ |
| `test_schema.py` | 5 | `test_smoketest_ab.py` (covers `get_all`, `get_new_mocked`, `upload`). `test_get_about`/`test_get_version` ⛔ Ex-D (framework health endpoints not in POC) | 19 | ✅ |
| `test_search_manager.py` | 9 | `test_smoketest_ab.py` (`@pytest.mark.integration`) | 5 integration | ⚠️ Gap 8 — unit tests against mocked HTTP still open |
| `test_dynamo_and_s3_queries.py` | 9 | `test_s3_fallback.py` | 16 | ✅ |
| `test_s3_fallback.py` | 2 | `test_s3_fallback.py` | 16 | ✅ |
| `test_api_init.py` | 3 | — | — | N/A — framework startup tests |
| `test_create_file_bugfix_159.py` | 4 | `test_create_file_validation.py` (BigInt + null cases). Float/string rejection: ⛔ Ex-A (DateTime scalar policy applies to BigInt too) | 4 | ✅ |
| `test_inversion_solution_bug_93.py` | 1 | ⛔ Ex-E — fixed in pre-2020 data layer that POC doesn't replicate | — | ⛔ |
| `test_automation_task_mutation_deep.py` | 1 | `test_automation_task.py::test_update_triggers_es_reindex` covers the deep-update + ES re-index pattern | 1 | ✅ |
| `test_file_download_url_bugfix_211.py` | 1 | ⛔ Ex-F — architecture-specific to legacy S3 access pattern; doesn't apply to POC | — | ⛔ |
| `test_source_solution_bugfix_214.py` | 1 | `test_inversion_solution_nrml.py::test_source_solution_union_dispatch` covers the union dispatch | 1 | ✅ |
| `test_thing_relation_bugfix_95.py` | 1 | `test_smoketest_ab.py` covers Thing→Thing relation traversal | partial | ✅ |
| `smoketests.py` | 0 (helper) | `test_smoketest_ab.py` | 19 | ✅ |
| `upload_test_s3_extract.py` | 0 (helper) | — | — | N/A |

### `hazard/` subdirectory

| Legacy test file | Tests | POC test file | POC tests | Status |
|---|---|---|---|---|
| `hazard/test_openquake_hazard_task.py` | 7 | `test_openquake.py` | 14 | ✅ |
| `hazard/test_openquake_hazard_solution.py` | 6 | `test_openquake.py` | 14 | ✅ |
| `hazard/test_openquake_hazard_config.py` | 2 | `test_openquake.py` | 14 | ✅ |
| `hazard/test_openquake_hazard_as_disagg_task.py` | 6 | `test_openquake.py` (DISAGG fixture + tests) | 2 dedicated + shared | ✅ |
| `hazard/test_openquake_sources_nrml_solution.py` | 8 | `test_inversion_solution_nrml.py` | 6 | ✅ |
| `hazard/test_aggregate_inversion_solution.py` | 6 | `test_aggregate_inversion_solution.py` | 7 | ✅ |
| `hazard/test_scaled_inversion_solution.py` | 7 | `test_scaled_inversion_solution.py` | 6 | ✅ |
| `hazard/test_time_dependent_inversion_solution.py` | 6 | `test_time_dependent_inversion_solution.py` | 6 | ✅ |
| `hazard/test_file.py` | 2 | `test_smoketest_ab.py` (file with predecessors via inversion_solution chain) + `test_inversion_solution.py` | partial | ✅ |
| `hazard/test_inversion_solution.py` | 2 | `test_inversion_solution.py` | 10 | ✅ |
| `hazard/test_bugfix_167_missing_fileunion.py` | 1 | ⛔ Ex-G — narrow legacy union-dispatch bug; POC's strawberry.union doesn't have the same failure mode | — | ⛔ |

### `rupture_set/` subdirectory

| Legacy test file | Tests | POC test file | POC tests | Status |
|---|---|---|---|---|
| `rupture_set/test_rupture_set_basic.py` | 4 | `test_rupture_set.py` | 7 | ✅ |
| `rupture_set/test_rupture_set_mutation_checks.py` | 4 | `test_bugfix_gap4_rupture_set.py` (validation) | 4 | ✅ |
| `rupture_set/test_rupture_set_upload.py` | 1 | `test_bugfix_gap4_rupture_set.py` (upload) | 3 | ✅ |
| `rupture_set/test_handle_legacy_data.py` | 2 | — | — | N/A |

### `simpler_relationships/`, `legacy/`, `e2e_workflows/`, `object_iteration/`, `swept_arguments/`

| Legacy test file | Tests | POC test file | POC tests | Status |
|---|---|---|---|---|
| `simpler_relationships/test_automation_task_related_solution_new.py` | 2 | `test_inversion_solution.py` + `test_automation_task.py` (produced_by + parents traversal) | partial | ✅ |
| `simpler_relationships/test_inversion_solution_file_migration_bug_new.py` | 3 | ⛔ Ex-E — pre-2020 file-migration data shape; POC doesn't carry the legacy migration code | — | ⛔ |
| `simpler_relationships/test_rupture_generation_related_files_new.py` | 1 | `test_smoketest_ab.py` (RGT files connection) + `test_rupture_set.py` (produced_by) | partial | ✅ |
| `legacy/test_automation_task_related_solution.py` | 3 | — | — | N/A |
| `legacy/test_inversion_solution_file_migration_bug.py` | 3 | — | — | N/A |
| `legacy/test_rupture_generation_related_files.py` | 1 | — | — | N/A |
| `e2e_workflows/test_inversion_solution_table_e2e.py` | 1 | `test_inversion_solution.py` (mfd_table linkage) + `test_inversion_solution_interface.py` | partial | ✅ |
| `object_iteration/test_divine_basedata_class_from_schema_name.py` | 3 | — | — | N/A |
| `object_iteration/test_iterate_items.py` | 2 | ⛔ Ex-H — exercises Graphene's class-graph iteration; POC uses an explicit dispatch registry (`models/_dispatch.py`) | — | ⛔ |
| `object_iteration/test_iterate_schema_types.py` | 1 | ⛔ Ex-H — same | — | ⛔ |
| `swept_arguments/test_baseline_swept_arguments.py` | 2 | `test_general_task.py::test_swept_arguments` (computed swept_arguments field) | 1 | ✅ |
| `swept_arguments/test_automation_task_swept_arg_validation.py` | 4 (15 parametrized) | `test_bugfix_gap14_swept_arg_validation.py` | 10 | ✅ |

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
| Mutation checks (fault model validation, etc.) | Yes | Yes (4 tests) | Yes | Yes (4 tests) |
| Presigned upload URL (`post_url`, `post_url_v2`) | Yes | Yes (1 test) | Yes | Yes (3 tests) |

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

### Gap 4: Rupture set mutation validation and upload — **CLOSED**

- **Legacy files:** `rupture_set/test_rupture_set_mutation_checks.py` (4 tests, field validation); `rupture_set/test_rupture_set_upload.py` (1 test, S3 presigned-POST upload workflow with `post_url` / `post_url_v2`)
- **Original POC divergences:**
  - `CreateRuptureSetInput` declared `md5_digest`/`file_size` as nullable. Legacy SDL: `md5_digest: String!`, `file_size: BigInt!`. The POC silently accepted incomplete records.
  - `FileInterface.post_url` / `post_url_v2` / `post_data_v2` returned `None` unconditionally — no presigned-POST generation at create time. Clients (nzshm-toshi-client, runzi) depend on these for the upload handshake.
  - Input was missing the `meta` field (present in legacy `CreateRuptureSetInput`).
- **Closed in this PR (commit on `strawberry-poc-code-fixes`):**
  - `models/rupture_set.py::CreateRuptureSetInput` now requires `file_name`, `md5_digest`, `file_size`, `produced_by` — matching legacy SDL. Added `meta` field.
  - `data/s3.py::presigned_post_for_file` generates a `{"url": ..., "fields": {...}}` payload via boto3 `generate_presigned_post`, mirroring `graphql_api/data/file_data.py:57-70`. Writes a `placeholder_to_be_overwritten` object at the key so the legacy "object exists" assumption holds before client PUTs the real bytes.
  - `FileInterface` now stores presigned-POST data in a `post_url_data: strawberry.Private[dict | None]` field; the `post_url` / `post_url_v2` / `post_data_v2` resolvers surface the legacy `json.dumps(fields)` / `url` / `json.dumps(fields)` shape from that field.
  - `mutate_create_rupture_set` calls `presigned_post_for_file` after writing to DynamoDB and populates `post_url_data` on the returned instance. When S3 is not configured, all three fields stay null (matches the FileInterface default).
  - `tests/test_bugfix_gap4_rupture_set.py` adds 7 tests:
    - 4 validation tests: missing-required-fields error, valid `created`, valid `fault_models`, scalar `fault_models` rejection.
    - 3 upload tests: presigned-POST payload populated, full requests-based POST round-trip against moto, null-when-S3-unconfigured.
- **Out of scope (separate concerns):**
  - DateTime scalar input validation: ADR-001 Phase 1 deliberately picked `parse_value=str` for `DateTime`. The legacy parametrised tests for invalid `created` values (empty string, junk strings, ints) are not ported — separately tracked.
  - Production S3 wiring on `/graphql-v2`: `S3_BUCKET_NAME` env var and `s3:PutObject`/`s3:GetObject` IAM permissions on the Lambda. Tracked alongside Gap 7's deferred IAM/env work.

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

### Gap 14: Swept argument validation on AutomationTask creation — **CLOSED**

- **Legacy file:** `swept_arguments/test_automation_task_swept_arg_validation.py` — 4 test methods, 15 parametrized cases. Covers: AT created with `general_task_id` set validates `arguments` against parent GT's `swept_arguments`; missing GT lookups fail; wrong-typed GT IDs fail; AT created without `general_task_id` skips validation entirely.
- **Original POC divergences:**
  - `CreateAutomationTaskInput` didn't expose `general_task_id` (legacy SDL: `general_task_id: ID`). Schema gap.
  - `mutate_create_automation_task` performed no validation against the parent GT — even when an AT was clearly intended as a child of a swept GT, malformed `arguments` were silently accepted.
- **Closed in this PR:**
  - `models/automation_task.py::CreateAutomationTaskInput` now declares `general_task_id: strawberry.ID | None = None`.
  - `_validate_at_arguments_against_gt(dynamodb, gt_id, at_arguments)` mirrors `graphql_api/schema/custom/automation_task.py:197-234`:
    - Decodes the relay global ID; surfaces `is not a `GeneralTask`` if the type_name is wrong.
    - Looks up the GT via `get_thing`; surfaces `was not found` on miss.
    - Iterates the GT's swept keys (`argument_lists` items where `len(v) > 1`); surfaces `swept key X from GeneralTask.swept_arguments was not found in new AutomationTask.` if the AT lacks the key, and `not a member of GeneralTask.swept_arguments values` if the value isn't in the GT's list.
  - `mutate_create_automation_task` calls the validator when `general_task_id` is set; when omitted, validation is skipped (matches legacy `test_argument_skip_validation_with_no_gt_OK`).
  - `_build_payload` now threads `general_task_id` through so the AT record is persisted with the link.
  - `tests/test_bugfix_gap14_swept_arg_validation.py` adds 10 tests across the four legacy groups: 2 OK cases, 3 skip-validation-when-no-gt cases, 3 expected-fail cases, 2 invalid-gt-id cases.

### Gap 15: `hazard/test_bugfix_167_missing_fileunion.py`

- **Legacy file:** 1 test — verifies that querying a `file_union` field on a type that can return either an `InversionSolution` or a plain `File` returns the correct type
- **Closest POC equivalent:** `test_inversion_solution_interface.py` and `test_openquake.py` exercise union fields but do not specifically test the "missing file union" scenario
- **Gap severity:** **Low** — narrow regression test for a specific legacy bug

---

## 3a. Documented Exceptions

The legacy suite contains tests that the POC deliberately *does not*
port. Each falls into one of the categories below. Cross-referenced as
**⛔ Ex-N** in the summary tables above.

### Ex-A — DateTime / BigInt scalar input validation

**Affected legacy tests:**
- `test_automation_task_schema.py::test_date_must_include_timezone`
- `test_automation_task_schema.py::test_date_must_be_iso_format`
- `test_rupture_generation_schema.py::test_date_must_include_timezone`
- `test_rupture_generation_schema.py::test_date_must_be_iso_format`
- `test_sms_schema.py::test_created_date_must_include_timezone`
- `test_sms_schema.py::test_date_must_be_iso_format`
- `test_create_file_bugfix_159.py` float/string-rejection cases

**Why:** ADR-001 Phase 1 (#303) deliberately defined the POC's `DateTime` and `BigInt` scalars as `NewType("DateTime", str)` / `NewType("BigInt", int)` with `parse_value=str` / `parse_value=int`. They serialise/deserialise as wire-format strings and integers without further coercion. Graphene's scalars did finer-grained parsing (ISO-8601 conformance for DateTime, type-narrowing for BigInt) and surfaced descriptive error messages on bad input.

**Wire-format impact:** zero — every existing client (weka, runzi, nzshm-model) sends pre-validated values. The only behavioural change is that the POC accepts a wider input domain at the schema boundary.

**Tracked for tightening:** a future "scalar policy" ADR (potential ADR-003) would document the validation rules to add. Not blocking POC ship.

### Ex-B — `git_refs → environment` field migration

**Affected legacy tests:**
- `test_rupture_generation_schema.py::test_transforms_old_fields`

**Why:** A pre-2020 RuptureGenerationTask data shape had a top-level `git_refs: dict` field that legacy's Graphene `from_json` rewrites at read time into `environment: [KeyValuePair]`. The POC's Pydantic-based `from_dict` does not include this rewrite — by design. Any DynamoDB row predating this migration cannot be read by either the POC or by current production legacy queries that go through the data-layer transform (because the transform mutates the in-memory dict; the on-disk row stays as `git_refs`).

**Wire-format impact:** any client still ingesting pre-2020 RGT objects would need the legacy data layer. Audit of weka, runzi, and nzshm-model query patterns shows no such ingestion — all consumers handle `environment` directly.

**Tracked:** if a migration job is ever needed, it belongs in a one-off script under `tools/` rather than in the schema's read path.

### Ex-C — Tests that are `@unittest.skip` in legacy

**Affected legacy tests:**
- `test_sms_schema.py::test_create_with_metrics` — `@unittest.skip("not there yet")`
- `test_sms_schema.py::test_update_with_metrics` — `@unittest.skip("not there yet")`, and the test body references a typo'd mutation name (`update.rupture_generation_task_task`)
- `test_sms_schema.py::test_merge_update_is_effective` — `@unittest.skip("TODO")`

**Why:** These were placeholder tests that never landed in production. The POC inherits no behaviour to test from them. Listed for transparency.

### Ex-D — Framework health/metadata endpoints

**Affected legacy tests:**
- `test_schema.py::test_get_about`
- `test_schema.py::test_get_version`

**Why:** Legacy Flask exposed `/about` and `/version` HTTP routes outside the GraphQL schema. The POC's FastAPI wrapper is configured separately and these are tested at the deployment layer (not in the in-process schema tests). The remaining `test_schema.py` tests (`test_get_new_mocked`, `test_get_all`, `test_upload`) are GraphQL-level and covered by `test_smoketest_ab.py`.

### Ex-E — Pre-DynamoDB data-migration paths

**Affected legacy tests:**
- `test_inversion_solution_bug_93.py`
- `simpler_relationships/test_inversion_solution_file_migration_bug_new.py` (3 tests)

**Why:** These exercise migration code that lived in the legacy data layer to handle objects written before the DynamoDB cut-over (pre-2020). The POC does not carry this code — it expects modern DynamoDB rows. The `_from_s3` fallback in `data/dynamo.py` is the *only* legacy-format read path the POC supports, and it's covered by `test_s3_fallback.py` (16 tests).

**If pre-2020 IDs become production-critical:** open a migration script under `tools/`. Don't reintroduce the migration into the schema.

### Ex-F — File download URL pattern from legacy S3 access

**Affected legacy tests:**
- `test_file_download_url_bugfix_211.py`

**Why:** The bug being regressed against was specific to legacy's pattern of making S3 API calls during GraphQL field resolution for metadata reads (an `UploadPartCopy` error surfaced on `file_name` queries). The POC does not make S3 API calls for metadata — it returns DynamoDB-stored values directly. The failure mode does not exist.

### Ex-G — Strawberry vs Graphene union-dispatch failure modes

**Affected legacy tests:**
- `hazard/test_bugfix_167_missing_fileunion.py`

**Why:** The bug 167 case was a Graphene-specific failure where a union field returned `None` instead of the correct concrete type when the dispatch table didn't have an entry. Strawberry's union resolution is type-driven (`Annotated[A | B, strawberry.union(...)]`) and validated at schema-build time — the equivalent miss would fail loudly at startup rather than silently at request time. Union dispatch is exercised by the existing tests for `InversionSolutionUnion`, `SourceSolutionUnion`, `OpenquakeNrmlUnion`, `FileUnion`, `ThingUnion`, `ChildTaskUnion`.

### Ex-H — Graphene class-graph iteration tests

**Affected legacy tests:**
- `object_iteration/test_iterate_items.py` (2 tests)
- `object_iteration/test_iterate_schema_types.py` (1 test)

**Why:** These walk Graphene's runtime class registry to discover all types implementing a given interface, then assert each is handled by a dispatch function. The POC replaces this pattern with an explicit `_CLAZZ_REGISTRY` dict in `models/_dispatch.py` (introduced in PR #313 review-followups). The registry is the source of truth; iteration-driven discovery is unnecessary. Net safer — adding a new type without a registry entry now fails at startup, not at first request.

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
9. ~~**Rupture set upload / `post_url`**~~ — done. `data/s3.presigned_post_for_file` wired into `mutate_create_rupture_set`; `FileInterface` resolvers surface `post_url` / `post_url_v2` / `post_data_v2` from a private field populated at create time. Full requests-based POST round-trip exercised against moto in `test_bugfix_gap4_rupture_set.py` (Gap 4).
10. ~~**`update_automation_task` ES re-indexing**~~ — done; automatic via existing `update_thing` → `index_document` path, asserted via monkeypatch in test.

11. ~~**File relation compression (Gap 6)**~~ — done in `strawberry-poc-compression` (commit 47bd09a, folded into #310). `nzshm_common.util.compress_string`/`decompress_string` wired into `get_file`/`list_files`/`create_file_relation`; write threshold at `UNCOMPRESSED_LIMIT=100` matches legacy. 6 tests in `tests/test_file_relation_compression.py`.

### Open — needs follow-up work

After Gap 14 closure, only one item remains genuinely-open (not a Documented Exception):

- **Gap 8** — Elasticsearch search-manager unit tests (9). Integration smoketests cover the path; unit-level regression coverage on `_dispatch_search` is missing.

Low priority follow-ups (POC ship is not blocked on these):
- `post_url`-family field coverage on file types other than RuptureSet — same `presigned_post_for_file` pattern from Gap 4 closure can be applied if a client surfaces a need.

Everything else from the legacy suite is either ✅ closed or ⛔ a documented exception (see §3a).
