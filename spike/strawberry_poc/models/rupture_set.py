"""
RuptureSet — file type with a produced_by relation.

This is the union-type stress test: produced_by can be a RuptureGenerationTask
(or other automation task types in future). In Strawberry, unions are explicit
annotated types — much cleaner than Graphene's dynamic dispatch.
"""

from collections.abc import Iterable
from typing import Optional

import strawberry
from strawberry import relay
from strawberry.relay import GlobalID
from strawberry.types import Info

from data.dynamo import create_file, get_file, get_thing, list_files
from data.models import RuptureSetData

from .automation_task import RuptureGenerationTask  # noqa: F401 — re-exported for schema.py
from .common import BigInt, KeyValuePair, KeyValuePairInput
from .file_interface import FileInterface

# ── RuptureSet ────────────────────────────────────────────────────────────────


@strawberry.type
class RuptureSet(relay.Node, FileInterface):
    """A RuptureSet file produced by a RuptureGenerationTask."""

    pk: relay.NodeID[str]
    fault_models: list[str] | None = None
    metrics: list[KeyValuePair] | None = None
    # stored as raw object_id; resolved lazily (hidden from GraphQL schema)
    produced_by_raw_id: strawberry.Private[str | None] = None

    @strawberry.field
    def produced_by(self, info: Info) -> RuptureGenerationTask | None:
        if not self.produced_by_raw_id:
            return None
        # produced_by is stored as a relay global ID string
        try:
            gid = GlobalID.from_id(self.produced_by_raw_id)
            raw_id = gid.node_id
        except Exception:
            raw_id = self.produced_by_raw_id
        data = get_thing(info.context["dynamodb"], raw_id)
        return RuptureGenerationTask.from_dict(data) if data else None

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["RuptureSet"]:
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "RuptureSet":
        d = RuptureSetData.model_validate(data)
        return cls(
            pk=d.object_id,
            file_name=d.file_name,
            md5_digest=d.md5_digest,
            file_size=d.file_size,
            created=d.created,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            fault_models=d.fault_models,
            metrics=[KeyValuePair(k=i.k, v=i.v) for i in d.metrics] if d.metrics else None,
            produced_by_raw_id=d.produced_by,
        )


@strawberry.input
class CreateRuptureSetInput:
    file_name: str
    produced_by: strawberry.ID
    md5_digest: str | None = None
    file_size: BigInt | None = None
    created: str | None = None
    fault_models: list[str] | None = None
    metrics: list[KeyValuePairInput] | None = None


def resolve_rupture_sets(info: Info) -> Iterable[RuptureSet]:
    items = list_files(info.context["dynamodb"], "RuptureSet")
    return [RuptureSet.from_dict(item) for item in items]


def mutate_create_rupture_set(info: Info, input: CreateRuptureSetInput) -> RuptureSet:
    # Validate produced_by is a RuptureGenerationTask global ID
    gid = relay.GlobalID.from_id(input.produced_by)
    assert gid.type_name == "RuptureGenerationTask", f"produced_by must be a RuptureGenerationTask, got {gid.type_name}"

    metrics = [{"k": i.k, "v": i.v} for i in input.metrics] if input.metrics else None
    payload = {
        "file_name": input.file_name,
        "produced_by": str(input.produced_by),
        "md5_digest": input.md5_digest,
        "file_size": input.file_size,
        "created": input.created,
        "fault_models": input.fault_models,
        "metrics": metrics,
    }
    data = create_file(info.context["dynamodb"], "RuptureSet", payload)
    return RuptureSet.from_dict(data)
