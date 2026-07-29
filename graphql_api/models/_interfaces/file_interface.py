"""FileInterface — matches legacy graphql_api.schema.file.FileInterface."""

import json

import strawberry
from strawberry import relay
from strawberry.types import Info

from graphql_api.data.s3 import presigned_download_url
from graphql_api.models._infra.common import BigInt, DateTime, JSONString, KeyValuePair
from graphql_api.models.relations import FileRelation, FileRelationsConnection, build_file_relations_for_file


@strawberry.interface
class FileInterface:
    """Common fields shared by all file types (File, RuptureSet, InversionSolution, etc.)."""

    file_name: str | None = None
    md5_digest: str | None = None
    file_size: BigInt | None = None
    created: DateTime | None = None
    meta: list[KeyValuePair | None] | None = None

    # Embedded [{"id": thing_id, "role": ...}] array off the ToshiFileObject row.
    # Decompressed upstream in data/dynamo.py, so always a plain list here.
    relations_raw: strawberry.Private[list | None] = None

    @relay.connection(FileRelationsConnection)
    def relations(self, info: Info) -> list[FileRelation | None]:
        """Things related to this data file.

        Legacy parity: this field belongs on FileInterface (see the pre-ADR-004
        Graphene `graphql_api/schema/file.py`), not on the concrete types. Clients
        spread `... on FileInterface { relations { total_count } }`; declaring it
        only on the concrete types fails validation and nulls the whole document.
        """
        return build_file_relations_for_file(self.pk, self.relations_raw or [])  # type: ignore[attr-defined]

    # Populated at create-time by mutate_create_<file_type> when S3 is configured.
    # Legacy semantics: presigned-POST is generated once and surfaced on the
    # immediate create mutation response. Subsequent reads see None — clients
    # are expected to refresh by re-running a "get upload URL" flow if needed.
    post_url_data: strawberry.Private[dict | None] = None

    @strawberry.field
    def file_url(self, info: Info) -> str | None:
        return presigned_download_url(self.pk, self.file_name)  # type: ignore[attr-defined]

    @strawberry.field
    def post_url(self) -> str | None:
        if not self.post_url_data:
            return None
        return json.dumps(self.post_url_data.get("fields"))

    @strawberry.field
    def post_url_v2(self) -> str | None:
        if not self.post_url_data:
            return None
        return self.post_url_data.get("url")

    @strawberry.field
    def post_data_v2(self) -> JSONString | None:
        if not self.post_url_data:
            return None
        return json.dumps(self.post_url_data.get("fields"))
