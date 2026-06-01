"""
InversionSolution — file type with produced_by (AutomationTaskUnion),
embedded LabelledTableRelation list, and optional predecessors.

LabelledTableRelation is stored inline in the parent's JSON; it has no
separate DynamoDB record and is not a relay.Node.
"""
import uuid
from typing import Annotated, Iterable, Optional, Union

import strawberry
from strawberry import relay
from strawberry.types import Info

from .common import (
    AncestryLabel,
    KeyValuePair,
    KeyValuePairInput,
    KeyValueListPair,
    KeyValueListPairInput,
    TableType,
)

# ── Lazy forward refs for produced_by union ───────────────────────────────────

_RuptureGenerationTask = Annotated["RuptureGenerationTask", strawberry.lazy("models.automation_task")]
_AutomationTask = Annotated["AutomationTask", strawberry.lazy("models.automation_task")]

AutomationTaskUnion = Annotated[
    Union[_RuptureGenerationTask, _AutomationTask],
    strawberry.union(name="AutomationTaskUnion"),
]


# ── LabelledTableRelation (embedded — not a relay.Node) ───────────────────────

@strawberry.type
class LabelledTableRelation:
    """A labelled reference to a ToshiTableObject, stored inline in the parent."""
    identity: Optional[str] = None
    created: Optional[str] = None
    produced_by_id: Optional[strawberry.ID] = None
    label: Optional[str] = None
    table_id: Optional[strawberry.ID] = None
    table_type: Optional[TableType] = None
    dimensions: Optional[list[KeyValueListPair]] = None


@strawberry.input
class LabelledTableRelationInput:
    table_id: strawberry.ID
    table_type: TableType
    label: Optional[str] = None
    produced_by_id: Optional[strawberry.ID] = None
    dimensions: Optional[list[KeyValueListPairInput]] = None


def _ltr_from_dict(d: dict) -> LabelledTableRelation:
    dims = d.get("dimensions")
    try:
        tt = TableType(d["table_type"]) if d.get("table_type") else None
    except ValueError:
        tt = None
    return LabelledTableRelation(
        identity=d.get("identity"),
        created=d.get("created"),
        produced_by_id=d.get("produced_by_id"),
        label=d.get("label"),
        table_id=d.get("table_id"),
        table_type=tt,
        dimensions=[KeyValueListPair(k=x["k"], v=x["v"]) for x in dims] if dims else None,
    )


def _ltr_to_dict(inp: LabelledTableRelationInput) -> dict:
    dims = [{"k": d.k, "v": d.v} for d in inp.dimensions] if inp.dimensions else None
    return {
        "identity": str(uuid.uuid4()),
        "table_id": str(inp.table_id),
        "table_type": inp.table_type.value if inp.table_type else None,
        "label": inp.label,
        "produced_by_id": str(inp.produced_by_id) if inp.produced_by_id else None,
        "dimensions": dims,
    }


# ── Predecessor (embedded — not a relay.Node) ─────────────────────────────────

@strawberry.type
class Predecessor:
    """An ancestor in the provenance chain, stored inline in the parent."""
    id: strawberry.ID
    depth: int

    @strawberry.field
    def typename(self) -> Optional[str]:
        try:
            from strawberry.relay import GlobalID
            return GlobalID.from_id(self.id).type_name
        except Exception:
            return None

    @strawberry.field
    def relationship(self) -> Optional[str]:
        try:
            return AncestryLabel(self.depth).name.lower()
        except ValueError:
            return None


@strawberry.input
class PredecessorInput:
    id: strawberry.ID
    depth: int


# ── InversionSolution ──────────────────────────────────────────────────────────

@strawberry.type
class InversionSolution(relay.Node):
    """An Inversion Solution file produced by an automation task."""

    pk: relay.NodeID[str]
    file_name: Optional[str] = None
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    meta: Optional[list[KeyValuePair]] = None
    created: Optional[str] = None
    metrics: Optional[list[KeyValuePair]] = None
    tables: Optional[list[LabelledTableRelation]] = None

    produced_by_raw_id: strawberry.Private[Optional[str]] = None
    predecessors_raw: strawberry.Private[Optional[list]] = None

    @strawberry.field
    def produced_by(self, info: Info) -> Optional[AutomationTaskUnion]:
        if not self.produced_by_raw_id:
            return None
        from data.dynamo import get_thing
        from strawberry.relay import GlobalID
        try:
            raw_id = GlobalID.from_id(self.produced_by_raw_id).node_id
        except Exception:
            raw_id = self.produced_by_raw_id
        data = get_thing(info.context["dynamodb"], raw_id)
        return _dispatch_automation_task(data) if data else None

    @strawberry.field
    def predecessors(self) -> Optional[list[Predecessor]]:
        if not self.predecessors_raw:
            return None
        return [Predecessor(id=p["id"], depth=p["depth"]) for p in self.predecessors_raw]

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["InversionSolution"]:
        from data.dynamo import get_file
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "InversionSolution":
        from data.models import InversionSolutionData
        d = InversionSolutionData.model_validate(data)
        return cls(
            pk=d.object_id,
            file_name=d.file_name,
            md5_digest=d.md5_digest,
            file_size=d.file_size,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            created=d.created,
            metrics=[KeyValuePair(k=i.k, v=i.v) for i in d.metrics] if d.metrics else None,
            tables=[_ltr_from_dict(t.model_dump()) for t in d.tables] if d.tables else None,
            produced_by_raw_id=d.produced_by,
            predecessors_raw=[p.model_dump() for p in d.predecessors] if d.predecessors else None,
        )


def _dispatch_automation_task(data: dict):
    clazz = data.get("clazz_name", "")
    if clazz == "RuptureGenerationTask":
        from models.automation_task import RuptureGenerationTask
        return RuptureGenerationTask.from_dict(data)
    else:
        from models.automation_task import AutomationTask
        return AutomationTask.from_dict(data)


# ── Input types ───────────────────────────────────────────────────────────────

@strawberry.input
class CreateInversionSolutionInput:
    file_name: str
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    meta: Optional[list[KeyValuePairInput]] = None
    created: Optional[str] = None
    produced_by: Optional[strawberry.ID] = None
    metrics: Optional[list[KeyValuePairInput]] = None
    tables: Optional[list[LabelledTableRelationInput]] = None
    predecessors: Optional[list[PredecessorInput]] = None


@strawberry.input
class AppendInversionSolutionTablesInput:
    id: strawberry.ID
    tables: list[LabelledTableRelationInput]


# ── Resolvers + mutations ─────────────────────────────────────────────────────

def resolve_inversion_solutions(info: Info) -> Iterable[InversionSolution]:
    from data.dynamo import list_files
    items = list_files(info.context["dynamodb"], "InversionSolution")
    return [InversionSolution.from_dict(item) for item in items]


def mutate_create_inversion_solution(info: Info, input: CreateInversionSolutionInput) -> InversionSolution:
    from data.dynamo import create_file
    meta = [{"k": i.k, "v": i.v} for i in input.meta] if input.meta else None
    metrics = [{"k": i.k, "v": i.v} for i in input.metrics] if input.metrics else None
    tables = [_ltr_to_dict(t) for t in input.tables] if input.tables else None
    predecessors = [{"id": str(p.id), "depth": p.depth} for p in input.predecessors] if input.predecessors else None
    payload = {
        "file_name": input.file_name,
        "md5_digest": input.md5_digest,
        "file_size": input.file_size,
        "meta": meta,
        "created": input.created,
        "produced_by": str(input.produced_by) if input.produced_by else None,
        "metrics": metrics,
        "tables": tables,
        "predecessors": predecessors,
    }
    data = create_file(info.context["dynamodb"], "InversionSolution", payload)
    return InversionSolution.from_dict(data)


def mutate_append_inversion_solution_tables(
    info: Info, input: AppendInversionSolutionTablesInput
) -> Optional[InversionSolution]:
    import json
    from data.dynamo import get_file, _file_table
    from strawberry.relay import GlobalID
    gid = GlobalID.from_id(input.id)
    existing = get_file(info.context["dynamodb"], gid.node_id)
    if existing is None:
        return None
    existing_tables = existing.get("tables") or []
    existing["tables"] = existing_tables + [_ltr_to_dict(t) for t in input.tables]
    _file_table(info.context["dynamodb"]).put_item(Item={
        "object_id": gid.node_id,
        "object_type": "InversionSolution",
        "object_content": json.dumps({k: v for k, v in existing.items() if k != "object_id"}),
    })
    return InversionSolution.from_dict(existing)
