"""OpenquakeHazardConfig — Thing type holding source model references."""
from typing import Annotated, Iterable, Optional, Union

import strawberry
from strawberry import relay
from strawberry.types import Info

# ── OpenquakeNrmlUnion ────────────────────────────────────────────────────────

_ToshiFile = Annotated["ToshiFile", strawberry.lazy("models.file")]
_InversionSolutionNrml = Annotated["InversionSolutionNrml", strawberry.lazy("models.inversion_solution_nrml")]

OpenquakeNrmlUnion = Annotated[
    Union[_ToshiFile, _InversionSolutionNrml],
    strawberry.union(name="OpenquakeNrmlUnion"),
]


def dispatch_nrml(data: dict):
    clazz = data.get("clazz_name", "")
    if clazz == "InversionSolutionNrml":
        from models.inversion_solution_nrml import InversionSolutionNrml
        return InversionSolutionNrml.from_dict(data)
    from models.file import ToshiFile
    return ToshiFile.from_dict(data)


# ── OpenquakeHazardConfig ─────────────────────────────────────────────────────

@strawberry.type
class OpenquakeHazardConfig(relay.Node):
    pk: relay.NodeID[str]
    created: Optional[str] = None

    source_models_raw_ids: strawberry.Private[Optional[list[str]]] = None
    template_archive_raw_id: strawberry.Private[Optional[str]] = None

    @strawberry.field
    def source_models(self, info: Info) -> Optional[list[OpenquakeNrmlUnion]]:
        if not self.source_models_raw_ids:
            return None
        from data.dynamo import get_file
        from strawberry.relay import GlobalID
        results = []
        for gid_str in self.source_models_raw_ids:
            try:
                raw_id = GlobalID.from_id(gid_str).node_id
            except Exception:
                raw_id = gid_str
            data = get_file(info.context["dynamodb"], raw_id)
            if data:
                results.append(dispatch_nrml(data))
        return results or None

    @strawberry.field
    def template_archive(self, info: Info) -> Optional[_ToshiFile]:
        if not self.template_archive_raw_id:
            return None
        from data.dynamo import get_file
        from models.file import ToshiFile
        from strawberry.relay import GlobalID
        try:
            raw_id = GlobalID.from_id(self.template_archive_raw_id).node_id
        except Exception:
            raw_id = self.template_archive_raw_id
        data = get_file(info.context["dynamodb"], raw_id)
        return ToshiFile.from_dict(data) if data else None

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["OpenquakeHazardConfig"]:
        from data.dynamo import get_thing
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "OpenquakeHazardConfig":
        from data.models import OpenquakeHazardConfigData
        d = OpenquakeHazardConfigData.model_validate(data)
        return cls(
            pk=d.object_id,
            created=d.created,
            source_models_raw_ids=d.source_models,
            template_archive_raw_id=d.template_archive,
        )


@strawberry.input
class CreateOpenquakeHazardConfigInput:
    template_archive: strawberry.ID
    source_models: Optional[list[strawberry.ID]] = None
    created: Optional[str] = None


def resolve_openquake_hazard_configs(info: Info) -> Iterable[OpenquakeHazardConfig]:
    from data.dynamo import list_things
    items = list_things(info.context["dynamodb"], "OpenquakeHazardConfig")
    return [OpenquakeHazardConfig.from_dict(item) for item in items]


def mutate_create_openquake_hazard_config(
    info: Info, input: CreateOpenquakeHazardConfigInput
) -> OpenquakeHazardConfig:
    from data.dynamo import create_thing
    payload = {
        "created": input.created,
        "template_archive": str(input.template_archive),
        "source_models": [str(s) for s in input.source_models] if input.source_models else None,
    }
    data = create_thing(info.context["dynamodb"], "OpenquakeHazardConfig", payload)
    return OpenquakeHazardConfig.from_dict(data)
