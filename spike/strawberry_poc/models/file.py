"""
ToshiFile — base file type.

Equivalent to graphql_api/schema/file.py FileInterface + File.
In Strawberry there's no separate Interface class needed — relay.Node
acts as the node interface, and shared fields are just inherited.
"""
from typing import Iterable, Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from .common import KeyValuePair, KeyValuePairInput
from .relations import FileRelation, build_file_relations_for_file


@strawberry.type
class ToshiFile(relay.Node):
    """A file stored in S3 and indexed in DynamoDB."""

    pk: relay.NodeID[str]
    file_name: Optional[str] = None
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    meta: Optional[list[KeyValuePair]] = None
    created: Optional[str] = None

    relations_raw: strawberry.Private[Optional[list]] = None

    @relay.connection(relay.ListConnection[FileRelation])
    def relations(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_file(self.pk, self.relations_raw or [])

    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Info,
        **kwargs,
    ) -> Optional["ToshiFile"]:
        from data.dynamo import get_file
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "ToshiFile":
        from data.models import ToshiFileData
        d = ToshiFileData.model_validate(data)
        return cls(
            pk=d.object_id,
            file_name=d.file_name,
            md5_digest=d.md5_digest,
            file_size=d.file_size,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            created=d.created,
            relations_raw=d.relations,
        )


@strawberry.input
class CreateFileInput:
    file_name: str
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    meta: Optional[list[KeyValuePairInput]] = None
    created: Optional[str] = None


def resolve_files(info: Info) -> Iterable[ToshiFile]:
    from data.dynamo import list_files
    items = list_files(info.context["dynamodb"], "File")
    return [ToshiFile.from_dict(item) for item in items]


def mutate_create_file(info: Info, input: CreateFileInput) -> ToshiFile:
    from data.dynamo import create_file
    meta = [{"k": i.k, "v": i.v} for i in input.meta] if input.meta else None
    payload = {
        "file_name": input.file_name,
        "md5_digest": input.md5_digest,
        "file_size": input.file_size,
        "meta": meta,
        "created": input.created,
    }
    data = create_file(info.context["dynamodb"], "File", payload)
    return ToshiFile.from_dict(data)
