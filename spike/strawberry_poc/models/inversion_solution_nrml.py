"""InversionSolutionNrml — file type used as an Openquake source model."""

from collections.abc import Iterable
from typing import Optional

import strawberry
from strawberry import relay
from strawberry.relay import GlobalID
from strawberry.types import Info

from data.dynamo import create_file, get_file, list_files
from data.models import InversionSolutionNrmlData

from .common import KeyValuePair, KeyValuePairInput
from .file_interface import FileInterface
from .inversion_solution import Predecessor, PredecessorInput
from .scaled_inversion_solution import SourceSolutionUnion, dispatch_source_solution


@strawberry.type
class InversionSolutionNrml(relay.Node, FileInterface):
    pk: relay.NodeID[str]

    source_solution_raw_id: strawberry.Private[str | None] = None
    predecessors_raw: strawberry.Private[list | None] = None

    @strawberry.field
    def source_solution(self, info: Info) -> SourceSolutionUnion | None:
        if not self.source_solution_raw_id:
            return None
        try:
            raw_id = GlobalID.from_id(self.source_solution_raw_id).node_id
        except Exception:
            raw_id = self.source_solution_raw_id
        data = get_file(info.context["dynamodb"], raw_id)
        return dispatch_source_solution(data) if data else None

    @strawberry.field
    def predecessors(self) -> list[Predecessor] | None:
        if not self.predecessors_raw:
            return None
        return [Predecessor(id=p["id"], depth=p["depth"]) for p in self.predecessors_raw]

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["InversionSolutionNrml"]:
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "InversionSolutionNrml":
        d = InversionSolutionNrmlData.model_validate(data)
        return cls(
            pk=d.object_id,
            file_name=d.file_name,
            md5_digest=d.md5_digest,
            file_size=d.file_size,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            created=d.created,
            source_solution_raw_id=d.source_solution,
            predecessors_raw=[p.model_dump() for p in d.predecessors] if d.predecessors else None,
        )


@strawberry.input
class CreateInversionSolutionNrmlInput:
    file_name: str
    source_solution: strawberry.ID | None = None
    md5_digest: str | None = None
    file_size: int | None = None
    meta: list[KeyValuePairInput] | None = None
    created: str | None = None
    predecessors: list[PredecessorInput] | None = None


def resolve_inversion_solution_nrmls(info: Info) -> Iterable[InversionSolutionNrml]:
    items = list_files(info.context["dynamodb"], "InversionSolutionNrml")
    return [InversionSolutionNrml.from_dict(item) for item in items]


def mutate_create_inversion_solution_nrml(info: Info, input: CreateInversionSolutionNrmlInput) -> InversionSolutionNrml:
    meta = [{"k": i.k, "v": i.v} for i in input.meta] if input.meta else None
    predecessors = [{"id": str(p.id), "depth": p.depth} for p in input.predecessors] if input.predecessors else None
    payload = {
        "file_name": input.file_name,
        "md5_digest": input.md5_digest,
        "file_size": input.file_size,
        "meta": meta,
        "created": input.created,
        "source_solution": str(input.source_solution) if input.source_solution else None,
        "predecessors": predecessors,
    }
    data = create_file(info.context["dynamodb"], "InversionSolutionNrml", payload)
    return InversionSolutionNrml.from_dict(data)
