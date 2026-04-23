"""
SmsFile — File type for Strong Motion Station data files.
"""
from typing import Iterable, Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from .common import SmsFileType
from .relations import FileRelation, build_file_relations_for_file


@strawberry.type
class SmsFile(relay.Node):
    """A file associated with a Strong Motion Station."""

    pk: relay.NodeID[str]
    file_name: Optional[str] = None
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[SmsFileType] = None
    created: Optional[str] = None

    relations_raw: strawberry.Private[Optional[list]] = None

    @relay.connection(relay.ListConnection[FileRelation])
    def relations(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_file(self.pk, self.relations_raw or [])

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["SmsFile"]:
        from data.dynamo import get_file
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "SmsFile":
        return cls(
            pk=data["object_id"],
            file_name=data.get("file_name"),
            md5_digest=data.get("md5_digest"),
            file_size=data.get("file_size"),
            file_type=SmsFileType(data["file_type"]) if data.get("file_type") else None,
            created=data.get("created"),
            relations_raw=data.get("relations", []),
        )


@strawberry.input
class CreateSmsFileInput:
    file_name: str
    file_type: SmsFileType
    md5_digest: Optional[str] = None
    file_size: Optional[int] = None
    created: Optional[str] = None


def resolve_sms_files(info: Info) -> Iterable[SmsFile]:
    from data.dynamo import list_files
    items = list_files(info.context["dynamodb"], "SmsFile")
    return [SmsFile.from_dict(item) for item in items]


def mutate_create_sms_file(info: Info, input: CreateSmsFileInput) -> SmsFile:
    from data.dynamo import create_file
    payload = {
        "file_name": input.file_name,
        "file_type": input.file_type.value,
        "md5_digest": input.md5_digest,
        "file_size": input.file_size,
        "created": input.created,
    }
    data = create_file(info.context["dynamodb"], "SmsFile", payload)
    return SmsFile.from_dict(data)
