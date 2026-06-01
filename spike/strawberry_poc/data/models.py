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
from typing import Any, Optional

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
    clazz_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    agent_name: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    notes: Optional[str] = None
    subtask_count: Optional[int] = None
    subtask_type: Optional[str] = None
    model_type: Optional[str] = None
    argument_lists: Optional[list[KVListPairModel]] = None
    meta: Optional[list[KVPairModel]] = None
    files: list[dict] = []
    children: list[dict] = []
    parents: list[dict] = []


class AutomationTaskData(BaseModel):
    object_id: str
    clazz_name: Optional[str] = None
    state: Optional[str] = None
    result: Optional[str] = None
    task_type: Optional[str] = None
    model_type: Optional[str] = None
    created: Optional[str] = None
    duration: Optional[float] = None
    arguments: Optional[list[KVPairModel]] = None
    environment: Optional[list[KVPairModel]] = None
    metrics: Optional[list[KVPairModel]] = None
    files: list[dict] = []
    parents: list[dict] = []
    children: list[dict] = []


class StrongMotionStationData(BaseModel):
    object_id: str
    clazz_name: Optional[str] = None
    site_code: Optional[str] = None
    site_class: Optional[str] = None
    site_class_basis: Optional[str] = None
    Vs30_mean: Optional[list[float]] = None
    Vs30_std_dev: Optional[list[float]] = None
    liquefiable: Optional[bool] = None
    bedrock_encountered: Optional[bool] = None
    soft_clay_or_peat: Optional[bool] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    files: list[dict] = []


# ── File types (ToshiFileObject) ──────────────────────────────────────────────

class ToshiFileData(BaseModel):
    object_id: str
    clazz_name: Optional[str] = None
    file_name: Optional[str] = None
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    meta: Optional[list[KVPairModel]] = None
    created: Optional[str] = None
    relations: list[dict] = []


class SmsFileData(ToshiFileData):
    file_type: Optional[str] = None


class LabelledTableRelationEntry(BaseModel):
    identity: Optional[str] = None
    created: Optional[str] = None
    produced_by_id: Optional[str] = None
    label: Optional[str] = None
    table_id: Optional[str] = None
    table_type: Optional[str] = None
    dimensions: Optional[list[KVListPairModel]] = None


class PredecessorEntry(BaseModel):
    id: str    # relay GlobalID string
    depth: int


class InversionSolutionData(ToshiFileData):
    metrics: Optional[list[KVPairModel]] = None
    produced_by: Optional[str] = None  # relay GlobalID
    tables: Optional[list[LabelledTableRelationEntry]] = None
    predecessors: Optional[list[PredecessorEntry]] = None


class RuptureSetData(ToshiFileData):
    fault_models: Optional[list[str]] = None
    metrics: Optional[list[KVPairModel]] = None
    produced_by: Optional[str] = None  # relay GlobalID


class ScaledInversionSolutionData(ToshiFileData):
    metrics: Optional[list[KVPairModel]] = None
    produced_by: Optional[str] = None
    source_solution: Optional[str] = None  # relay GlobalID
    predecessors: Optional[list[PredecessorEntry]] = None


class AggregateInversionSolutionData(ToshiFileData):
    metrics: Optional[list[KVPairModel]] = None
    produced_by: Optional[str] = None
    common_rupture_set: Optional[str] = None  # relay GlobalID
    source_solutions: Optional[list[str]] = None  # list of relay GlobalIDs
    aggregation_fn: Optional[str] = None
    predecessors: Optional[list[PredecessorEntry]] = None


class TimeDependentInversionSolutionData(ToshiFileData):
    metrics: Optional[list[KVPairModel]] = None
    produced_by: Optional[str] = None
    source_solution: Optional[str] = None  # relay GlobalID
    predecessors: Optional[list[PredecessorEntry]] = None


class InversionSolutionNrmlData(ToshiFileData):
    source_solution: Optional[str] = None  # relay GlobalID
    predecessors: Optional[list[PredecessorEntry]] = None


# ── Thing types — Openquake ───────────────────────────────────────────────────

class OpenquakeHazardConfigData(BaseModel):
    object_id: str
    clazz_name: Optional[str] = None
    created: Optional[str] = None
    source_models: Optional[list[str]] = None  # list of relay GlobalIDs
    template_archive: Optional[str] = None  # relay GlobalID
    files: list[dict] = []
    parents: list[dict] = []
    children: list[dict] = []


class OpenquakeHazardSolutionData(BaseModel):
    object_id: str
    clazz_name: Optional[str] = None
    created: Optional[str] = None
    task_type: Optional[str] = None
    produced_by: Optional[str] = None   # relay GlobalID → OpenquakeHazardTask
    csv_archive: Optional[str] = None   # relay GlobalID → File
    hdf5_archive: Optional[str] = None  # relay GlobalID → File
    task_args: Optional[str] = None     # relay GlobalID → File
    metrics: Optional[list[KVPairModel]] = None
    meta: Optional[list[KVPairModel]] = None
    predecessors: Optional[list[PredecessorEntry]] = None
    files: list[dict] = []
    parents: list[dict] = []
    children: list[dict] = []


class OpenquakeHazardTaskData(AutomationTaskData):
    hazard_solution: Optional[str] = None  # relay GlobalID
    executor: Optional[str] = None
    srm_logic_tree: Optional[str] = None   # JSON string
    gmcm_logic_tree: Optional[str] = None  # JSON string
    openquake_config: Optional[str] = None # JSON string


# ── Catch-all for unknown / future types ─────────────────────────────────────

class RawObjectData(BaseModel):
    """Fallback for any object type not yet modelled above."""
    object_id: str
    clazz_name: Optional[str] = None

    model_config = {"extra": "allow"}
