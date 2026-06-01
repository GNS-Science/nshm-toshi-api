"""TimeDependentInversionSolution — file type with a single InversionSolution source."""

from collections.abc import Iterable
from typing import Annotated, Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from .common import KeyValuePair, KeyValuePairInput
from .inversion_solution import Predecessor, PredecessorInput

_InversionSolution = Annotated["InversionSolution", strawberry.lazy("models.inversion_solution")]


@strawberry.type
class TimeDependentInversionSolution(relay.Node):
    pk: relay.NodeID[str]
    file_name: str | None = None
    md5_digest: str | None = None
    file_size: int | None = None
    meta: list[KeyValuePair] | None = None
    created: str | None = None
    metrics: list[KeyValuePair] | None = None

    produced_by_raw_id: strawberry.Private[str | None] = None
    source_solution_raw_id: strawberry.Private[str | None] = None
    predecessors_raw: strawberry.Private[list | None] = None

    @strawberry.field
    def source_solution(self, info: Info) -> _InversionSolution | None:
        if not self.source_solution_raw_id:
            return None
        from strawberry.relay import GlobalID

        from data.dynamo import get_file
        from models.inversion_solution import InversionSolution

        try:
            raw_id = GlobalID.from_id(self.source_solution_raw_id).node_id
        except Exception:
            raw_id = self.source_solution_raw_id
        data = get_file(info.context["dynamodb"], raw_id)
        return InversionSolution.from_dict(data) if data else None

    @strawberry.field
    def predecessors(self) -> list[Predecessor] | None:
        if not self.predecessors_raw:
            return None
        return [Predecessor(id=p["id"], depth=p["depth"]) for p in self.predecessors_raw]

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["TimeDependentInversionSolution"]:
        from data.dynamo import get_file

        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "TimeDependentInversionSolution":
        from data.models import TimeDependentInversionSolutionData

        d = TimeDependentInversionSolutionData.model_validate(data)
        return cls(
            pk=d.object_id,
            file_name=d.file_name,
            md5_digest=d.md5_digest,
            file_size=d.file_size,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            created=d.created,
            metrics=[KeyValuePair(k=i.k, v=i.v) for i in d.metrics] if d.metrics else None,
            produced_by_raw_id=d.produced_by,
            source_solution_raw_id=d.source_solution,
            predecessors_raw=[p.model_dump() for p in d.predecessors] if d.predecessors else None,
        )


@strawberry.input
class CreateTimeDependentInversionSolutionInput:
    file_name: str
    source_solution: strawberry.ID
    produced_by: strawberry.ID | None = None
    md5_digest: str | None = None
    file_size: int | None = None
    meta: list[KeyValuePairInput] | None = None
    created: str | None = None
    predecessors: list[PredecessorInput] | None = None


def resolve_time_dependent_inversion_solutions(info: Info) -> Iterable[TimeDependentInversionSolution]:
    from data.dynamo import list_files

    items = list_files(info.context["dynamodb"], "TimeDependentInversionSolution")
    return [TimeDependentInversionSolution.from_dict(item) for item in items]


def mutate_create_time_dependent_inversion_solution(
    info: Info, input: CreateTimeDependentInversionSolutionInput
) -> TimeDependentInversionSolution:
    from data.dynamo import create_file

    meta = [{"k": i.k, "v": i.v} for i in input.meta] if input.meta else None
    predecessors = [{"id": str(p.id), "depth": p.depth} for p in input.predecessors] if input.predecessors else None
    payload = {
        "file_name": input.file_name,
        "md5_digest": input.md5_digest,
        "file_size": input.file_size,
        "meta": meta,
        "created": input.created,
        "produced_by": str(input.produced_by) if input.produced_by else None,
        "source_solution": str(input.source_solution),
        "predecessors": predecessors,
    }
    data = create_file(info.context["dynamodb"], "TimeDependentInversionSolution", payload)
    return TimeDependentInversionSolution.from_dict(data)
