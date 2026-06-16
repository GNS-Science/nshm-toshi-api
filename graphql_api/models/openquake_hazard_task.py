"""OpenquakeHazardTask — Thing type extending AutomationTask with hazard-specific fields."""

from collections.abc import Iterable
from typing import Annotated, Optional

import strawberry
from strawberry import relay
from strawberry.relay import GlobalID
from strawberry.types import Info

from graphql_api.data.dynamo import create_thing, get_thing, list_things, update_thing
from graphql_api.data.models import OpenquakeHazardTaskData

from .common import DateTime, EventResult, EventState, JSONString, KeyValuePair, KeyValuePairInput, ModelType, TaskSubType, _try_enum, client_mutation_id_input_field

from .thing import AutomationTaskInterface, Thing

from .inversion_solution_union import InversionSolutionUnion, resolve_task_inversion_solution
from .relations import (
    FileRelation,
    FileRelationsConnection,
    TaskRelationsConnection,
    TaskTaskRelation,
    build_file_relations_for_thing,
    build_task_children,
    build_task_parents,
)

_OpenquakeHazardSolution = Annotated["OpenquakeHazardSolution", strawberry.lazy("graphql_api.models.openquake_hazard_solution")]
_OpenquakeHazardConfig = Annotated["OpenquakeHazardConfig", strawberry.lazy("graphql_api.models.openquake_hazard_config")]

@strawberry.type
class OpenquakeHazardTask(relay.Node, Thing, AutomationTaskInterface):
    pk: relay.NodeID[str]
    state: EventState | None = None
    result: EventResult | None = None
    task_type: TaskSubType | None = None
    model_type: ModelType | None = None
    created: DateTime | None = None
    duration: float | None = None
    general_task_id: strawberry.ID | None = None
    arguments: list[KeyValuePair | None] | None = None
    environment: list[KeyValuePair | None] | None = None
    metrics: list[KeyValuePair | None] | None = None
    executor: str | None = None
    srm_logic_tree: JSONString | None = None
    gmcm_logic_tree: JSONString | None = None
    openquake_config: JSONString | None = None

    files_raw: strawberry.Private[list | None] = None
    parents_raw: strawberry.Private[list | None] = None
    children_raw: strawberry.Private[list | None] = None
    hazard_solution_raw_id: strawberry.Private[str | None] = None
    config_raw_id: strawberry.Private[str | None] = None

    @relay.connection(FileRelationsConnection)
    def files(self, info: Info) -> list[FileRelation | None]:
        return build_file_relations_for_thing(self.pk, self.files_raw or [])

    @relay.connection(TaskRelationsConnection)
    def parents(self, info: Info) -> list[TaskTaskRelation | None]:
        return build_task_parents(self.pk, self.parents_raw or [])

    @relay.connection(TaskRelationsConnection)
    def children(self, info: Info) -> list[TaskTaskRelation | None]:
        return build_task_children(self.pk, self.children_raw or [])

    @strawberry.field
    def inversion_solution(self, info: Info) -> InversionSolutionUnion | None:
        return resolve_task_inversion_solution(info.context["dynamodb"], self.files_raw)

    @strawberry.field(deprecation_reason="We no longer store this value.")
    def config(self, info: Info) -> _OpenquakeHazardConfig | None:
        if not self.config_raw_id:
            return None
        from graphql_api.models.openquake_hazard_config import OpenquakeHazardConfig  # noqa: PLC0415

        try:
            raw_id = GlobalID.from_id(self.config_raw_id).node_id
        except Exception:
            raw_id = self.config_raw_id
        data = get_thing(info.context["dynamodb"], raw_id)
        return OpenquakeHazardConfig.from_dict(data) if data else None

    @strawberry.field
    def hazard_solution(self, info: Info) -> _OpenquakeHazardSolution | None:
        if not self.hazard_solution_raw_id:
            return None
        from graphql_api.models.openquake_hazard_solution import OpenquakeHazardSolution  # noqa: PLC0415

        try:
            raw_id = GlobalID.from_id(self.hazard_solution_raw_id).node_id
        except Exception:
            raw_id = self.hazard_solution_raw_id
        data = get_thing(info.context["dynamodb"], raw_id)
        return OpenquakeHazardSolution.from_dict(data) if data else None

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["OpenquakeHazardTask"]:
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "OpenquakeHazardTask":
        d = OpenquakeHazardTaskData.model_validate(data)
        return cls(
            pk=d.object_id,
            state=_try_enum(EventState, d.state),
            result=_try_enum(EventResult, d.result),
            task_type=_try_enum(TaskSubType, d.task_type),
            model_type=_try_enum(ModelType, d.model_type),
            created=d.created,
            duration=d.duration,
            general_task_id=strawberry.ID(d.general_task_id) if d.general_task_id else None,
            arguments=[KeyValuePair(k=i.k, v=i.v) for i in d.arguments] if d.arguments else None,
            environment=[KeyValuePair(k=i.k, v=i.v) for i in d.environment] if d.environment else None,
            metrics=[KeyValuePair(k=i.k, v=i.v) for i in d.metrics] if d.metrics else None,
            executor=d.executor,
            srm_logic_tree=d.srm_logic_tree,
            gmcm_logic_tree=d.gmcm_logic_tree,
            openquake_config=d.openquake_config,
            files_raw=d.files,
            parents_raw=d.parents,
            children_raw=d.children,
            hazard_solution_raw_id=d.hazard_solution,
            config_raw_id=d.config,
        )

@strawberry.input
class CreateOpenquakeHazardTaskInput:
    state: EventState
    result: EventResult
    created: DateTime
    task_type: TaskSubType
    duration: float | None = None
    model_type: ModelType | None = None
    arguments: list[KeyValuePairInput | None] | None = None
    environment: list[KeyValuePairInput | None] | None = None
    metrics: list[KeyValuePairInput | None] | None = None
    executor: str | None = None
    srm_logic_tree: JSONString | None = None
    gmcm_logic_tree: JSONString | None = None
    openquake_config: JSONString | None = None
    hazard_solution: strawberry.ID | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()

@strawberry.input
class UpdateOpenquakeHazardTaskInput:
    task_id: strawberry.ID
    state: EventState | None = None
    result: EventResult | None = None
    duration: float | None = None
    arguments: list[KeyValuePairInput | None] | None = None
    environment: list[KeyValuePairInput | None] | None = None
    metrics: list[KeyValuePairInput | None] | None = None
    hazard_solution: strawberry.ID | None = None
    # Legacy parity: runzi's `complete_task` mutation sets executor on update.
    executor: str | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()

def resolve_openquake_hazard_tasks(info: Info) -> Iterable[OpenquakeHazardTask]:
    items = list_things(info.context["dynamodb"], "OpenquakeHazardTask")
    return [OpenquakeHazardTask.from_dict(item) for item in items]

def mutate_create_openquake_hazard_task(info: Info, input: CreateOpenquakeHazardTaskInput) -> OpenquakeHazardTask:
    payload = {
        "state": input.state.value,
        "result": input.result.value,
        "created": input.created,
        "task_type": input.task_type.value,
        "duration": input.duration,
        "model_type": input.model_type.value if input.model_type else None,
        "arguments": [{"k": i.k, "v": i.v} for i in input.arguments] if input.arguments else None,
        "environment": [{"k": i.k, "v": i.v} for i in input.environment] if input.environment else None,
        "metrics": [{"k": i.k, "v": i.v} for i in input.metrics] if input.metrics else None,
        "executor": input.executor,
        "srm_logic_tree": input.srm_logic_tree,
        "gmcm_logic_tree": input.gmcm_logic_tree,
        "openquake_config": input.openquake_config,
        "hazard_solution": str(input.hazard_solution) if input.hazard_solution else None,
    }
    data = create_thing(info.context["dynamodb"], "OpenquakeHazardTask", payload)
    return OpenquakeHazardTask.from_dict(data)

def mutate_update_openquake_hazard_task(
    info: Info, input: UpdateOpenquakeHazardTaskInput
) -> OpenquakeHazardTask | None:
    gid = GlobalID.from_id(input.task_id)
    payload = {
        "state": input.state.value if input.state else None,
        "result": input.result.value if input.result else None,
        "duration": input.duration,
        "arguments": [{"k": i.k, "v": i.v} for i in input.arguments] if input.arguments else None,
        "environment": [{"k": i.k, "v": i.v} for i in input.environment] if input.environment else None,
        "metrics": [{"k": i.k, "v": i.v} for i in input.metrics] if input.metrics else None,
        "hazard_solution": str(input.hazard_solution) if input.hazard_solution else None,
        "executor": input.executor,
    }
    data = update_thing(info.context["dynamodb"], gid.node_id, payload)
    return OpenquakeHazardTask.from_dict(data) if data else None
