"""Predecessor — embedded provenance type (not a relay.Node)."""

from typing import Annotated

import strawberry
from strawberry.relay import GlobalID
from strawberry.types import Info

from .common import AncestryLabel

# Legacy PredecessorUnion = (File, InversionSolution, ScaledInversionSolution,
# AggregateInversionSolution, TimeDependentInversionSolution, InversionSolutionNrml).
# All file-like; reuse the lazy refs pattern from relations.py.
_File = Annotated["ToshiFile", strawberry.lazy("graphql_api.models.file")]
_InversionSolution = Annotated["InversionSolution", strawberry.lazy("graphql_api.models.inversion_solution")]
_ScaledInversionSolution = Annotated["ScaledInversionSolution", strawberry.lazy("graphql_api.models.scaled_inversion_solution")]
_AggregateInversionSolution = Annotated[
    "AggregateInversionSolution", strawberry.lazy("graphql_api.models.aggregate_inversion_solution")
]
_TimeDependentInversionSolution = Annotated[
    "TimeDependentInversionSolution", strawberry.lazy("graphql_api.models.time_dependent_inversion_solution")
]
_InversionSolutionNrml = Annotated["InversionSolutionNrml", strawberry.lazy("graphql_api.models.inversion_solution_nrml")]

PredecessorUnion = Annotated[
    _File
    | _InversionSolution
    | _ScaledInversionSolution
    | _AggregateInversionSolution
    | _TimeDependentInversionSolution
    | _InversionSolutionNrml,
    strawberry.union(name="PredecessorUnion"),
]


@strawberry.type
class Predecessor:
    """An ancestor in the provenance chain, stored inline in the parent."""

    id: strawberry.ID
    depth: int

    @strawberry.field
    def typename(self) -> str | None:
        try:
            return GlobalID.from_id(self.id).type_name
        except Exception:
            return None

    @strawberry.field
    def relationship(self) -> str | None:
        """Title-cased ancestry label. Matches legacy `.name.title()` output —
        e.g. depth=-1 → "Parent", not "parent". Clients (legacy + nshm) expect
        the Title Case form.
        """
        try:
            return AncestryLabel(self.depth).name.title()
        except ValueError:
            return None

    @strawberry.field
    def node(self, info: Info) -> PredecessorUnion | None:
        """Resolved node behind the predecessor id. Legacy SDL ships this on
        Predecessor; clients use it to selection-spread into the underlying
        file's fields without a separate node(id:) lookup.
        """
        from graphql_api.data.dynamo import get_file  # noqa: PLC0415

        try:
            raw_id = GlobalID.from_id(str(self.id)).node_id
        except Exception:
            raw_id = str(self.id)
        data = get_file(info.context["dynamodb"], raw_id)
        if not data:
            return None
        from ._dispatch import dispatch_file as _dispatch_file  # noqa: PLC0415

        return _dispatch_file(data)


@strawberry.input
class PredecessorInput:
    id: strawberry.ID
    depth: int
