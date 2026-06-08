"""
SmsFile — File type for Strong Motion Station data files.
"""

from collections.abc import Iterable
from typing import Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from data.dynamo import create_file, get_file, list_files
from data.models import SmsFileData

from .common import BigInt, client_mutation_id_input_field, KeyValuePair, SmsFileType, _try_enum
from .file_interface import FileInterface
from .relations import FileRelation, FileRelationsConnection, build_file_relations_for_file


@strawberry.type
class SmsFile(relay.Node, FileInterface):
    """A file associated with a Strong Motion Station."""

    pk: relay.NodeID[str]
    file_type: SmsFileType | None = None

    relations_raw: strawberry.Private[list | None] = None

    @relay.connection(FileRelationsConnection)
    def relations(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_file(self.pk, self.relations_raw or [])

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["SmsFile"]:
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "SmsFile":
        d = SmsFileData.model_validate(data)
        return cls(
            pk=d.object_id,
            file_name=d.file_name,
            md5_digest=d.md5_digest,
            file_size=d.file_size,
            file_type=_try_enum(SmsFileType, d.file_type),
            created=d.created,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            relations_raw=d.relations,
        )


@strawberry.input
class CreateSmsFileInput:
    file_name: str
    file_type: SmsFileType
    md5_digest: str | None = None
    file_size: BigInt | None = None
    created: str | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()


def resolve_sms_files(info: Info) -> Iterable[SmsFile]:
    items = list_files(info.context["dynamodb"], "SmsFile")
    return [SmsFile.from_dict(item) for item in items]


def mutate_create_sms_file(info: Info, input: CreateSmsFileInput) -> SmsFile:
    payload = {
        "file_name": input.file_name,
        "file_type": input.file_type.value,
        "md5_digest": input.md5_digest,
        "file_size": input.file_size,
        "created": input.created,
    }
    data = create_file(info.context["dynamodb"], "SmsFile", payload)
    return SmsFile.from_dict(data)
