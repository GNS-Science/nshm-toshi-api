"""
AutomationTask and RuptureGenerationTask — full implementations.

RuptureGenerationTask extends AutomationTask (same storage, same fields,
different clazz_name). Both live in ToshiThingObject.

Relations (files, parents, children) are stored as embedded arrays in the
Thing's JSON and assembled into virtual FileRelation / TaskTaskRelation objects.
"""
from typing import Iterable, Optional

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


def _kv_input_to_list(items) -> Optional[list[dict]]:
    if not items:
        return None
    return [{"k": i.k, "v": i.v} for i in items]


# ── AutomationTask ─────────────────────────────────────────────────────────────

@strawberry.type
class AutomationTask(relay.Node):
    """An automation task in the NSHM process."""

    pk: relay.NodeID[str]
    state: Optional[EventState] = None
    result: Optional[EventResult] = None
    task_type: Optional[TaskSubType] = None
    model_type: Optional[ModelType] = None
    created: Optional[str] = None
    duration: Optional[float] = None
    arguments: Optional[list[KeyValuePair]] = None
    environment: Optional[list[KeyValuePair]] = None
    metrics: Optional[list[KeyValuePair]] = None

    # Embedded relation arrays — hidden from schema, resolved lazily
    files_raw: strawberry.Private[Optional[list]] = None
    parents_raw: strawberry.Private[Optional[list]] = None
    children_raw: strawberry.Private[Optional[list]] = None

    @relay.connection(relay.ListConnection[FileRelation])
    def files(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_thing(self.pk, self.files_raw or [])

    @relay.connection(relay.ListConnection[TaskTaskRelation])
    def parents(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_parents(self.pk, self.parents_raw or [])

    @relay.connection(relay.ListConnection[TaskTaskRelation])
    def children(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_children(self.pk, self.children_raw or [])

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["AutomationTask"]:
        from data.dynamo import get_thing
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "AutomationTask":
        from data.models import AutomationTaskData
        d = AutomationTaskData.model_validate(data)
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
            files_raw=d.files,
            parents_raw=d.parents,
            children_raw=d.children,
        )


# ── RuptureGenerationTask ──────────────────────────────────────────────────────

@strawberry.type
class RuptureGenerationTask(relay.Node):
    """A rupture set generation task — stored identically to AutomationTask."""

    pk: relay.NodeID[str]
    state: Optional[EventState] = None
    result: Optional[EventResult] = None
    task_type: Optional[TaskSubType] = None
    created: Optional[str] = None
    duration: Optional[float] = None
    arguments: Optional[list[KeyValuePair]] = None
    environment: Optional[list[KeyValuePair]] = None
    metrics: Optional[list[KeyValuePair]] = None

    files_raw: strawberry.Private[Optional[list]] = None
    parents_raw: strawberry.Private[Optional[list]] = None
    children_raw: strawberry.Private[Optional[list]] = None

    @relay.connection(relay.ListConnection[FileRelation])
    def files(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_thing(self.pk, self.files_raw or [])

    @relay.connection(relay.ListConnection[TaskTaskRelation])
    def parents(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_parents(self.pk, self.parents_raw or [])

    @relay.connection(relay.ListConnection[TaskTaskRelation])
    def children(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_children(self.pk, self.children_raw or [])

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["RuptureGenerationTask"]:
        from data.dynamo import get_thing
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "RuptureGenerationTask":
        from data.models import AutomationTaskData
        d = AutomationTaskData.model_validate(data)
        return cls(
            pk=d.object_id,
            state=EventState(d.state) if d.state else None,
            result=EventResult(d.result) if d.result else None,
            task_type=TaskSubType(d.task_type) if d.task_type else None,
            created=d.created,
            duration=d.duration,
            arguments=[KeyValuePair(k=i.k, v=i.v) for i in d.arguments] if d.arguments else None,
            environment=[KeyValuePair(k=i.k, v=i.v) for i in d.environment] if d.environment else None,
            metrics=[KeyValuePair(k=i.k, v=i.v) for i in d.metrics] if d.metrics else None,
            files_raw=d.files,
            parents_raw=d.parents,
            children_raw=d.children,
        )


# ── Input types ───────────────────────────────────────────────────────────────

@strawberry.input
class CreateAutomationTaskInput:
    state: EventState
    result: EventResult
    created: str
    task_type: TaskSubType
    duration: Optional[float] = None
    model_type: Optional[ModelType] = None
    arguments: Optional[list[KeyValuePairInput]] = None
    environment: Optional[list[KeyValuePairInput]] = None
    metrics: Optional[list[KeyValuePairInput]] = None


@strawberry.input
class UpdateAutomationTaskInput:
    task_id: strawberry.ID
    state: Optional[EventState] = None
    result: Optional[EventResult] = None
    duration: Optional[float] = None
    arguments: Optional[list[KeyValuePairInput]] = None
    environment: Optional[list[KeyValuePairInput]] = None
    metrics: Optional[list[KeyValuePairInput]] = None


# ── Resolvers ─────────────────────────────────────────────────────────────────

def resolve_automation_tasks(info: Info) -> Iterable[AutomationTask]:
    from data.dynamo import list_things
    items = list_things(info.context["dynamodb"], "AutomationTask")
    return [AutomationTask.from_dict(item) for item in items]


def resolve_rupture_generation_tasks(info: Info) -> Iterable[RuptureGenerationTask]:
    from data.dynamo import list_things
    items = list_things(info.context["dynamodb"], "RuptureGenerationTask")
    return [RuptureGenerationTask.from_dict(item) for item in items]


def _build_payload(input, clazz_name: str) -> dict:
    return {
        "state": input.state.value if input.state else None,
        "result": input.result.value if input.result else None,
        "task_type": input.task_type.value if input.task_type else None,
        "model_type": input.model_type.value if hasattr(input, "model_type") and input.model_type else None,
        "created": input.created if hasattr(input, "created") else None,
        "duration": input.duration if input.duration else None,
        "arguments": _kv_input_to_list(input.arguments) if input.arguments else None,
        "environment": _kv_input_to_list(input.environment) if input.environment else None,
        "metrics": _kv_input_to_list(input.metrics) if input.metrics else None,
    }


def mutate_create_automation_task(info: Info, input: CreateAutomationTaskInput) -> AutomationTask:
    from data.dynamo import create_thing
    payload = _build_payload(input, "AutomationTask")
    data = create_thing(info.context["dynamodb"], "AutomationTask", payload)
    return AutomationTask.from_dict(data)


def mutate_create_rupture_generation_task(info: Info, input: CreateAutomationTaskInput) -> RuptureGenerationTask:
    from data.dynamo import create_thing
    payload = _build_payload(input, "RuptureGenerationTask")
    data = create_thing(info.context["dynamodb"], "RuptureGenerationTask", payload)
    return RuptureGenerationTask.from_dict(data)


def mutate_update_rupture_generation_task(
    info: Info, input: UpdateAutomationTaskInput
) -> Optional[RuptureGenerationTask]:
    from data.dynamo import update_thing
    from strawberry.relay import GlobalID
    gid = GlobalID.from_id(input.task_id)
    payload = {
        "state": input.state.value if input.state else None,
        "result": input.result.value if input.result else None,
        "duration": input.duration,
        "arguments": _kv_input_to_list(input.arguments),
        "environment": _kv_input_to_list(input.environment),
        "metrics": _kv_input_to_list(input.metrics),
    }
    data = update_thing(info.context["dynamodb"], gid.node_id, payload)
    return RuptureGenerationTask.from_dict(data) if data else None
