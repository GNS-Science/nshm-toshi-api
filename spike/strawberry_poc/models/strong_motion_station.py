"""
StrongMotionStation — Thing type with file relations.
"""

from collections.abc import Iterable
from typing import Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from data.dynamo import create_thing, get_thing, list_things
from data.models import StrongMotionStationData

from .common import client_mutation_id_input_field, SmsSiteClass, SmsSiteClassBasis, _try_enum
from .relations import FileRelation, FileRelationsConnection, build_file_relations_for_thing


@strawberry.type
class StrongMotionStation(relay.Node):
    """An NSHM Strong Motion Station record."""

    pk: relay.NodeID[str]
    site_code: str | None = None
    site_class: SmsSiteClass | None = None
    site_class_basis: SmsSiteClassBasis | None = None
    Vs30_mean: list[float] | None = None
    Vs30_std_dev: list[float] | None = None
    liquefiable: bool | None = None
    bedrock_encountered: bool | None = None
    soft_clay_or_peat: bool | None = None
    created: str | None = None
    updated: str | None = None

    files_raw: strawberry.Private[list | None] = None

    @relay.connection(FileRelationsConnection)
    def files(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_thing(self.pk, self.files_raw or [])

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["StrongMotionStation"]:
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "StrongMotionStation":
        d = StrongMotionStationData.model_validate(data)
        return cls(
            pk=d.object_id,
            site_code=d.site_code,
            site_class=_try_enum(SmsSiteClass, d.site_class),
            site_class_basis=_try_enum(SmsSiteClassBasis, d.site_class_basis),
            Vs30_mean=d.Vs30_mean,
            Vs30_std_dev=d.Vs30_std_dev,
            liquefiable=d.liquefiable,
            bedrock_encountered=d.bedrock_encountered,
            soft_clay_or_peat=d.soft_clay_or_peat,
            created=d.created,
            updated=d.updated,
            files_raw=d.files,
        )


@strawberry.input
class CreateStrongMotionStationInput:
    site_code: str | None = None
    site_class: SmsSiteClass | None = None
    site_class_basis: SmsSiteClassBasis | None = None
    Vs30_mean: list[float] | None = None
    Vs30_std_dev: list[float] | None = None
    liquefiable: bool | None = None
    bedrock_encountered: bool | None = None
    soft_clay_or_peat: bool | None = None
    created: str | None = None
    updated: str | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()


def resolve_strong_motion_stations(info: Info) -> Iterable[StrongMotionStation]:
    items = list_things(info.context["dynamodb"], "StrongMotionStation")
    return [StrongMotionStation.from_dict(item) for item in items]


def mutate_create_strong_motion_station(info: Info, input: CreateStrongMotionStationInput) -> StrongMotionStation:
    payload = {
        "site_code": input.site_code,
        "site_class": input.site_class.value if input.site_class else None,
        "site_class_basis": input.site_class_basis.value if input.site_class_basis else None,
        "Vs30_mean": input.Vs30_mean,
        "Vs30_std_dev": input.Vs30_std_dev,
        "liquefiable": input.liquefiable,
        "bedrock_encountered": input.bedrock_encountered,
        "soft_clay_or_peat": input.soft_clay_or_peat,
        "created": input.created,
        "updated": input.updated,
    }
    data = create_thing(info.context["dynamodb"], "StrongMotionStation", payload)
    return StrongMotionStation.from_dict(data)
