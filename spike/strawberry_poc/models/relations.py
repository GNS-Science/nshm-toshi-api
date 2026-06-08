"""
FileRelation and TaskTaskRelation — virtual join types.

Neither is stored as a separate DynamoDB record. Both are assembled on-the-fly
from embedded arrays inside Thing / File objects:
  - Thing.files      → list of {"file_id": ..., "file_role": ...}
  - File.relations   → list of {"id": thing_id, "role": ...}
  - Thing.children   → list of {"child_id": ..., "child_clazz": ...}
  - Thing.parents    → list of {"parent_id": ..., "parent_clazz": ...}

strawberry.lazy is used to reference types defined in other modules without
causing circular imports at schema build time.
"""

from typing import Annotated

import strawberry
from strawberry import relay
from strawberry.relay import GlobalID
from strawberry.types import Info

from data.dynamo import create_file_relation, create_task_relation, get_file, get_thing

from .common import client_mutation_id_input_field, FileRole

# ── Lazy forward references (break circular deps) ─────────────────────────────

_ToshiFile = Annotated["ToshiFile", strawberry.lazy("models.file")]
_SmsFile = Annotated["SmsFile", strawberry.lazy("models.sms_file")]
_RuptureSet = Annotated["RuptureSet", strawberry.lazy("models.rupture_set")]
_InversionSolution = Annotated["InversionSolution", strawberry.lazy("models.inversion_solution")]
_ScaledInversionSolution = Annotated["ScaledInversionSolution", strawberry.lazy("models.scaled_inversion_solution")]
_AggregateInversionSolution = Annotated[
    "AggregateInversionSolution", strawberry.lazy("models.aggregate_inversion_solution")
]
_TimeDependentInversionSolution = Annotated[
    "TimeDependentInversionSolution", strawberry.lazy("models.time_dependent_inversion_solution")
]
_InversionSolutionNrml = Annotated["InversionSolutionNrml", strawberry.lazy("models.inversion_solution_nrml")]
_GeneralTask = Annotated["GeneralTask", strawberry.lazy("models.general_task")]
_RuptureGenerationTask = Annotated["RuptureGenerationTask", strawberry.lazy("models.automation_task")]
_AutomationTask = Annotated["AutomationTask", strawberry.lazy("models.automation_task")]
_StrongMotionStation = Annotated["StrongMotionStation", strawberry.lazy("models.strong_motion_station")]
_OpenquakeHazardTask = Annotated["OpenquakeHazardTask", strawberry.lazy("models.openquake_hazard_task")]
_OpenquakeHazardSolution = Annotated["OpenquakeHazardSolution", strawberry.lazy("models.openquake_hazard_solution")]
_OpenquakeHazardConfig = Annotated["OpenquakeHazardConfig", strawberry.lazy("models.openquake_hazard_config")]

# Union types — referenced as return types of @strawberry.field methods
FileUnion = Annotated[
    _ToshiFile
    | _SmsFile
    | _RuptureSet
    | _InversionSolution
    | _ScaledInversionSolution
    | _AggregateInversionSolution
    | _TimeDependentInversionSolution
    | _InversionSolutionNrml,
    strawberry.union(name="FileUnion"),
]

ThingUnion = Annotated[
    _GeneralTask
    | _RuptureGenerationTask
    | _AutomationTask
    | _StrongMotionStation
    | _OpenquakeHazardTask
    | _OpenquakeHazardSolution
    | _OpenquakeHazardConfig,
    strawberry.union(name="ThingUnion"),
]

ChildTaskUnion = Annotated[
    _GeneralTask
    | _RuptureGenerationTask
    | _AutomationTask
    | _StrongMotionStation
    | _OpenquakeHazardTask
    | _OpenquakeHazardSolution,
    strawberry.union(name="ChildTaskUnion"),
]


# ── InversionSolutionRelations ────────────────────────────────────────────────


@strawberry.type
class InversionSolutionRelations:
    """Return type for InversionSolutionInterface.relations; provides total_count."""

    edges: list["FileRelation"] = strawberry.field(default_factory=list)

    @strawberry.field
    def total_count(self) -> int:
        return len(self.edges)


# ── FileRelation ──────────────────────────────────────────────────────────────


@strawberry.type
class FileRelation:
    """
    Virtual type linking a File to a Thing.
    Assembled from the embedded arrays in both records (not a stored entity).
    """

    role: FileRole
    file_raw_id: strawberry.Private[str]
    thing_raw_id: strawberry.Private[str]

    @strawberry.field
    def file(self, info: Info) -> FileUnion | None:
        data = get_file(info.context["dynamodb"], self.file_raw_id)
        return _dispatch_file(data) if data else None

    @strawberry.field
    def thing(self, info: Info) -> ThingUnion | None:
        data = get_thing(info.context["dynamodb"], self.thing_raw_id)
        return _dispatch_thing(data) if data else None


# ── TaskTaskRelation ──────────────────────────────────────────────────────────


@strawberry.type
class TaskTaskRelation:
    """
    Virtual type linking a parent task to a child task.
    Assembled from the embedded children/parents arrays.
    """

    parent_raw_id: strawberry.Private[str]
    child_raw_id: strawberry.Private[str]
    child_clazz: strawberry.Private[str]

    @strawberry.field
    def parent(self, info: Info) -> _GeneralTask | None:
        from models.general_task import GeneralTask  # noqa: PLC0415

        data = get_thing(info.context["dynamodb"], self.parent_raw_id)
        return GeneralTask.from_dict(data) if data else None

    @strawberry.field
    def child(self, info: Info) -> ChildTaskUnion | None:
        data = get_thing(info.context["dynamodb"], self.child_raw_id)
        return _dispatch_thing(data) if data else None


# ── Connection types with total_count ────────────────────────────────────────
#
# Strawberry optimisation: when the query does not request `edges`, it skips
# building edges entirely (should_resolve_list_connection_edges → False).
# Overriding resolve_connection lets us count BEFORE that optimisation fires.


@strawberry.type
class FileRelationsConnection(relay.ListConnection[FileRelation]):
    """Relay connection for FileRelation that exposes total_count."""

    _total: strawberry.Private[int] = 0

    @strawberry.field
    def total_count(self) -> int:
        return self._total

    @classmethod
    def resolve_connection(cls, nodes, *, info, **kwargs):
        nodes_list = list(nodes)
        conn = super().resolve_connection(nodes_list, info=info, **kwargs)
        conn._total = len(nodes_list)
        return conn


@strawberry.type
class TaskRelationsConnection(relay.ListConnection[TaskTaskRelation]):
    """Relay connection for TaskTaskRelation that exposes total_count."""

    _total: strawberry.Private[int] = 0

    @strawberry.field
    def total_count(self) -> int:
        return self._total

    @classmethod
    def resolve_connection(cls, nodes, *, info, **kwargs):
        nodes_list = list(nodes)
        conn = super().resolve_connection(nodes_list, info=info, **kwargs)
        conn._total = len(nodes_list)
        return conn


# ── Dispatch helpers ──────────────────────────────────────────────────────────


def _dispatch_file(data: dict):
    """Instantiate the right Strawberry file type from a raw data dict."""
    clazz = data.get("clazz_name", "")
    if clazz == "SmsFile":
        from models.sms_file import SmsFile  # noqa: PLC0415

        return SmsFile.from_dict(data)
    if clazz == "RuptureSet":
        from models.rupture_set import RuptureSet  # noqa: PLC0415

        return RuptureSet.from_dict(data)
    if clazz == "InversionSolution":
        from models.inversion_solution import InversionSolution  # noqa: PLC0415

        return InversionSolution.from_dict(data)
    if clazz == "ScaledInversionSolution":
        from models.scaled_inversion_solution import ScaledInversionSolution  # noqa: PLC0415

        return ScaledInversionSolution.from_dict(data)
    if clazz == "AggregateInversionSolution":
        from models.aggregate_inversion_solution import AggregateInversionSolution  # noqa: PLC0415

        return AggregateInversionSolution.from_dict(data)
    if clazz == "TimeDependentInversionSolution":
        from models.time_dependent_inversion_solution import TimeDependentInversionSolution  # noqa: PLC0415

        return TimeDependentInversionSolution.from_dict(data)
    if clazz == "InversionSolutionNrml":
        from models.inversion_solution_nrml import InversionSolutionNrml  # noqa: PLC0415

        return InversionSolutionNrml.from_dict(data)
    from models.file import ToshiFile  # noqa: PLC0415

    return ToshiFile.from_dict(data)


def _dispatch_thing(data: dict):
    """Instantiate the right Strawberry thing type from a raw data dict."""
    clazz = data.get("clazz_name", "")
    if clazz == "RuptureGenerationTask":
        from models.automation_task import RuptureGenerationTask  # noqa: PLC0415

        return RuptureGenerationTask.from_dict(data)
    if clazz == "AutomationTask":
        from models.automation_task import AutomationTask  # noqa: PLC0415

        return AutomationTask.from_dict(data)
    if clazz == "StrongMotionStation":
        from models.strong_motion_station import StrongMotionStation  # noqa: PLC0415

        return StrongMotionStation.from_dict(data)
    if clazz == "OpenquakeHazardTask":
        from models.openquake_hazard_task import OpenquakeHazardTask  # noqa: PLC0415

        return OpenquakeHazardTask.from_dict(data)
    if clazz == "OpenquakeHazardSolution":
        from models.openquake_hazard_solution import OpenquakeHazardSolution  # noqa: PLC0415

        return OpenquakeHazardSolution.from_dict(data)
    if clazz == "OpenquakeHazardConfig":
        from models.openquake_hazard_config import OpenquakeHazardConfig  # noqa: PLC0415

        return OpenquakeHazardConfig.from_dict(data)
    from models.general_task import GeneralTask  # noqa: PLC0415

    return GeneralTask.from_dict(data)


# ── Input types for mutations ─────────────────────────────────────────────────


@strawberry.input
class CreateFileRelationInput:
    thing_id: strawberry.ID
    file_id: strawberry.ID
    role: FileRole
    client_mutation_id: str | None = client_mutation_id_input_field()


@strawberry.input
class CreateTaskRelationInput:
    parent_id: strawberry.ID
    child_id: strawberry.ID
    client_mutation_id: str | None = client_mutation_id_input_field()


# ── Builder helpers (called from Thing/File from_dict) ────────────────────────


def build_file_relations_for_thing(thing_raw_id: str, files_raw: list) -> list[FileRelation]:
    """Build FileRelation list from a Thing's embedded files array."""
    result = []
    for entry in files_raw or []:
        file_id = entry.get("file_id")
        if not file_id:
            continue
        try:
            role = FileRole(entry.get("file_role", "undefined"))
        except ValueError:
            role = FileRole.UNDEFINED
        result.append(FileRelation(role=role, file_raw_id=file_id, thing_raw_id=thing_raw_id))
    return result


def build_file_relations_for_file(file_raw_id: str, relations_raw: list) -> list[FileRelation]:
    """Build FileRelation list from a File's embedded relations array."""
    result = []
    for entry in relations_raw or []:
        thing_id = entry.get("id")
        if not thing_id:
            continue
        try:
            role = FileRole(entry.get("role", "undefined"))
        except ValueError:
            role = FileRole.UNDEFINED
        result.append(FileRelation(role=role, file_raw_id=file_raw_id, thing_raw_id=thing_id))
    return result


def build_task_children(parent_raw_id: str, children_raw: list) -> list[TaskTaskRelation]:
    return [
        TaskTaskRelation(
            parent_raw_id=parent_raw_id,
            child_raw_id=entry["child_id"],
            child_clazz=entry.get("child_clazz", ""),
        )
        for entry in (children_raw or [])
        if "child_id" in entry
    ]


def build_task_parents(child_raw_id: str, parents_raw: list) -> list[TaskTaskRelation]:
    return [
        TaskTaskRelation(
            parent_raw_id=entry["parent_id"],
            child_raw_id=child_raw_id,
            child_clazz="",
        )
        for entry in (parents_raw or [])
        if "parent_id" in entry
    ]


# ── Mutation resolvers ────────────────────────────────────────────────────────


def mutate_create_file_relation(info: Info, input: CreateFileRelationInput) -> bool:
    thing_gid = GlobalID.from_id(input.thing_id)
    file_gid = GlobalID.from_id(input.file_id)
    create_file_relation(
        info.context["dynamodb"],
        thing_id=thing_gid.node_id,
        file_id=file_gid.node_id,
        role=input.role.value,
    )
    return True


def mutate_create_task_relation(info: Info, input: CreateTaskRelationInput) -> TaskTaskRelation:
    parent_gid = GlobalID.from_id(input.parent_id)
    child_gid = GlobalID.from_id(input.child_id)
    parent_data = get_thing(info.context["dynamodb"], parent_gid.node_id)
    child_data = get_thing(info.context["dynamodb"], child_gid.node_id)
    parent_clazz = parent_data.get("clazz_name", "") if parent_data else ""
    child_clazz = child_data.get("clazz_name", "") if child_data else ""
    create_task_relation(
        info.context["dynamodb"],
        parent_id=parent_gid.node_id,
        parent_clazz=parent_clazz,
        child_id=child_gid.node_id,
        child_clazz=child_clazz,
    )
    return TaskTaskRelation(
        parent_raw_id=parent_gid.node_id,
        child_raw_id=child_gid.node_id,
        child_clazz=child_clazz,
    )
