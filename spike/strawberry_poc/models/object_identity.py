"""ObjectIdentity — types for object_identities and legacy_object_identities queries."""

import base64

import strawberry
from strawberry.relay import GlobalID


@strawberry.type
class ObjectIdentity:
    object_type: str | None = None
    object_id: str | None = None
    clazz_name: str | None = None
    node_id: strawberry.ID | None = None


@strawberry.type
class ObjectIdentitiesEdge:
    node: ObjectIdentity | None = None
    cursor: str = ""


@strawberry.type
class ObjectIdentitiesPageInfo:
    has_next_page: bool = False
    end_cursor: str | None = None


@strawberry.type
class ObjectIdentitiesConnection:
    edges: list[ObjectIdentitiesEdge] = strawberry.field(default_factory=list)
    page_info: ObjectIdentitiesPageInfo = strawberry.field(default_factory=ObjectIdentitiesPageInfo)


def encode_cursor(object_id: str) -> str:
    return base64.b64encode(f"ObjectIdentitiesConnectionCursor:{object_id}".encode()).decode()


def decode_cursor(cursor: str) -> str | None:
    try:
        decoded = base64.b64decode(cursor.encode()).decode()
        _, _, node_id = decoded.partition(":")
        return node_id or None
    except Exception:
        return None


def make_object_identities_connection(
    items: list[dict],
    has_more: bool,
    last_id: str | None,
) -> ObjectIdentitiesConnection:
    edges = []
    for item in items:
        object_id = item.get("object_id", "")
        clazz = item.get("clazz_name") or item.get("object_type", "")
        node_id = strawberry.ID(str(GlobalID(type_name=clazz, node_id=object_id))) if clazz else None
        node = ObjectIdentity(
            object_type=clazz,
            object_id=object_id,
            clazz_name=item.get("clazz_name"),
            node_id=node_id,
        )
        edges.append(ObjectIdentitiesEdge(node=node, cursor=encode_cursor(object_id)))
    return ObjectIdentitiesConnection(
        edges=edges,
        page_info=ObjectIdentitiesPageInfo(
            has_next_page=has_more,
            end_cursor=encode_cursor(last_id) if last_id else None,
        ),
    )
