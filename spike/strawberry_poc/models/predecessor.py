"""Predecessor — embedded provenance type (not a relay.Node)."""

import strawberry
from strawberry.relay import GlobalID

from .common import AncestryLabel


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
        try:
            return AncestryLabel(self.depth).name.lower()
        except ValueError:
            return None


@strawberry.input
class PredecessorInput:
    id: strawberry.ID
    depth: int
