"""
PageInfo + ListConnection with both Relay-spec camelCase (preferred) and
POC snake_case (deprecated aliases).

The POC schema runs with `auto_camel_case=False` to match the broader
snake_case convention of the legacy API. But the Relay Cursor
Connections Spec is normative camelCase for `PageInfo` — every client
that follows the spec (Apollo Client, urql, Relay 2) writes
`pageInfo { hasNextPage ... }`. Without these compat fields the POC
silently returns `null` for those queries.

See ADR-001 (Specific Decisions table, PageInfo row): both forms ship,
camelCase is preferred, snake_case is marked `@deprecated`. Sunset is
driven by usage logs once Phase 3 introspection instrumentation lands.
"""

import strawberry
from strawberry import relay
from strawberry.relay.types import NodeType  # noqa: F401 — re-used as our generic param


@strawberry.type(name="PageInfo")
class CompatPageInfo:
    """PageInfo with Relay-spec camelCase (preferred) + snake_case deprecated aliases.

    Replaces `strawberry.relay.PageInfo` on every connection that uses
    `CompatListConnection` (below).
    """

    # Modern, preferred — Relay Connection spec normative
    has_next_page: bool = strawberry.field(name="hasNextPage")
    has_previous_page: bool = strawberry.field(name="hasPreviousPage")
    start_cursor: str | None = strawberry.field(name="startCursor", default=None)
    end_cursor: str | None = strawberry.field(name="endCursor", default=None)

    # Legacy snake_case aliases — deprecated, kept for drop-in client compat
    @strawberry.field(
        name="has_next_page",
        deprecation_reason="Use hasNextPage instead (Relay Cursor Connections Spec normative).",
    )
    def deprecated_has_next_page(self) -> bool:
        return self.has_next_page

    @strawberry.field(
        name="has_previous_page",
        deprecation_reason="Use hasPreviousPage instead (Relay Cursor Connections Spec normative).",
    )
    def deprecated_has_previous_page(self) -> bool:
        return self.has_previous_page

    @strawberry.field(
        name="start_cursor",
        deprecation_reason="Use startCursor instead (Relay Cursor Connections Spec normative).",
    )
    def deprecated_start_cursor(self) -> str | None:
        return self.start_cursor

    @strawberry.field(
        name="end_cursor",
        deprecation_reason="Use endCursor instead (Relay Cursor Connections Spec normative).",
    )
    def deprecated_end_cursor(self) -> str | None:
        return self.end_cursor


@strawberry.type(name="Connection")
class CompatListConnection(relay.ListConnection[NodeType]):
    """ListConnection with Relay-spec camelCase pageInfo (preferred) + snake_case deprecated alias.

    Overrides the inherited `page_info: relay.PageInfo` field so the
    SDL name is `pageInfo` and the type is `CompatPageInfo` (the legacy
    snake_case `page_info` alias is added as a deprecated field below).

    `resolve_connection` is overridden to substitute the relay PageInfo
    instance with our CompatPageInfo so the subclass field annotation
    matches the runtime value Strawberry serialises.
    """

    page_info: CompatPageInfo = strawberry.field(
        name="pageInfo",
        description="Relay Cursor Connections Spec normative pagination info.",
    )

    @strawberry.field(
        name="page_info",
        deprecation_reason="Use pageInfo instead (Relay Cursor Connections Spec normative).",
    )
    def deprecated_page_info(self) -> CompatPageInfo:
        return self.page_info

    @classmethod
    def resolve_connection(cls, nodes, *, info, **kwargs):
        conn = super().resolve_connection(nodes, info=info, **kwargs)
        # super() returns a connection whose .page_info is a relay.PageInfo.
        # Replace it with our CompatPageInfo so the subclass field annotation
        # matches the actual instance type — otherwise Strawberry's serialiser
        # sees a relay.PageInfo where the schema expects CompatPageInfo.
        old_pi = conn.page_info
        conn.page_info = CompatPageInfo(
            has_next_page=old_pi.has_next_page,
            has_previous_page=old_pi.has_previous_page,
            start_cursor=old_pi.start_cursor,
            end_cursor=old_pi.end_cursor,
        )
        return conn
