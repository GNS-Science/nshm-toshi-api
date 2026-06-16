"""PredecessorsInterface — matches legacy graphql_api.schema.custom.common.PredecessorsInterface."""

import strawberry

from graphql_api.models._interfaces.predecessor import Predecessor


@strawberry.interface
class PredecessorsInterface:
    """Shared by types that carry an inline provenance chain."""

    @strawberry.field
    def predecessors(self) -> list[Predecessor | None] | None:
        if not self.predecessors_raw:  # type: ignore[attr-defined]
            return None
        return [Predecessor(id=p["id"], depth=p["depth"]) for p in self.predecessors_raw]  # type: ignore[attr-defined]
