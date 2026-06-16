"""
ToshiFile — base file type.

Equivalent to graphql_api/schema/file.py FileInterface + File.
In Strawberry there's no separate Interface class needed — relay.Node
acts as the node interface, and shared fields are just inherited.
"""

from collections.abc import Iterable
from typing import Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from graphql_api.data.dynamo import create_file, get_file, list_files
from graphql_api.data.models import ToshiFileData
from graphql_api.data.s3 import presigned_post_for_file

from graphql_api.models._infra.common import BigInt, DateTime, KeyValuePair, KeyValuePairInput, client_mutation_id_input_field
from graphql_api.models._interfaces.file_interface import FileInterface
from graphql_api.models._interfaces.predecessor import PredecessorInput
from graphql_api.models._interfaces.predecessors_interface import PredecessorsInterface
from graphql_api.models.relations import FileRelation, FileRelationsConnection, build_file_relations_for_file


@strawberry.type(name="File")
class ToshiFile(relay.Node, FileInterface, PredecessorsInterface):
    """A file stored in S3 and indexed in DynamoDB."""

    pk: relay.NodeID[str]

    relations_raw: strawberry.Private[list | None] = None
    predecessors_raw: strawberry.Private[list | None] = None

    @relay.connection(FileRelationsConnection)
    def relations(self, info: Info) -> list[FileRelation | None]:
        return build_file_relations_for_file(self.pk, self.relations_raw or [])

    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Info,
        **kwargs,
    ) -> Optional["ToshiFile"]:
        data = get_file(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "ToshiFile":
        d = ToshiFileData.model_validate(data)
        return cls(
            pk=d.object_id,
            file_name=d.file_name,
            md5_digest=d.md5_digest,
            file_size=d.file_size,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            created=d.created,
            relations_raw=d.relations,
            predecessors_raw=[p.model_dump() for p in d.predecessors] if d.predecessors else None,
        )


@strawberry.input
class CreateFileInput:
    file_name: str
    md5_digest: str | None = None
    file_size: BigInt | None = None
    meta: list[KeyValuePairInput | None] | None = None
    created: DateTime | None = None
    # Legacy parity: plain File accepts predecessors. Persisted on the
    # ToshiFileObject row alongside meta/relations.
    predecessors: list[PredecessorInput | None] | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()


def resolve_files(info: Info) -> Iterable[ToshiFile]:
    items = list_files(info.context["dynamodb"], "File")
    return [ToshiFile.from_dict(item) for item in items]


def mutate_create_file(info: Info, input: CreateFileInput) -> ToshiFile:
    meta = [{"k": i.k, "v": i.v} for i in input.meta] if input.meta else None
    predecessors = (
        [{"id": str(p.id), "depth": p.depth} for p in input.predecessors] if input.predecessors else None
    )
    payload = {
        "file_name": input.file_name,
        "md5_digest": input.md5_digest,
        "file_size": input.file_size,
        "meta": meta,
        "created": input.created,
        "predecessors": predecessors,
    }
    data = create_file(info.context["dynamodb"], "File", payload)
    instance = ToshiFile.from_dict(data)
    # Surface a presigned-POST so nshm-toshi-client / runzi can upload the
    # file bytes via the standard FileInterface handshake.
    instance.post_url_data = presigned_post_for_file(instance.pk, input.file_name, input.md5_digest)
    return instance
