"""
StrongMotionStation — Thing type with file relations.
"""
from typing import Iterable, Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from .common import SmsSiteClass, SmsSiteClassBasis
from .relations import FileRelation, build_file_relations_for_thing


@strawberry.type
class StrongMotionStation(relay.Node):
    """An NSHM Strong Motion Station record."""

    pk: relay.NodeID[str]
    site_code: Optional[str] = None
    site_class: Optional[SmsSiteClass] = None
    site_class_basis: Optional[SmsSiteClassBasis] = None
    Vs30_mean: Optional[list[float]] = None
    Vs30_std_dev: Optional[list[float]] = None
    liquefiable: Optional[bool] = None
    bedrock_encountered: Optional[bool] = None
    soft_clay_or_peat: Optional[bool] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    files_raw: strawberry.Private[Optional[list]] = None

    @relay.connection(relay.ListConnection[FileRelation])
    def files(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_thing(self.pk, self.files_raw or [])

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["StrongMotionStation"]:
        from data.dynamo import get_thing
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "StrongMotionStation":
        from data.models import StrongMotionStationData
        d = StrongMotionStationData.model_validate(data)
        return cls(
            pk=d.object_id,
            site_code=d.site_code,
            site_class=SmsSiteClass(d.site_class) if d.site_class else None,
            site_class_basis=SmsSiteClassBasis(d.site_class_basis) if d.site_class_basis else None,
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
    site_code: Optional[str] = None
    site_class: Optional[SmsSiteClass] = None
    site_class_basis: Optional[SmsSiteClassBasis] = None
    Vs30_mean: Optional[list[float]] = None
    Vs30_std_dev: Optional[list[float]] = None
    liquefiable: Optional[bool] = None
    bedrock_encountered: Optional[bool] = None
    soft_clay_or_peat: Optional[bool] = None
    created: Optional[str] = None
    updated: Optional[str] = None


def resolve_strong_motion_stations(info: Info) -> Iterable[StrongMotionStation]:
    from data.dynamo import list_things
    items = list_things(info.context["dynamodb"], "StrongMotionStation")
    return [StrongMotionStation.from_dict(item) for item in items]


def mutate_create_strong_motion_station(
    info: Info, input: CreateStrongMotionStationInput
) -> StrongMotionStation:
    from data.dynamo import create_thing
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
