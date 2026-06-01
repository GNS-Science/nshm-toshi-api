"""OpenquakeHazardTask — Thing type extending AutomationTask with hazard-specific fields."""

from collections.abc import Iterable
from typing import Annotated, Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from .common import EventResult, EventState, KeyValuePair, KeyValuePairInput, ModelType, TaskSubType
from .relations import (
    FileRelation,
    TaskTaskRelation,
    build_file_relations_for_thing,
    build_task_children,
    build_task_parents,
)

_OpenquakeHazardSolution = Annotated["OpenquakeHazardSolution", strawberry.lazy("models.openquake_hazard_solution")]


@strawberry.type
class OpenquakeHazardTask(relay.Node):
    pk: relay.NodeID[str]
    state: EventState | None = None
    result: EventResult | None = None
    task_type: TaskSubType | None = None
    model_type: ModelType | None = None
    created: str | None = None
    duration: float | None = None
    arguments: list[KeyValuePair] | None = None
    environment: list[KeyValuePair] | None = None
    metrics: list[KeyValuePair] | None = None
    executor: str | None = None
    srm_logic_tree: str | None = None  # JSON string
    gmcm_logic_tree: str | None = None  # JSON string
    openquake_config: str | None = None  # JSON string

    files_raw: strawberry.Private[list | None] = None
    parents_raw: strawberry.Private[list | None] = None
    children_raw: strawberry.Private[list | None] = None
    hazard_solution_raw_id: strawberry.Private[str | None] = None

    @relay.connection(relay.ListConnection[FileRelation])
    def files(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_thing(self.pk, self.files_raw or [])

    @relay.connection(relay.ListConnection[TaskTaskRelation])
    def parents(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_parents(self.pk, self.parents_raw or [])

    @relay.connection(relay.ListConnection[TaskTaskRelation])
    def children(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_children(self.pk, self.children_raw or [])

    @strawberry.field
    def hazard_solution(self, info: Info) -> _OpenquakeHazardSolution | None:
        if not self.hazard_solution_raw_id:
            return None
        from strawberry.relay import GlobalID

        from data.dynamo import get_thing
        from models.openquake_hazard_solution import OpenquakeHazardSolution

        try:
            raw_id = GlobalID.from_id(self.hazard_solution_raw_id).node_id
        except Exception:
            raw_id = self.hazard_solution_raw_id
        data = get_thing(info.context["dynamodb"], raw_id)
        return OpenquakeHazardSolution.from_dict(data) if data else None

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["OpenquakeHazardTask"]:
        from data.dynamo import get_thing

        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "OpenquakeHazardTask":
        from data.models import OpenquakeHazardTaskData

        d = OpenquakeHazardTaskData.model_validate(data)
        return cls(
            pk=d.object_id,
            state=EventState(d.state) if d.state else None,
            result=EventResult(d.result) if d.result else None,
            task_type=TaskSubType(d.task_type) if d.task_type else None,
            model_type=ModelType(d.model_type) if d.model_type else None,
            created=d.created,
            duration=d.duration,
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
        )


@strawberry.input
class CreateOpenquakeHazardTaskInput:
    state: EventState
    result: EventResult
    created: str
    task_type: TaskSubType
    duration: float | None = None
    model_type: ModelType | None = None
    arguments: list[KeyValuePairInput] | None = None
    environment: list[KeyValuePairInput] | None = None
    metrics: list[KeyValuePairInput] | None = None
    executor: str | None = None
    srm_logic_tree: str | None = None
    gmcm_logic_tree: str | None = None
    openquake_config: str | None = None
    hazard_solution: strawberry.ID | None = None


@strawberry.input
class UpdateOpenquakeHazardTaskInput:
    task_id: strawberry.ID
    state: EventState | None = None
    result: EventResult | None = None
    duration: float | None = None
    arguments: list[KeyValuePairInput] | None = None
    environment: list[KeyValuePairInput] | None = None
    metrics: list[KeyValuePairInput] | None = None
    hazard_solution: strawberry.ID | None = None


def resolve_openquake_hazard_tasks(info: Info) -> Iterable[OpenquakeHazardTask]:
    from data.dynamo import list_things

    items = list_things(info.context["dynamodb"], "OpenquakeHazardTask")
    return [OpenquakeHazardTask.from_dict(item) for item in items]


def mutate_create_openquake_hazard_task(info: Info, input: CreateOpenquakeHazardTaskInput) -> OpenquakeHazardTask:
    from data.dynamo import create_thing

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
    from strawberry.relay import GlobalID

    from data.dynamo import update_thing

    gid = GlobalID.from_id(input.task_id)
    payload = {
        "state": input.state.value if input.state else None,
        "result": input.result.value if input.result else None,
        "duration": input.duration,
        "arguments": [{"k": i.k, "v": i.v} for i in input.arguments] if input.arguments else None,
        "environment": [{"k": i.k, "v": i.v} for i in input.environment] if input.environment else None,
        "metrics": [{"k": i.k, "v": i.v} for i in input.metrics] if input.metrics else None,
        "hazard_solution": str(input.hazard_solution) if input.hazard_solution else None,
    }
    data = update_thing(info.context["dynamodb"], gid.node_id, payload)
    return OpenquakeHazardTask.from_dict(data) if data else None
