"""FileInterface — matches legacy graphql_api.schema.file.FileInterface."""

import json

import strawberry
from strawberry.types import Info

from graphql_api.data.s3 import presigned_download_url

from graphql_api.models._infra.common import BigInt, DateTime, JSONString, KeyValuePair


@strawberry.interface
class FileInterface:
    """Common fields shared by all file types (File, RuptureSet, InversionSolution, etc.)."""

    file_name: str | None = None
    md5_digest: str | None = None
    file_size: BigInt | None = None
    created: DateTime | None = None
    meta: list[KeyValuePair | None] | None = None

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
