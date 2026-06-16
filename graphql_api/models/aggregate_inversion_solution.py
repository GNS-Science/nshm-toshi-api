"""AggregateInversionSolution — file type with multiple source solutions."""

from collections.abc import Iterable
from typing import Annotated, Optional

import strawberry
from strawberry import relay
from strawberry.relay import GlobalID
from strawberry.types import Info

from graphql_api.data.dynamo import create_file, get_file, list_files
from graphql_api.data.models import AggregateInversionSolutionData
from graphql_api.data.s3 import presigned_post_for_file
from graphql_api.models._infra.common import (
    AggregationFn,
    BigInt,
    DateTime,
    KeyValuePair,
    KeyValuePairInput,
    _try_enum,
    client_mutation_id_input_field,
)
from graphql_api.models._interfaces.file_interface import FileInterface
from graphql_api.models._interfaces.inversion_solution_interface import InversionSolutionInterface
from graphql_api.models._interfaces.predecessor import PredecessorInput
from graphql_api.models._interfaces.predecessors_interface import PredecessorsInterface
from graphql_api.models.inversion_solution import _ltr_from_dict
from graphql_api.models.rupture_set import RuptureSet
from graphql_api.models.scaled_inversion_solution import SourceSolutionUnion, dispatch_source_solution

_RuptureSet = Annotated["RuptureSet", strawberry.lazy("graphql_api.models.rupture_set")]


@strawberry.type
class AggregateInversionSolution(relay.Node, FileInterface, InversionSolutionInterface, PredecessorsInterface):
    pk: relay.NodeID[str]
    metrics: list[KeyValuePair | None] | None = None
    aggregation_fn: AggregationFn | None = None
    # tables, produced_by, mfd_table, mfd_table_id, hazard_table_id, relations
    # are all inherited from InversionSolutionInterface.

    produced_by_raw_id: strawberry.Private[str | None] = None
    common_rupture_set_raw_id: strawberry.Private[str | None] = None
    source_solutions_raw_ids: strawberry.Private[list[str | None] | None] = None
    relations_raw: strawberry.Private[list | None] = None
    predecessors_raw: strawberry.Private[list | None] = None

    @strawberry.field
    def common_rupture_set(self, info: Info) -> _RuptureSet | None:
        if not self.common_rupture_set_raw_id:
            return None
        try:
            raw_id = GlobalID.from_id(self.common_rupture_set_raw_id).node_id
        except Exception:
            raw_id = self.common_rupture_set_raw_id
        data = get_file(info.context["dynamodb"], raw_id)
        if data is None:
            return None
        return RuptureSet.from_dict(data)

    @strawberry.field
    def source_solutions(self, info: Info) -> list[SourceSolutionUnion | None] | None:
        if not self.source_solutions_raw_ids:
            return None
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

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["AggregateInversionSolution"]:
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "AggregateInversionSolution":
        d = AggregateInversionSolutionData.model_validate(data)
        agg_fn = _try_enum(AggregationFn, d.aggregation_fn)
        return cls(
            pk=d.object_id,
            file_name=d.file_name,
            md5_digest=d.md5_digest,
            file_size=d.file_size,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            created=d.created,
            metrics=[KeyValuePair(k=i.k, v=i.v) for i in d.metrics] if d.metrics else None,
            aggregation_fn=agg_fn,
            tables=[_ltr_from_dict(t.model_dump()) for t in d.tables] if d.tables else None,
            produced_by_raw_id=d.produced_by,
            common_rupture_set_raw_id=d.common_rupture_set,
            source_solutions_raw_ids=d.source_solutions,
            relations_raw=d.relations,
            predecessors_raw=[p.model_dump() for p in d.predecessors] if d.predecessors else None,
        )


@strawberry.input
class CreateAggregateInversionSolutionInput:
    file_name: str
    common_rupture_set: strawberry.ID
    source_solutions: list[strawberry.ID | None]
    aggregation_fn: AggregationFn
    produced_by: strawberry.ID | None = None
    md5_digest: str | None = None
    file_size: BigInt | None = None
    meta: list[KeyValuePairInput | None] | None = None
    created: DateTime | None = None
    predecessors: list[PredecessorInput | None] | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()


def resolve_aggregate_inversion_solutions(info: Info) -> Iterable[AggregateInversionSolution]:
    items = list_files(info.context["dynamodb"], "AggregateInversionSolution")
    return [AggregateInversionSolution.from_dict(item) for item in items]


def mutate_create_aggregate_inversion_solution(
    info: Info, input: CreateAggregateInversionSolutionInput
) -> AggregateInversionSolution:
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
    instance = AggregateInversionSolution.from_dict(data)
    # Surface a presigned-POST so nshm-toshi-client / runzi can upload the
    # file bytes via the standard FileInterface handshake.
    instance.post_url_data = presigned_post_for_file(instance.pk, input.file_name, input.md5_digest)
    return instance
