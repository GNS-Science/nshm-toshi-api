"""
InversionSolution — file type with produced_by (AutomationTaskUnion),
embedded LabelledTableRelation list, and optional predecessors.

LabelledTableRelation is stored inline in the parent's JSON; it has no
separate DynamoDB record and is not a relay.Node.
"""

import json
import uuid
from collections.abc import Iterable
from typing import Optional

import strawberry
from strawberry import relay
from strawberry.relay import GlobalID
from strawberry.types import Info

from graphql_api.data.dynamo import _file_table, create_file, get_file, list_files
from graphql_api.data.models import InversionSolutionData
from graphql_api.data.s3 import presigned_post_for_file
from graphql_api.models._base.table import Table  # noqa: F401 — re-exported; also needed for mfd_table return type
from graphql_api.models._infra.common import (
    BigInt,
    DateTime,
    KeyValueListPair,
    KeyValueListPairInput,
    KeyValuePair,
    KeyValuePairInput,
    TableType,
    _try_enum,
    client_mutation_id_input_field,
)
from graphql_api.models._interfaces.file_interface import FileInterface
from graphql_api.models._interfaces.inversion_solution_interface import (  # noqa: F401 — re-export AutomationTaskUnion for other modules
    AutomationTaskUnion,
    InversionSolutionInterface,
    _dispatch_automation_task,
)
from graphql_api.models._interfaces.predecessor import (  # noqa: F401 — re-exported for other models
    Predecessor,
    PredecessorInput,
)
from graphql_api.models._interfaces.predecessors_interface import PredecessorsInterface

# ── LabelledTableRelation (embedded — not a relay.Node) ───────────────────────


@strawberry.type
class LabelledTableRelation:
    """A labelled reference to a ToshiTableObject, stored inline in the parent."""

    identity: str | None = None
    created: DateTime | None = None
    produced_by_id: strawberry.ID | None = None
    label: str | None = None
    table_id: strawberry.ID | None = None
    table_type: TableType | None = None
    dimensions: list[KeyValueListPair | None] | None = None

    @strawberry.field
    def table(self, info: Info) -> Optional["Table"]:
        """Resolved Table reference matching legacy SDL (chris's Problem 2 #4).

        Without this field, runzi queries that select `tables { table { id } }`
        on InversionSolution fail validation.
        """
        if not self.table_id:
            return None
        from graphql_api.data.dynamo import get_table  # noqa: PLC0415
        from graphql_api.models._base.table import Table  # noqa: PLC0415

        try:
            raw_id = GlobalID.from_id(str(self.table_id)).node_id
        except Exception:
            raw_id = str(self.table_id)
        data = get_table(info.context["dynamodb"], raw_id)
        return Table.from_dict(data) if data else None


@strawberry.input
class LabelledTableRelationInput:
    table_id: strawberry.ID
    table_type: TableType
    label: str | None = None
    produced_by_id: strawberry.ID | None = None
    dimensions: list[KeyValueListPairInput | None] | None = None


def _ltr_from_dict(d: dict) -> LabelledTableRelation:
    dims = d.get("dimensions")
    tt = _try_enum(TableType, d.get("table_type"))
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


# ── InversionSolution ──────────────────────────────────────────────────────────


@strawberry.type
class InversionSolution(relay.Node, FileInterface, InversionSolutionInterface, PredecessorsInterface):
    """An Inversion Solution file produced by an automation task."""

    pk: relay.NodeID[str]
    metrics: list[KeyValuePair | None] | None = None
    # tables, produced_by, mfd_table, mfd_table_id, hazard_table_id, relations
    # are all inherited from InversionSolutionInterface.

    produced_by_raw_id: strawberry.Private[str | None] = None
    relations_raw: strawberry.Private[list | None] = None
    predecessors_raw: strawberry.Private[list | None] = None

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["InversionSolution"]:
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "InversionSolution":
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
            relations_raw=d.relations,
            predecessors_raw=[p.model_dump() for p in d.predecessors] if d.predecessors else None,
        )


# ── Input types ───────────────────────────────────────────────────────────────


@strawberry.input
class CreateInversionSolutionInput:
    file_name: str
    md5_digest: str | None = None
    file_size: BigInt | None = None
    meta: list[KeyValuePairInput | None] | None = None
    created: DateTime | None = None
    # Legacy SDL preserves both deprecated table-id fields on input (chris's
    # Problem 2 #5). Runzi may still send `mfd_table_id`; accept it silently.
    # Transient fields — resolver may consume them but they're not persisted.
    mfd_table_id: strawberry.ID | None = None
    hazard_table_id: strawberry.ID | None = None
    produced_by: strawberry.ID | None = None
    metrics: list[KeyValuePairInput | None] | None = None
    tables: list[LabelledTableRelationInput | None] | None = None
    predecessors: list[PredecessorInput | None] | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()


@strawberry.input
class AppendInversionSolutionTablesInput:
    id: strawberry.ID
    tables: list[LabelledTableRelationInput | None]
    client_mutation_id: str | None = client_mutation_id_input_field()


# ── Resolvers + mutations ─────────────────────────────────────────────────────


def resolve_inversion_solutions(info: Info) -> Iterable[InversionSolution]:
    items = list_files(info.context["dynamodb"], "InversionSolution")
    return [InversionSolution.from_dict(item) for item in items]


def mutate_create_inversion_solution(info: Info, input: CreateInversionSolutionInput) -> InversionSolution:
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
    instance = InversionSolution.from_dict(data)
    # Surface a presigned-POST so nshm-toshi-client / runzi can upload the
    # file bytes via the standard FileInterface handshake.
    instance.post_url_data = presigned_post_for_file(instance.pk, input.file_name, input.md5_digest)
    return instance


def mutate_append_inversion_solution_tables(
    info: Info, input: AppendInversionSolutionTablesInput
) -> InversionSolution | None:
    gid = GlobalID.from_id(input.id)
    existing = get_file(info.context["dynamodb"], gid.node_id)
    if existing is None:
        return None
    existing_tables = existing.get("tables") or []
    existing["tables"] = existing_tables + [_ltr_to_dict(t) for t in input.tables]
    _file_table(info.context["dynamodb"]).put_item(
        Item={
            "object_id": gid.node_id,
            "object_type": "InversionSolution",
            "object_content": json.dumps({k: v for k, v in existing.items() if k != "object_id"}),
        }
    )
    return InversionSolution.from_dict(existing)
