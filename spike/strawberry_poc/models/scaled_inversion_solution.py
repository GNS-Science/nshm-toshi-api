"""ScaledInversionSolution — file type with a source_solution (SourceSolutionUnion)."""
from typing import Annotated, Iterable, Optional, Union

import strawberry
from strawberry import relay
from strawberry.types import Info

from .common import KeyValuePair, KeyValuePairInput
from .inversion_solution import Predecessor, PredecessorInput

# ── SourceSolutionUnion (lazy — defined once here, imported elsewhere) ────────

_InversionSolution = Annotated["InversionSolution", strawberry.lazy("models.inversion_solution")]
_ScaledInversionSolution = Annotated["ScaledInversionSolution", strawberry.lazy("models.scaled_inversion_solution")]
_AggregateInversionSolution = Annotated["AggregateInversionSolution", strawberry.lazy("models.aggregate_inversion_solution")]
_TimeDependentInversionSolution = Annotated["TimeDependentInversionSolution", strawberry.lazy("models.time_dependent_inversion_solution")]

SourceSolutionUnion = Annotated[
    Union[_InversionSolution, _ScaledInversionSolution, _AggregateInversionSolution, _TimeDependentInversionSolution],
    strawberry.union(name="SourceSolutionUnion"),
]


def dispatch_source_solution(data: dict):
    """Instantiate the correct Strawberry type from a raw file dict."""
    clazz = data.get("clazz_name", "")
    if clazz == "ScaledInversionSolution":
        return ScaledInversionSolution.from_dict(data)
    if clazz == "AggregateInversionSolution":
        from models.aggregate_inversion_solution import AggregateInversionSolution
        return AggregateInversionSolution.from_dict(data)
    if clazz == "TimeDependentInversionSolution":
        from models.time_dependent_inversion_solution import TimeDependentInversionSolution
        return TimeDependentInversionSolution.from_dict(data)
    from models.inversion_solution import InversionSolution
    return InversionSolution.from_dict(data)


# ── ScaledInversionSolution ───────────────────────────────────────────────────

@strawberry.type
class ScaledInversionSolution(relay.Node):
    pk: relay.NodeID[str]
    file_name: Optional[str] = None
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    meta: Optional[list[KeyValuePair]] = None
    created: Optional[str] = None
    metrics: Optional[list[KeyValuePair]] = None

    produced_by_raw_id: strawberry.Private[Optional[str]] = None
    source_solution_raw_id: strawberry.Private[Optional[str]] = None
    predecessors_raw: strawberry.Private[Optional[list]] = None

    @strawberry.field
    def source_solution(self, info: Info) -> Optional[SourceSolutionUnion]:
        if not self.source_solution_raw_id:
            return None
        from data.dynamo import get_file
        from strawberry.relay import GlobalID
        try:
            raw_id = GlobalID.from_id(self.source_solution_raw_id).node_id
        except Exception:
            raw_id = self.source_solution_raw_id
        data = get_file(info.context["dynamodb"], raw_id)
        return dispatch_source_solution(data) if data else None

    @strawberry.field
    def predecessors(self) -> Optional[list[Predecessor]]:
        if not self.predecessors_raw:
            return None
        return [Predecessor(id=p["id"], depth=p["depth"]) for p in self.predecessors_raw]

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["ScaledInversionSolution"]:
        from data.dynamo import get_file
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "ScaledInversionSolution":
        from data.models import ScaledInversionSolutionData
        d = ScaledInversionSolutionData.model_validate(data)
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
class CreateScaledInversionSolutionInput:
    file_name: str
    source_solution: strawberry.ID
    produced_by: Optional[strawberry.ID] = None
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    meta: Optional[list[KeyValuePairInput]] = None
    created: Optional[str] = None
    predecessors: Optional[list[PredecessorInput]] = None


def resolve_scaled_inversion_solutions(info: Info) -> Iterable[ScaledInversionSolution]:
    from data.dynamo import list_files
    items = list_files(info.context["dynamodb"], "ScaledInversionSolution")
    return [ScaledInversionSolution.from_dict(item) for item in items]


def mutate_create_scaled_inversion_solution(
    info: Info, input: CreateScaledInversionSolutionInput
) -> ScaledInversionSolution:
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
    data = create_file(info.context["dynamodb"], "ScaledInversionSolution", payload)
    return ScaledInversionSolution.from_dict(data)
