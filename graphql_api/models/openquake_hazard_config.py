"""OpenquakeHazardConfig — Thing type holding source model references."""

from collections.abc import Iterable
from typing import Annotated, Optional

import strawberry
from strawberry import relay
from strawberry.relay import GlobalID
from strawberry.types import Info

from graphql_api.data.dynamo import create_thing, get_file, get_thing, list_things
from graphql_api.data.models import OpenquakeHazardConfigData
from graphql_api.models.common import DateTime, client_mutation_id_input_field
from graphql_api.models.file import ToshiFile
from graphql_api.models.inversion_solution_nrml import InversionSolutionNrml
from graphql_api.models.thing import Thing

# ── OpenquakeNrmlUnion ────────────────────────────────────────────────────────

_ToshiFile = Annotated["ToshiFile", strawberry.lazy("graphql_api.models.file")]
_InversionSolutionNrml = Annotated["InversionSolutionNrml", strawberry.lazy("graphql_api.models.inversion_solution_nrml")]

OpenquakeNrmlUnion = Annotated[
    _ToshiFile | _InversionSolutionNrml,
    strawberry.union(name="OpenquakeNrmlUnion"),
]


def dispatch_nrml(data: dict):
    clazz = data.get("clazz_name", "")
    if clazz == "InversionSolutionNrml":
        return InversionSolutionNrml.from_dict(data)
    return ToshiFile.from_dict(data)


# ── OpenquakeHazardConfig ─────────────────────────────────────────────────────


@strawberry.type
class OpenquakeHazardConfig(relay.Node, Thing):
    pk: relay.NodeID[str]
    created: DateTime | None = None

    source_models_raw_ids: strawberry.Private[list[str | None] | None] = None
    template_archive_raw_id: strawberry.Private[str | None] = None

    @strawberry.field
    def source_models(self, info: Info) -> list[OpenquakeNrmlUnion | None] | None:
        if not self.source_models_raw_ids:
            return None
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
    def template_archive(self, info: Info) -> _ToshiFile | None:
        if not self.template_archive_raw_id:
            return None
        try:
            raw_id = GlobalID.from_id(self.template_archive_raw_id).node_id
        except Exception:
            raw_id = self.template_archive_raw_id
        data = get_file(info.context["dynamodb"], raw_id)
        return ToshiFile.from_dict(data) if data else None

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["OpenquakeHazardConfig"]:
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "OpenquakeHazardConfig":
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
    source_models: list[strawberry.ID | None] | None = None
    created: DateTime | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()


def resolve_openquake_hazard_configs(info: Info) -> Iterable[OpenquakeHazardConfig]:
    items = list_things(info.context["dynamodb"], "OpenquakeHazardConfig")
    return [OpenquakeHazardConfig.from_dict(item) for item in items]


def mutate_create_openquake_hazard_config(info: Info, input: CreateOpenquakeHazardConfigInput) -> OpenquakeHazardConfig:
    payload = {
        "created": input.created,
        "template_archive": str(input.template_archive),
        "source_models": [str(s) for s in input.source_models] if input.source_models else None,
    }
    data = create_thing(info.context["dynamodb"], "OpenquakeHazardConfig", payload)
    return OpenquakeHazardConfig.from_dict(data)
