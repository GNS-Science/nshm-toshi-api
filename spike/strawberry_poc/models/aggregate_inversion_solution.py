"""AggregateInversionSolution — file type with multiple source solutions."""
from typing import Iterable, Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from typing import Annotated, Optional as _Opt
from .common import AggregationFn, KeyValuePair, KeyValuePairInput
from .inversion_solution import Predecessor, PredecessorInput
from .scaled_inversion_solution import SourceSolutionUnion, dispatch_source_solution

_RuptureSet = Annotated["RuptureSet", strawberry.lazy("models.rupture_set")]


@strawberry.type
class AggregateInversionSolution(relay.Node):
    pk: relay.NodeID[str]
    file_name: Optional[str] = None
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    meta: Optional[list[KeyValuePair]] = None
    created: Optional[str] = None
    metrics: Optional[list[KeyValuePair]] = None
    aggregation_fn: Optional[AggregationFn] = None

    produced_by_raw_id: strawberry.Private[Optional[str]] = None
    common_rupture_set_raw_id: strawberry.Private[Optional[str]] = None
    source_solutions_raw_ids: strawberry.Private[Optional[list[str]]] = None
    predecessors_raw: strawberry.Private[Optional[list]] = None

    @strawberry.field
    def common_rupture_set(self, info: Info) -> Optional[_RuptureSet]:
        if not self.common_rupture_set_raw_id:
            return None
        from data.dynamo import get_file
        from strawberry.relay import GlobalID
        try:
            raw_id = GlobalID.from_id(self.common_rupture_set_raw_id).node_id
        except Exception:
            raw_id = self.common_rupture_set_raw_id
        data = get_file(info.context["dynamodb"], raw_id)
        if data is None:
            return None
        from models.rupture_set import RuptureSet
        return RuptureSet.from_dict(data)

    @strawberry.field
    def source_solutions(self, info: Info) -> Optional[list[SourceSolutionUnion]]:
        if not self.source_solutions_raw_ids:
            return None
        from data.dynamo import get_file
        from strawberry.relay import GlobalID
        results = []
        for gid_str in self.source_solutions_raw_ids:
            try:
                raw_id = GlobalID.from_id(gid_str).node_id
            except Exception:
                raw_id = gid_str
            data = get_file(info.context["dynamodb"], raw_id)
            if data:
                results.append(dispatch_source_solution(data))
        return results or None

    @strawberry.field
    def predecessors(self) -> Optional[list[Predecessor]]:
        if not self.predecessors_raw:
            return None
        return [Predecessor(id=p["id"], depth=p["depth"]) for p in self.predecessors_raw]

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["AggregateInversionSolution"]:
        from data.dynamo import get_file
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "AggregateInversionSolution":
        from data.models import AggregateInversionSolutionData
        d = AggregateInversionSolutionData.model_validate(data)
        try:
            agg_fn = AggregationFn(d.aggregation_fn) if d.aggregation_fn else None
        except ValueError:
            agg_fn = None
        return cls(
            pk=d.object_id,
            file_name=d.file_name,
            md5_digest=d.md5_digest,
            file_size=d.file_size,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            created=d.created,
            metrics=[KeyValuePair(k=i.k, v=i.v) for i in d.metrics] if d.metrics else None,
            aggregation_fn=agg_fn,
            produced_by_raw_id=d.produced_by,
            common_rupture_set_raw_id=d.common_rupture_set,
            source_solutions_raw_ids=d.source_solutions,
            predecessors_raw=[p.model_dump() for p in d.predecessors] if d.predecessors else None,
        )


@strawberry.input
class CreateAggregateInversionSolutionInput:
    file_name: str
    common_rupture_set: strawberry.ID
    source_solutions: list[strawberry.ID]
    aggregation_fn: AggregationFn
    produced_by: Optional[strawberry.ID] = None
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    meta: Optional[list[KeyValuePairInput]] = None
    created: Optional[str] = None
    predecessors: Optional[list[PredecessorInput]] = None


def resolve_aggregate_inversion_solutions(info: Info) -> Iterable[AggregateInversionSolution]:
    from data.dynamo import list_files
    items = list_files(info.context["dynamodb"], "AggregateInversionSolution")
    return [AggregateInversionSolution.from_dict(item) for item in items]


def mutate_create_aggregate_inversion_solution(
    info: Info, input: CreateAggregateInversionSolutionInput
) -> AggregateInversionSolution:
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
        "common_rupture_set": str(input.common_rupture_set),
        "source_solutions": [str(s) for s in input.source_solutions],
        "aggregation_fn": input.aggregation_fn.value,
        "predecessors": predecessors,
    }
    data = create_file(info.context["dynamodb"], "AggregateInversionSolution", payload)
    return AggregateInversionSolution.from_dict(data)
