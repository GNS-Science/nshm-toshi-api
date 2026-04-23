"""
GeneralTask — Strawberry/relay equivalent of graphql_api/schema/custom/general_task.py

Key differences vs Graphene:
  - No Meta class, no separate Connection class — relay.ListConnection[GeneralTask] handles it
  - Input types are @strawberry.input dataclasses, not inner classes
  - get_node() becomes resolve_node() classmethod
  - Children/parents relations omitted in POC (same pattern as produced_by on RuptureSet)
"""
from typing import Iterable, Optional

import strawberry
from strawberry import relay
from strawberry.types import Info

from .common import KeyValueListPair, KeyValueListPairInput, KeyValuePair, KeyValuePairInput, ModelType, TaskSubType
from .relations import (
    FileRelation,
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
    title: Optional[str] = None
    description: Optional[str] = None
    agent_name: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    notes: Optional[str] = None
    subtask_count: Optional[int] = None
    subtask_type: Optional[TaskSubType] = None
    model_type: Optional[ModelType] = None
    argument_lists: Optional[list[KeyValueListPair]] = None
    meta: Optional[list[KeyValuePair]] = None

    files_raw: strawberry.Private[Optional[list]] = None
    children_raw: strawberry.Private[Optional[list]] = None
    parents_raw: strawberry.Private[Optional[list]] = None

    @relay.connection(relay.ListConnection[FileRelation])
    def files(self, info: Info) -> list[FileRelation]:
        return build_file_relations_for_thing(self.pk, self.files_raw or [])

    @relay.connection(relay.ListConnection[TaskTaskRelation])
    def children(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_children(self.pk, self.children_raw or [])

    @relay.connection(relay.ListConnection[TaskTaskRelation])
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
        from data.dynamo import get_thing
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "GeneralTask":
        kvl = data.get("argument_lists")
        meta = data.get("meta")
        return cls(
            pk=data["object_id"],
            title=data.get("title"),
            description=data.get("description"),
            agent_name=data.get("agent_name"),
            created=data.get("created"),
            updated=data.get("updated"),
            notes=data.get("notes"),
            subtask_count=data.get("subtask_count"),
            subtask_type=TaskSubType(data["subtask_type"]) if data.get("subtask_type") else None,
            model_type=ModelType(data["model_type"]) if data.get("model_type") else None,
            argument_lists=[KeyValueListPair(k=i["k"], v=i["v"]) for i in kvl] if kvl else None,
            meta=[KeyValuePair(k=i["k"], v=i["v"]) for i in meta] if meta else None,
            files_raw=data.get("files", []),
            children_raw=data.get("children", []),
            parents_raw=data.get("parents", []),
        )


@strawberry.input
class CreateGeneralTaskInput:
    title: Optional[str] = None
    description: Optional[str] = None
    agent_name: Optional[str] = None
    created: Optional[str] = None
    notes: Optional[str] = None
    subtask_count: Optional[int] = None
    subtask_type: Optional[TaskSubType] = None
    model_type: Optional[ModelType] = None
    argument_lists: Optional[list[KeyValueListPairInput]] = None
    meta: Optional[list[KeyValuePairInput]] = None


@strawberry.input
class UpdateGeneralTaskInput:
    task_id: strawberry.ID
    title: Optional[str] = None
    description: Optional[str] = None
    agent_name: Optional[str] = None
    updated: Optional[str] = None
    notes: Optional[str] = None
    subtask_count: Optional[int] = None
    subtask_type: Optional[TaskSubType] = None
    model_type: Optional[ModelType] = None
    argument_lists: Optional[list[KeyValueListPairInput]] = None
    meta: Optional[list[KeyValuePairInput]] = None


def resolve_general_tasks(info: Info) -> Iterable[GeneralTask]:
    from data.dynamo import list_things
    items = list_things(info.context["dynamodb"], "GeneralTask")
    return [GeneralTask.from_dict(item) for item in items]


def mutate_create_general_task(info: Info, input: CreateGeneralTaskInput) -> GeneralTask:
    from data.dynamo import create_thing

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
        "model_type": input.model_type.value if input.model_type else None,
        "argument_lists": _kvl(input.argument_lists),
        "meta": _kvl(input.meta),
    }
    data = create_thing(info.context["dynamodb"], "GeneralTask", payload)
    return GeneralTask.from_dict(data)


def mutate_update_general_task(info: Info, input: UpdateGeneralTaskInput) -> Optional[GeneralTask]:
    from data.dynamo import update_thing

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
