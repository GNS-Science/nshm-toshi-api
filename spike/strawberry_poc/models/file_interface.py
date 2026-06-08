"""FileInterface — matches legacy graphql_api.schema.file.FileInterface."""

import strawberry
from strawberry.types import Info

from data.s3 import presigned_download_url

from .common import BigInt, DateTime, JSONString, KeyValuePair


@strawberry.interface
class FileInterface:
    """Common fields shared by all file types (File, RuptureSet, InversionSolution, etc.)."""

    file_name: str | None = None
    md5_digest: str | None = None
    file_size: BigInt | None = None
    created: DateTime | None = None
    meta: list[KeyValuePair] | None = None

    @strawberry.field
    def file_url(self, info: Info) -> str | None:
        return presigned_download_url(self.pk, self.file_name)  # type: ignore[attr-defined]

    @strawberry.field
    def post_url(self) -> str | None:
        return None

    @strawberry.field
    def post_url_v2(self) -> str | None:
        return None

    @strawberry.field
    def post_data_v2(self) -> JSONString | None:
        return None
