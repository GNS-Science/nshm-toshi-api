"""OpenquakeHazardSolution — Thing type produced by an OpenquakeHazardTask."""

from collections.abc import Iterable
from typing import Annotated, Optional

import strawberry
from strawberry import relay
from strawberry.relay import GlobalID
from strawberry.types import Info

from data.dynamo import create_thing, get_file, get_thing, list_things
from data.models import OpenquakeHazardSolutionData
from models.file import ToshiFile
from models.openquake_hazard_task import OpenquakeHazardTask

from .common import KeyValuePair, KeyValuePairInput, OpenquakeTaskType
from .inversion_solution import Predecessor, PredecessorInput

_OpenquakeHazardTask = Annotated["OpenquakeHazardTask", strawberry.lazy("models.openquake_hazard_task")]
_ToshiFile = Annotated["ToshiFile", strawberry.lazy("models.file")]


@strawberry.type
class OpenquakeHazardSolution(relay.Node):
    pk: relay.NodeID[str]
    created: str | None = None
    task_type: OpenquakeTaskType | None = None
    metrics: list[KeyValuePair] | None = None
    meta: list[KeyValuePair] | None = None

    produced_by_raw_id: strawberry.Private[str | None] = None
    csv_archive_raw_id: strawberry.Private[str | None] = None
    hdf5_archive_raw_id: strawberry.Private[str | None] = None
    task_args_raw_id: strawberry.Private[str | None] = None
    predecessors_raw: strawberry.Private[list | None] = None

    def _resolve_file(self, info: Info, raw_id: str | None):
        if not raw_id:
            return None
        try:
            node_id = GlobalID.from_id(raw_id).node_id
        except Exception:
            node_id = raw_id
        data = get_file(info.context["dynamodb"], node_id)
        return ToshiFile.from_dict(data) if data else None

    @strawberry.field
    def produced_by(self, info: Info) -> _OpenquakeHazardTask | None:
        if not self.produced_by_raw_id:
            return None
        try:
            raw_id = GlobalID.from_id(self.produced_by_raw_id).node_id
        except Exception:
            raw_id = self.produced_by_raw_id
        data = get_thing(info.context["dynamodb"], raw_id)
        return OpenquakeHazardTask.from_dict(data) if data else None

    @strawberry.field
    def csv_archive(self, info: Info) -> _ToshiFile | None:
        return self._resolve_file(info, self.csv_archive_raw_id)

    @strawberry.field
    def hdf5_archive(self, info: Info) -> _ToshiFile | None:
        return self._resolve_file(info, self.hdf5_archive_raw_id)

    @strawberry.field
    def task_args(self, info: Info) -> _ToshiFile | None:
        return self._resolve_file(info, self.task_args_raw_id)

    @strawberry.field
    def predecessors(self) -> list[Predecessor] | None:
        if not self.predecessors_raw:
            return None
        return [Predecessor(id=p["id"], depth=p["depth"]) for p in self.predecessors_raw]

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["OpenquakeHazardSolution"]:
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "OpenquakeHazardSolution":
        d = OpenquakeHazardSolutionData.model_validate(data)
        try:
            task_type = OpenquakeTaskType(d.task_type) if d.task_type else None
        except ValueError:
            task_type = None
        return cls(
            pk=d.object_id,
            created=d.created,
            task_type=task_type,
            metrics=[KeyValuePair(k=i.k, v=i.v) for i in d.metrics] if d.metrics else None,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            produced_by_raw_id=d.produced_by,
            csv_archive_raw_id=d.csv_archive,
            hdf5_archive_raw_id=d.hdf5_archive,
            task_args_raw_id=d.task_args,
            predecessors_raw=[p.model_dump() for p in d.predecessors] if d.predecessors else None,
        )


@strawberry.input
class CreateOpenquakeHazardSolutionInput:
    produced_by: strawberry.ID
    task_type: OpenquakeTaskType
    created: str | None = None
    csv_archive: strawberry.ID | None = None
    hdf5_archive: strawberry.ID | None = None
    task_args: strawberry.ID | None = None
    metrics: list[KeyValuePairInput] | None = None
    meta: list[KeyValuePairInput] | None = None
    predecessors: list[PredecessorInput] | None = None


def resolve_openquake_hazard_solutions(info: Info) -> Iterable[OpenquakeHazardSolution]:
    items = list_things(info.context["dynamodb"], "OpenquakeHazardSolution")
    return [OpenquakeHazardSolution.from_dict(item) for item in items]


def mutate_create_openquake_hazard_solution(
    info: Info, input: CreateOpenquakeHazardSolutionInput
) -> OpenquakeHazardSolution:
    metrics = [{"k": i.k, "v": i.v} for i in input.metrics] if input.metrics else None
    meta = [{"k": i.k, "v": i.v} for i in input.meta] if input.meta else None
    predecessors = [{"id": str(p.id), "depth": p.depth} for p in input.predecessors] if input.predecessors else None
    payload = {
        "created": input.created,
        "task_type": input.task_type.value,
        "produced_by": str(input.produced_by),
        "csv_archive": str(input.csv_archive) if input.csv_archive else None,
        "hdf5_archive": str(input.hdf5_archive) if input.hdf5_archive else None,
        "task_args": str(input.task_args) if input.task_args else None,
        "metrics": metrics,
        "meta": meta,
        "predecessors": predecessors,
    }
    data = create_thing(info.context["dynamodb"], "OpenquakeHazardSolution", payload)
    return OpenquakeHazardSolution.from_dict(data)
