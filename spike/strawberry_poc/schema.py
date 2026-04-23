"""
Root schema — Query + Mutation.

Designed as a drop-in replacement for the Graphene stack:
  - auto_camel_case=False  → field/mutation names stay snake_case
  - Payload wrapper types  → mutation return shapes match Graphene's relay
                             ClientIDMutation pattern exactly

This means all existing client query strings work unchanged against
either the old (Graphene/Flask) or new (Strawberry/FastAPI) stack.
"""
from typing import Annotated, Iterable, Optional, Union

import strawberry
from strawberry import relay
from strawberry.schema.config import StrawberryConfig

from models.automation_task import (
    AutomationTask,
    CreateAutomationTaskInput,
    RuptureGenerationTask,
    UpdateAutomationTaskInput,
    mutate_create_automation_task,
    mutate_create_rupture_generation_task,
    mutate_update_rupture_generation_task,
    resolve_automation_tasks,
    resolve_rupture_generation_tasks,
)
from models.file import CreateFileInput, ToshiFile, mutate_create_file, resolve_files
from models.general_task import (
    CreateGeneralTaskInput,
    GeneralTask,
    UpdateGeneralTaskInput,
    mutate_create_general_task,
    mutate_update_general_task,
    resolve_general_tasks,
)
from models.relations import (
    CreateFileRelationInput,
    CreateTaskRelationInput,
    TaskTaskRelation,
    mutate_create_file_relation,
    mutate_create_task_relation,
)
from models.rupture_set import (
    CreateRuptureSetInput,
    RuptureSet,
    mutate_create_rupture_set,
    resolve_rupture_sets,
)
from models.sms_file import CreateSmsFileInput, SmsFile, mutate_create_sms_file, resolve_sms_files
from models.strong_motion_station import (
    CreateStrongMotionStationInput,
    StrongMotionStation,
    mutate_create_strong_motion_station,
    resolve_strong_motion_stations,
)


# ── SearchResult union + connection ───────────────────────────────────────────

SearchResult = Annotated[
    Union[
        GeneralTask,
        RuptureGenerationTask,
        AutomationTask,
        StrongMotionStation,
        ToshiFile,
        SmsFile,
        RuptureSet,
    ],
    strawberry.union(name="SearchResult"),
]


@strawberry.type
class SearchResultEdge:
    node: Optional[SearchResult] = None


@strawberry.type
class SearchResultConnection:
    edges: list[SearchResultEdge] = strawberry.field(default_factory=list)


@strawberry.type
class SearchPayload:
    search_result: Optional[SearchResultConnection] = None


def _dispatch_search(hit: dict) -> Optional[SearchResult]:
    """Instantiate the right Strawberry type from an ES _source dict."""
    clazz = hit.get("clazz_name", "")
    try:
        if clazz == "GeneralTask":
            return GeneralTask.from_dict(hit)
        elif clazz == "RuptureGenerationTask":
            return RuptureGenerationTask.from_dict(hit)
        elif clazz == "AutomationTask":
            return AutomationTask.from_dict(hit)
        elif clazz == "StrongMotionStation":
            return StrongMotionStation.from_dict(hit)
        elif clazz == "SmsFile":
            return SmsFile.from_dict(hit)
        elif clazz == "RuptureSet":
            return RuptureSet.from_dict(hit)
        else:
            return ToshiFile.from_dict(hit)
    except Exception:
        return None


# ── Payload wrapper types (mirrors Graphene's ClientIDMutation Output pattern) ─

@strawberry.type
class CreateGeneralTaskPayload:
    general_task: Optional[GeneralTask] = None

@strawberry.type
class UpdateGeneralTaskPayload:
    general_task: Optional[GeneralTask] = None

@strawberry.type
class CreateRuptureGenerationTaskPayload:
    task_result: Optional[RuptureGenerationTask] = None

@strawberry.type
class UpdateRuptureGenerationTaskPayload:
    task_result: Optional[RuptureGenerationTask] = None

@strawberry.type
class CreateAutomationTaskPayload:
    task_result: Optional[AutomationTask] = None

@strawberry.type
class CreateFilePayload:
    ok: Optional[bool] = None
    file_result: Optional[ToshiFile] = None

@strawberry.type
class CreateSmsFilePayload:
    ok: Optional[bool] = None
    file_result: Optional[SmsFile] = None

@strawberry.type
class CreateStrongMotionStationPayload:
    strong_motion_station: Optional[StrongMotionStation] = None

@strawberry.type
class CreateRuptureSetPayload:
    ok: Optional[bool] = None
    rupture_set: Optional[RuptureSet] = None

@strawberry.type
class CreateFileRelationPayload:
    ok: Optional[bool] = None

@strawberry.type
class CreateTaskRelationPayload:
    ok: Optional[bool] = None
    thing_relation: Optional[TaskTaskRelation] = None


# ── Query ──────────────────────────────────────────────────────────────────────

@strawberry.type
class Query:
    node: relay.Node = relay.node()

    @relay.connection(relay.ListConnection[GeneralTask])
    def general_tasks(self, info: strawberry.types.Info) -> Iterable[GeneralTask]:
        return resolve_general_tasks(info)

    @relay.connection(relay.ListConnection[RuptureSet])
    def rupture_sets(self, info: strawberry.types.Info) -> Iterable[RuptureSet]:
        return resolve_rupture_sets(info)

    @relay.connection(relay.ListConnection[ToshiFile])
    def files(self, info: strawberry.types.Info) -> Iterable[ToshiFile]:
        return resolve_files(info)

    @relay.connection(relay.ListConnection[SmsFile])
    def sms_files(self, info: strawberry.types.Info) -> Iterable[SmsFile]:
        return resolve_sms_files(info)

    @relay.connection(relay.ListConnection[StrongMotionStation])
    def strong_motion_stations(self, info: strawberry.types.Info) -> Iterable[StrongMotionStation]:
        return resolve_strong_motion_stations(info)

    @relay.connection(relay.ListConnection[AutomationTask])
    def automation_tasks(self, info: strawberry.types.Info) -> Iterable[AutomationTask]:
        return resolve_automation_tasks(info)

    @relay.connection(relay.ListConnection[RuptureGenerationTask])
    def rupture_generation_tasks(self, info: strawberry.types.Info) -> Iterable[RuptureGenerationTask]:
        return resolve_rupture_generation_tasks(info)

    @strawberry.field
    def search(self, info: strawberry.types.Info, search_term: str) -> SearchPayload:
        from data.search import search as es_search
        ctx = info.context
        hits = es_search(
            search_term,
            endpoint=ctx.get("es_endpoint", ""),
            index=ctx.get("es_index", "toshi-index-mapped"),
        )
        edges = [
            SearchResultEdge(node=node)
            for hit in hits
            if (node := _dispatch_search(hit)) is not None
        ]
        return SearchPayload(search_result=SearchResultConnection(edges=edges))


# ── Mutation ───────────────────────────────────────────────────────────────────

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_general_task(
        self, info: strawberry.types.Info, input: CreateGeneralTaskInput
    ) -> CreateGeneralTaskPayload:
        return CreateGeneralTaskPayload(general_task=mutate_create_general_task(info, input))

    @strawberry.mutation
    def update_general_task(
        self, info: strawberry.types.Info, input: UpdateGeneralTaskInput
    ) -> UpdateGeneralTaskPayload:
        return UpdateGeneralTaskPayload(general_task=mutate_update_general_task(info, input))

    @strawberry.mutation
    def create_rupture_set(
        self, info: strawberry.types.Info, input: CreateRuptureSetInput
    ) -> CreateRuptureSetPayload:
        return CreateRuptureSetPayload(ok=True, rupture_set=mutate_create_rupture_set(info, input))

    @strawberry.mutation
    def create_file(
        self, info: strawberry.types.Info, input: CreateFileInput
    ) -> CreateFilePayload:
        return CreateFilePayload(ok=True, file_result=mutate_create_file(info, input))

    @strawberry.mutation
    def create_sms_file(
        self, info: strawberry.types.Info, input: CreateSmsFileInput
    ) -> CreateSmsFilePayload:
        return CreateSmsFilePayload(ok=True, file_result=mutate_create_sms_file(info, input))

    @strawberry.mutation
    def create_strong_motion_station(
        self, info: strawberry.types.Info, input: CreateStrongMotionStationInput
    ) -> CreateStrongMotionStationPayload:
        return CreateStrongMotionStationPayload(
            strong_motion_station=mutate_create_strong_motion_station(info, input)
        )

    @strawberry.mutation
    def create_automation_task(
        self, info: strawberry.types.Info, input: CreateAutomationTaskInput
    ) -> CreateAutomationTaskPayload:
        return CreateAutomationTaskPayload(task_result=mutate_create_automation_task(info, input))

    @strawberry.mutation
    def create_rupture_generation_task(
        self, info: strawberry.types.Info, input: CreateAutomationTaskInput
    ) -> CreateRuptureGenerationTaskPayload:
        return CreateRuptureGenerationTaskPayload(
            task_result=mutate_create_rupture_generation_task(info, input)
        )

    @strawberry.mutation
    def update_rupture_generation_task(
        self, info: strawberry.types.Info, input: UpdateAutomationTaskInput
    ) -> UpdateRuptureGenerationTaskPayload:
        return UpdateRuptureGenerationTaskPayload(
            task_result=mutate_update_rupture_generation_task(info, input)
        )

    @strawberry.mutation
    def create_file_relation(
        self, info: strawberry.types.Info, input: CreateFileRelationInput
    ) -> CreateFileRelationPayload:
        mutate_create_file_relation(info, input)
        return CreateFileRelationPayload(ok=True)

    @strawberry.mutation
    def create_task_relation(
        self, info: strawberry.types.Info, input: CreateTaskRelationInput
    ) -> CreateTaskRelationPayload:
        relation = mutate_create_task_relation(info, input)
        return CreateTaskRelationPayload(ok=True, thing_relation=relation)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    config=StrawberryConfig(auto_camel_case=False),
)
