"""
Pydantic data models representing the DynamoDB stored schema.

These are pure data/validation models — no Strawberry or GraphQL concerns.
Each class mirrors the JSON stored in the `object_content` column of its table.

Convention:
  - All fields are Optional with None defaults (DynamoDB data may be partial).
  - Relation arrays (files, parents, children, relations) are kept as list[dict]
    for compatibility with the existing build_* helpers in models/relations.py.
  - Enum fields are plain str — conversion to Strawberry enums happens in from_dict.
  - Nested KV pairs use typed sub-models (KVPairModel, KVListPairModel) to catch
    malformed entries early with a clear ValidationError.
"""

from pydantic import BaseModel

# ── Shared sub-models ─────────────────────────────────────────────────────────


class KVPairModel(BaseModel):
    k: str
    v: str


class KVListPairModel(BaseModel):
    k: str
    v: list[str]


# ── Thing types (ToshiThingObject) ────────────────────────────────────────────


class GeneralTaskData(BaseModel):
    object_id: str
    clazz_name: str | None = None
    title: str | None = None
    description: str | None = None
    agent_name: str | None = None
    created: str | None = None
    updated: str | None = None
    notes: str | None = None
    subtask_count: int | None = None
    subtask_type: str | None = None
    model_type: str | None = None
    argument_lists: list[KVListPairModel] | None = None
    meta: list[KVPairModel] | None = None
    files: list[dict] | None = None
    children: list[dict] | None = None
    parents: list[dict] | None = None


class AutomationTaskData(BaseModel):
    object_id: str
    clazz_name: str | None = None
    state: str | None = None
    result: str | None = None
    task_type: str | None = None
    model_type: str | None = None
    created: str | None = None
    duration: float | None = None
    arguments: list[KVPairModel] | None = None
    environment: list[KVPairModel] | None = None
    metrics: list[KVPairModel] | None = None
    files: list[dict] | None = None
    parents: list[dict] | None = None
    children: list[dict] | None = None


class StrongMotionStationData(BaseModel):
    object_id: str
    clazz_name: str | None = None
    site_code: str | None = None
    site_class: str | None = None
    site_class_basis: str | None = None
    Vs30_mean: list[float] | None = None
    Vs30_std_dev: list[float] | None = None
    liquefiable: bool | None = None
    bedrock_encountered: bool | None = None
    soft_clay_or_peat: bool | None = None
    created: str | None = None
    updated: str | None = None
    files: list[dict] | None = None


# ── File types (ToshiFileObject) ──────────────────────────────────────────────


class ToshiFileData(BaseModel):
    object_id: str
    clazz_name: str | None = None
    file_name: str | None = None
    md5_digest: str | None = None
    file_size: int | None = None
    meta: list[KVPairModel] | None = None
    created: str | None = None
    relations: list[dict] | None = None


class SmsFileData(ToshiFileData):
    file_type: str | None = None


class LabelledTableRelationEntry(BaseModel):
    identity: str | None = None
    created: str | None = None
    produced_by_id: str | None = None
    label: str | None = None
    table_id: str | None = None
    table_type: str | None = None
    dimensions: list[KVListPairModel] | None = None


class PredecessorEntry(BaseModel):
    id: str  # relay GlobalID string
    depth: int


class InversionSolutionData(ToshiFileData):
    metrics: list[KVPairModel] | None = None
    produced_by: str | None = None  # relay GlobalID
    tables: list[LabelledTableRelationEntry] | None = None
    predecessors: list[PredecessorEntry] | None = None


class RuptureSetData(ToshiFileData):
    fault_models: list[str] | None = None
    metrics: list[KVPairModel] | None = None
    produced_by: str | None = None  # relay GlobalID


class ScaledInversionSolutionData(ToshiFileData):
    metrics: list[KVPairModel] | None = None
    produced_by: str | None = None
    source_solution: str | None = None  # relay GlobalID
    predecessors: list[PredecessorEntry] | None = None


class AggregateInversionSolutionData(ToshiFileData):
    metrics: list[KVPairModel] | None = None
    produced_by: str | None = None
    common_rupture_set: str | None = None  # relay GlobalID
    source_solutions: list[str] | None = None  # list of relay GlobalIDs
    aggregation_fn: str | None = None
    predecessors: list[PredecessorEntry] | None = None


class TimeDependentInversionSolutionData(ToshiFileData):
    metrics: list[KVPairModel] | None = None
    produced_by: str | None = None
    source_solution: str | None = None  # relay GlobalID
    predecessors: list[PredecessorEntry] | None = None


class InversionSolutionNrmlData(ToshiFileData):
    source_solution: str | None = None  # relay GlobalID
    predecessors: list[PredecessorEntry] | None = None


# ── Thing types — Openquake ───────────────────────────────────────────────────


class OpenquakeHazardConfigData(BaseModel):
    object_id: str
    clazz_name: str | None = None
    created: str | None = None
    source_models: list[str] | None = None  # list of relay GlobalIDs
    template_archive: str | None = None  # relay GlobalID
    files: list[dict] | None = None
    parents: list[dict] | None = None
    children: list[dict] | None = None


class OpenquakeHazardSolutionData(BaseModel):
    object_id: str
    clazz_name: str | None = None
    created: str | None = None
    task_type: str | None = None
    produced_by: str | None = None  # relay GlobalID → OpenquakeHazardTask
    csv_archive: str | None = None  # relay GlobalID → File
    hdf5_archive: str | None = None  # relay GlobalID → File
    task_args: str | None = None  # relay GlobalID → File
    metrics: list[KVPairModel] | None = None
    meta: list[KVPairModel] | None = None
    predecessors: list[PredecessorEntry] | None = None
    files: list[dict] | None = None
    parents: list[dict] | None = None
    children: list[dict] | None = None


class OpenquakeHazardTaskData(AutomationTaskData):
    hazard_solution: str | None = None  # relay GlobalID
    executor: str | None = None
    srm_logic_tree: str | None = None  # JSON string
    gmcm_logic_tree: str | None = None  # JSON string
    openquake_config: str | None = None  # JSON string


# ── Catch-all for unknown / future types ─────────────────────────────────────


class RawObjectData(BaseModel):
    """Fallback for any object type not yet modelled above."""

    object_id: str
    clazz_name: str | None = None

    model_config = {"extra": "allow"}
