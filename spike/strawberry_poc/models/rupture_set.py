"""
RuptureSet — file type with a produced_by relation.

This is the union-type stress test: produced_by can be a RuptureGenerationTask
(or other automation task types in future). In Strawberry, unions are explicit
annotated types — much cleaner than Graphene's dynamic dispatch.

POC simplification: only RuptureGenerationTask stub is included.
A full migration would add the other AutomationTask subtypes.
"""
from typing import Annotated, Iterable, Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from .common import KeyValuePair, KeyValuePairInput


# ── Stub for produced_by union type ───────────────────────────────────────────
# In the full migration this would be a proper relay.Node type with its own resolvers.

@strawberry.type
class RuptureGenerationTask(relay.Node):
    """Stub: the task that produced a RuptureSet."""

    pk: relay.NodeID[str]
    state: Optional[str] = None
    result: Optional[str] = None
    created: Optional[str] = None

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["RuptureGenerationTask"]:
        from data.dynamo import get_thing
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "RuptureGenerationTask":
        return cls(
            pk=data["object_id"],
            state=data.get("state"),
            result=data.get("result"),
            created=data.get("created"),
        )


# Union type for produced_by — strawberry.union is explicit and type-safe.
# Feasibility test: does is_type_of dispatch work cleanly?
AutomationTaskUnion = Annotated[
    RuptureGenerationTask,
    strawberry.union(name="AutomationTaskUnion"),
]


# ── RuptureSet ────────────────────────────────────────────────────────────────

@strawberry.type
class RuptureSet(relay.Node):
    """A RuptureSet file produced by a RuptureGenerationTask."""

    pk: relay.NodeID[str]
    file_name: Optional[str] = None
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    created: Optional[str] = None
    fault_models: Optional[list[str]] = None
    metrics: Optional[list[KeyValuePair]] = None
    # stored as raw object_id; resolved lazily (hidden from GraphQL schema)
    produced_by_raw_id: strawberry.Private[Optional[str]] = None

    @strawberry.field
    def produced_by(self, info: Info) -> Optional[RuptureGenerationTask]:
        if not self.produced_by_raw_id:
            return None
        from data.dynamo import get_thing
        from strawberry.relay import GlobalID
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
        from data.dynamo import get_file
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "RuptureSet":
        metrics = data.get("metrics")
        return cls(
            pk=data["object_id"],
            file_name=data.get("file_name"),
            md5_digest=data.get("md5_digest"),
            file_size=data.get("file_size"),
            created=data.get("created"),
            fault_models=data.get("fault_models"),
            metrics=[KeyValuePair(k=i["k"], v=i["v"]) for i in metrics] if metrics else None,
            produced_by_raw_id=data.get("produced_by"),
        )


@strawberry.input
class CreateRuptureSetInput:
    file_name: str
    produced_by: strawberry.ID
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    created: Optional[str] = None
    fault_models: Optional[list[str]] = None
    metrics: Optional[list[KeyValuePairInput]] = None


def resolve_rupture_sets(info: Info) -> Iterable[RuptureSet]:
    from data.dynamo import list_files
    items = list_files(info.context["dynamodb"], "RuptureSet")
    return [RuptureSet.from_dict(item) for item in items]


def mutate_create_rupture_set(info: Info, input: CreateRuptureSetInput) -> RuptureSet:
    from data.dynamo import create_file

    # Validate produced_by is a RuptureGenerationTask global ID
    gid = relay.GlobalID.from_id(input.produced_by)
    assert gid.type_name == "RuptureGenerationTask", (
        f"produced_by must be a RuptureGenerationTask, got {gid.type_name}"
    )

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
