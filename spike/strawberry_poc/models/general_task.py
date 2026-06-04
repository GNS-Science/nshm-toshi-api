"""
GeneralTask — Strawberry/relay equivalent of graphql_api/schema/custom/general_task.py

Key differences vs Graphene:
  - No Meta class, no separate Connection class — relay.ListConnection[GeneralTask] handles it
  - Input types are @strawberry.input dataclasses, not inner classes
  - get_node() becomes resolve_node() classmethod
  - Children/parents relations omitted in POC (same pattern as produced_by on RuptureSet)
"""

from collections.abc import Iterable
from typing import Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from data.dynamo import create_thing, get_thing, list_things, update_thing
from data.models import GeneralTaskData

from .common import (
    EventResult,
    KeyValueListPair,
    KeyValueListPairInput,
    KeyValuePair,
    KeyValuePairInput,
    ModelType,
    TaskSubType,
    _try_enum,
)
from .relations import (
    FileRelation,
    FileRelationsConnection,
    TaskRelationsConnection,
    TaskTaskRelation,
    build_file_relations_for_thing,
    build_task_children,
    build_task_parents,
)


@strawberry.type
class GeneralTask(relay.Node):
    """
    A General Task captures metadata and related inputs/outputs for arbitrary tasks.
    """

    pk: relay.NodeID[str]
    title: str | None = None
    description: str | None = None
    agent_name: str | None = None
    created: str | None = None
    updated: str | None = None
    notes: str | None = None
    subtask_count: int | None = None
    subtask_type: TaskSubType | None = None
    subtask_result: EventResult | None = None
    model_type: ModelType | None = None
    argument_lists: list[KeyValueListPair] | None = None
    meta: list[KeyValuePair] | None = None

    files_raw: strawberry.Private[list | None] = None
    children_raw: strawberry.Private[list | None] = None
    parents_raw: strawberry.Private[list | None] = None

    @relay.connection(FileRelationsConnection)
    def files(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_thing(self.pk, self.files_raw or [])

    @relay.connection(TaskRelationsConnection)
    def children(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_children(self.pk, self.children_raw or [])

    @relay.connection(TaskRelationsConnection)
    def parents(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_parents(self.pk, self.parents_raw or [])

    @strawberry.field
    def swept_arguments(self) -> list[str]:
        """Keys with >1 value in argument_lists."""
        if not self.argument_lists:
            return []
        return [item.k for item in self.argument_lists if len(item.v) > 1]

    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Info,
        **kwargs,
    ) -> Optional["GeneralTask"]:
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "GeneralTask":
        d = GeneralTaskData.model_validate(data)
        return cls(
            pk=d.object_id,
            title=d.title,
            description=d.description,
            agent_name=d.agent_name,
            created=d.created,
            updated=d.updated,
            notes=d.notes,
            subtask_count=d.subtask_count,
            subtask_type=_try_enum(TaskSubType, d.subtask_type),
            subtask_result=_try_enum(EventResult, d.subtask_result),
            model_type=_try_enum(ModelType, d.model_type),
            argument_lists=[KeyValueListPair(k=i.k, v=i.v) for i in d.argument_lists] if d.argument_lists else None,
            meta=[KeyValuePair(k=i.k, v=i.v) for i in d.meta] if d.meta else None,
            files_raw=d.files,
            children_raw=d.children,
            parents_raw=d.parents,
        )


@strawberry.input
class CreateGeneralTaskInput:
    title: str | None = None
    description: str | None = None
    agent_name: str | None = None
    created: str | None = None
    notes: str | None = None
    subtask_count: int | None = None
    subtask_type: TaskSubType | None = None
    subtask_result: EventResult | None = None
    model_type: ModelType | None = None
    argument_lists: list[KeyValueListPairInput] | None = None
    meta: list[KeyValuePairInput] | None = None


@strawberry.input
class UpdateGeneralTaskInput:
    task_id: strawberry.ID
    title: str | None = None
    description: str | None = None
    agent_name: str | None = None
    updated: str | None = None
    notes: str | None = None
    subtask_count: int | None = None
    subtask_type: TaskSubType | None = None
    subtask_result: EventResult | None = None
    model_type: ModelType | None = None
    argument_lists: list[KeyValueListPairInput] | None = None
    meta: list[KeyValuePairInput] | None = None


def resolve_general_tasks(info: Info) -> Iterable[GeneralTask]:
    items = list_things(info.context["dynamodb"], "GeneralTask")
    return [GeneralTask.from_dict(item) for item in items]


def mutate_create_general_task(info: Info, input: CreateGeneralTaskInput) -> GeneralTask:
    def _kvl(items):
        return [{"k": i.k, "v": i.v} for i in items] if items else None

    payload = {
        "title": input.title,
        "description": input.description,
        "agent_name": input.agent_name,
        "created": input.created,
        "notes": input.notes,
        "subtask_count": input.subtask_count,
        "subtask_type": input.subtask_type.value if input.subtask_type else None,
        "subtask_result": input.subtask_result.value if input.subtask_result else None,
        "model_type": input.model_type.value if input.model_type else None,
        "argument_lists": _kvl(input.argument_lists),
        "meta": _kvl(input.meta),
    }
    data = create_thing(info.context["dynamodb"], "GeneralTask", payload)
    return GeneralTask.from_dict(data)


def mutate_update_general_task(info: Info, input: UpdateGeneralTaskInput) -> GeneralTask | None:
    # Decode relay global ID → raw object_id
    gid = relay.GlobalID.from_id(input.task_id)
    object_id = gid.node_id

    def _kvl(items):
        return [{"k": i.k, "v": i.v} for i in items] if items else None

    payload = {
        "title": input.title,
        "description": input.description,
        "agent_name": input.agent_name,
        "updated": input.updated,
        "notes": input.notes,
        "subtask_count": input.subtask_count,
        "subtask_type": input.subtask_type.value if input.subtask_type else None,
        "model_type": input.model_type.value if input.model_type else None,
        "argument_lists": _kvl(input.argument_lists),
        "meta": _kvl(input.meta),
    }
    data = update_thing(info.context["dynamodb"], object_id, payload)
    return GeneralTask.from_dict(data) if data else None
