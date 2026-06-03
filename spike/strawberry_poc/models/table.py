"""Table — relay.Node for ToshiTableObject records."""

from typing import Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from data.dynamo import get_table
from data.models import TableData

from .common import KeyValueListPair, KeyValuePair, TableType


@strawberry.type
class Table(relay.Node):
    pk: relay.NodeID[str]
    object_id: strawberry.ID | None = None
    name: str | None = None
    created: str | None = None
    column_headers: list[str] | None = None
    column_types: list[str] | None = None
    rows: list[list[str]] | None = None
    meta: list[KeyValuePair] | None = None
    table_type: TableType | None = None
    dimensions: list[KeyValueListPair] | None = None

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["Table"]:
        data = get_table(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "Table":
        d = TableData.model_validate(data)
        try:
            table_type = TableType(d.table_type) if d.table_type else None
        except ValueError:
            table_type = None
        return cls(
            pk=d.object_id,
            object_id=strawberry.ID(d.object_id),
            name=d.name,
            created=d.created,
            column_headers=d.column_headers,
            column_types=d.column_types,
            rows=d.rows,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            table_type=table_type,
            dimensions=[KeyValueListPair(k=i.k, v=i.v) for i in d.dimensions] if d.dimensions else None,
        )
