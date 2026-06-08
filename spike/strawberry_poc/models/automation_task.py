"""
AutomationTask and RuptureGenerationTask — full implementations.

RuptureGenerationTask extends AutomationTask (same storage, same fields,
different clazz_name). Both live in ToshiThingObject.

Relations (files, parents, children) are stored as embedded arrays in the
Thing's JSON and assembled into virtual FileRelation / TaskTaskRelation objects.
"""

from collections.abc import Iterable
from typing import Optional

import strawberry
from strawberry import relay
from strawberry.relay import GlobalID
from strawberry.types import Info

from data.dynamo import create_thing, get_thing, list_things, update_thing
from data.models import AutomationTaskData

from .common import client_mutation_id_input_field, EventResult, EventState, KeyValuePair, KeyValuePairInput, ModelType, TaskSubType, _try_enum
from .relations import (
    FileRelation,
    FileRelationsConnection,
    TaskRelationsConnection,
    TaskTaskRelation,
    build_file_relations_for_thing,
    build_task_children,
    build_task_parents,
)


def _kv_input_to_list(items) -> list[dict] | None:
    if not items:
        return None
    return [{"k": i.k, "v": i.v} for i in items]


# ── AutomationTask ─────────────────────────────────────────────────────────────


@strawberry.type
class AutomationTask(relay.Node):
    """An automation task in the NSHM process."""

    pk: relay.NodeID[str]
    state: EventState | None = None
    result: EventResult | None = None
    task_type: TaskSubType | None = None
    model_type: ModelType | None = None
    created: str | None = None
    duration: float | None = None
    general_task_id: strawberry.ID | None = None
    arguments: list[KeyValuePair] | None = None
    environment: list[KeyValuePair] | None = None
    metrics: list[KeyValuePair] | None = None

    # Embedded relation arrays — hidden from schema, resolved lazily
    files_raw: strawberry.Private[list | None] = None
    parents_raw: strawberry.Private[list | None] = None
    children_raw: strawberry.Private[list | None] = None

    @relay.connection(FileRelationsConnection)
    def files(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_thing(self.pk, self.files_raw or [])

    @relay.connection(TaskRelationsConnection)
    def parents(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_parents(self.pk, self.parents_raw or [])

    @relay.connection(TaskRelationsConnection)
    def children(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_children(self.pk, self.children_raw or [])

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["AutomationTask"]:
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "AutomationTask":
        d = AutomationTaskData.model_validate(data)
        return cls(
            pk=d.object_id,
            state=_try_enum(EventState, d.state),
            result=_try_enum(EventResult, d.result),
            task_type=_try_enum(TaskSubType, d.task_type),
            model_type=_try_enum(ModelType, d.model_type),
            created=d.created,
            duration=d.duration,
            arguments=[KeyValuePair(k=i.k, v=i.v) for i in d.arguments] if d.arguments else None,
            environment=[KeyValuePair(k=i.k, v=i.v) for i in d.environment] if d.environment else None,
            metrics=[KeyValuePair(k=i.k, v=i.v) for i in d.metrics] if d.metrics else None,
            general_task_id=strawberry.ID(d.general_task_id) if d.general_task_id else None,
            files_raw=d.files,
            parents_raw=d.parents,
            children_raw=d.children,
        )


# ── RuptureGenerationTask ──────────────────────────────────────────────────────


@strawberry.type
class RuptureGenerationTask(relay.Node):
    """A rupture set generation task — stored identically to AutomationTask."""

    pk: relay.NodeID[str]
    state: EventState | None = None
    result: EventResult | None = None
    task_type: TaskSubType | None = None
    created: str | None = None
    duration: float | None = None
    general_task_id: strawberry.ID | None = None
    arguments: list[KeyValuePair] | None = None
    environment: list[KeyValuePair] | None = None
    metrics: list[KeyValuePair] | None = None

    files_raw: strawberry.Private[list | None] = None
    parents_raw: strawberry.Private[list | None] = None
    children_raw: strawberry.Private[list | None] = None

    @relay.connection(FileRelationsConnection)
    def files(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_thing(self.pk, self.files_raw or [])

    @relay.connection(TaskRelationsConnection)
    def parents(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_parents(self.pk, self.parents_raw or [])

    @relay.connection(TaskRelationsConnection)
    def children(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_children(self.pk, self.children_raw or [])

    @classmethod
    def resolve_node(cls, node_id: str, *, info: Info, **kwargs) -> Optional["RuptureGenerationTask"]:
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "RuptureGenerationTask":
        d = AutomationTaskData.model_validate(data)
        return cls(
            pk=d.object_id,
            state=_try_enum(EventState, d.state),
            result=_try_enum(EventResult, d.result),
            task_type=_try_enum(TaskSubType, d.task_type),
            created=d.created,
            duration=d.duration,
            arguments=[KeyValuePair(k=i.k, v=i.v) for i in d.arguments] if d.arguments else None,
            environment=[KeyValuePair(k=i.k, v=i.v) for i in d.environment] if d.environment else None,
            metrics=[KeyValuePair(k=i.k, v=i.v) for i in d.metrics] if d.metrics else None,
            general_task_id=strawberry.ID(d.general_task_id) if d.general_task_id else None,
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
    duration: float | None = None
    model_type: ModelType | None = None
    arguments: list[KeyValuePairInput] | None = None
    environment: list[KeyValuePairInput] | None = None
    metrics: list[KeyValuePairInput] | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()


@strawberry.input
class UpdateAutomationTaskInput:
    task_id: strawberry.ID
    state: EventState | None = None
    result: EventResult | None = None
    duration: float | None = None
    arguments: list[KeyValuePairInput] | None = None
    environment: list[KeyValuePairInput] | None = None
    metrics: list[KeyValuePairInput] | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()


# ── Resolvers ─────────────────────────────────────────────────────────────────


def resolve_automation_tasks(info: Info) -> Iterable[AutomationTask]:
    items = list_things(info.context["dynamodb"], "AutomationTask")
    return [AutomationTask.from_dict(item) for item in items]


def resolve_rupture_generation_tasks(info: Info) -> Iterable[RuptureGenerationTask]:
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
    payload = _build_payload(input, "AutomationTask")
    data = create_thing(info.context["dynamodb"], "AutomationTask", payload)
    return AutomationTask.from_dict(data)


def mutate_create_rupture_generation_task(info: Info, input: CreateAutomationTaskInput) -> RuptureGenerationTask:
    payload = _build_payload(input, "RuptureGenerationTask")
    data = create_thing(info.context["dynamodb"], "RuptureGenerationTask", payload)
    return RuptureGenerationTask.from_dict(data)


def mutate_update_automation_task(info: Info, input: UpdateAutomationTaskInput) -> AutomationTask | None:
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
    return AutomationTask.from_dict(data) if data else None


def mutate_update_rupture_generation_task(info: Info, input: UpdateAutomationTaskInput) -> RuptureGenerationTask | None:
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
