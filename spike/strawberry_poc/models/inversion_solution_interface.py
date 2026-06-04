"""
InversionSolutionInterface — Strawberry interface for the IS family types.

Implements the legacy graphql_api InversionSolutionInterface, providing
mfd_table_id, hazard_table_id, mfd_table, tables, produced_by, relations,
created, file_name and all FileInterface fields on one abstract type.

All four concrete solution types implement this interface:
  InversionSolution, ScaledInversionSolution,
  AggregateInversionSolution, TimeDependentInversionSolution.

Note: this interface is standalone (does not inherit FileInterface) to keep
the Strawberry schema simple; concrete types implement both interfaces.
"""

from typing import Annotated

import strawberry
from strawberry.relay import GlobalID
from strawberry.types import Info

from data.dynamo import get_table, get_thing

from .common import BigInt, KeyValuePair, TableType
from .relations import InversionSolutionRelations, build_file_relations_for_file

# ── Lazy forward refs ─────────────────────────────────────────────────────────
# These types are defined in modules that import *this* module (circular),
# so strawberry.lazy is required to break the import cycle.

_AutomationTask = Annotated["AutomationTask", strawberry.lazy("models.automation_task")]
_RuptureGenerationTask = Annotated["RuptureGenerationTask", strawberry.lazy("models.automation_task")]
_LabelledTableRelation = Annotated["LabelledTableRelation", strawberry.lazy("models.inversion_solution")]
_Table = Annotated["Table", strawberry.lazy("models.table")]

# Registered once here; inversion_solution.py re-exports it via import.
AutomationTaskUnion = Annotated[
    _RuptureGenerationTask | _AutomationTask,
    strawberry.union(name="AutomationTaskUnion"),
]


def _dispatch_automation_task(data: dict):
    """Instantiate the correct task type from a raw thing dict."""
    from models.automation_task import AutomationTask, RuptureGenerationTask  # noqa: PLC0415

    clazz = data.get("clazz_name", "")
    if clazz == "RuptureGenerationTask":
        return RuptureGenerationTask.from_dict(data)
    return AutomationTask.from_dict(data)


# ── InversionSolutionInterface ────────────────────────────────────────────────


@strawberry.interface
class InversionSolutionInterface:
    """
    Shared interface for all InversionSolution family types.

    Declares all fields that weka queries via
      `... on InversionSolutionInterface { ... }`,
    including file fields (file_name, created, meta, …) and IS-specific fields
    (mfd_table_id, hazard_table_id, mfd_table, tables, produced_by, relations).

    Concrete types also implement FileInterface directly; the overlap is valid
    GraphQL (same field name, compatible types).
    """

    # ── FileInterface-overlapping fields ──────────────────────────────────────
    # Re-declared here so that `... on InversionSolutionInterface { file_name }`
    # is a valid GQL fragment selection.
    file_name: str | None = None
    md5_digest: str | None = None
    file_size: BigInt | None = None
    created: str | None = None
    meta: list[KeyValuePair] | None = None

    @strawberry.field
    def file_url(self) -> str | None:
        return None  # resolved by FileInterface on concrete types

    # ── IS-specific fields ────────────────────────────────────────────────────

    tables: list[_LabelledTableRelation] | None = None

    @strawberry.field
    def relations(self, info: Info) -> InversionSolutionRelations | None:
        pk = self.pk  # type: ignore[attr-defined]
        relations_raw = self.relations_raw  # type: ignore[attr-defined]
        if not relations_raw:
            return InversionSolutionRelations()
        return InversionSolutionRelations(edges=build_file_relations_for_file(pk, relations_raw))

    @strawberry.field
    def produced_by(self, info: Info) -> AutomationTaskUnion | None:
        raw_id = self.produced_by_raw_id  # type: ignore[attr-defined]
        if not raw_id:
            return None
        try:
            node_id = GlobalID.from_id(raw_id).node_id
        except Exception:
            node_id = raw_id
        data = get_thing(info.context["dynamodb"], node_id)
        return _dispatch_automation_task(data) if data else None

    @strawberry.field
    def mfd_table(self, info: Info) -> _Table | None:
        if not self.tables:
            return None
        for t in self.tables:  # type: ignore[union-attr]
            if t.table_type == TableType.MFD_CURVES_V2 and t.table_id:  # type: ignore[attr-defined]
                try:
                    raw_id = GlobalID.from_id(str(t.table_id)).node_id  # type: ignore[attr-defined]
                except Exception:
                    raw_id = str(t.table_id)  # type: ignore[attr-defined]
                data = get_table(info.context["dynamodb"], raw_id)
                if data:
                    from models.table import Table  # noqa: PLC0415

                    return Table.from_dict(data)
        return None

    @strawberry.field
    def mfd_table_id(self) -> str | None:
        if not self.tables:
            return None
        for t in self.tables:  # type: ignore[union-attr]
            if t.table_type == TableType.MFD_CURVES_V2:  # type: ignore[attr-defined]
                return str(t.table_id) if t.table_id else None  # type: ignore[attr-defined]
        return None

    @strawberry.field
    def hazard_table_id(self) -> str | None:
        if not self.tables:
            return None
        for t in self.tables:  # type: ignore[union-attr]
            if t.table_type in (TableType.HAZARD_GRIDDED, TableType.HAZARD_SITES):  # type: ignore[attr-defined]
                return str(t.table_id) if t.table_id else None  # type: ignore[attr-defined]
        return None
