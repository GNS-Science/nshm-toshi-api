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

from graphql_api.data.dynamo import create_thing, get_thing, list_things, update_thing
from graphql_api.data.models import AutomationTaskData
from graphql_api.models._base.thing import AutomationTaskInterface, Thing
from graphql_api.models._infra.common import (
    DateTime,
    EventResult,
    EventState,
    KeyValuePair,
    KeyValuePairInput,
    ModelType,
    TaskSubType,
    _try_enum,
    client_mutation_id_input_field,
)
from graphql_api.models._infra.inversion_solution_union import InversionSolutionUnion, resolve_task_inversion_solution
from graphql_api.models.relations import (
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
class AutomationTask(relay.Node, Thing, AutomationTaskInterface):
    """An automation task in the NSHM process."""

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

    # Embedded relation arrays — hidden from schema, resolved lazily
    files_raw: strawberry.Private[list | None] = None
    parents_raw: strawberry.Private[list | None] = None
    children_raw: strawberry.Private[list | None] = None

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
class RuptureGenerationTask(relay.Node, Thing, AutomationTaskInterface):
    """A rupture set generation task — stored identically to AutomationTask."""

    pk: relay.NodeID[str]
    state: EventState | None = None
    result: EventResult | None = None
    task_type: TaskSubType | None = None
    created: DateTime | None = None
    duration: float | None = None
    general_task_id: strawberry.ID | None = None
    arguments: list[KeyValuePair | None] | None = None
    environment: list[KeyValuePair | None] | None = None
    metrics: list[KeyValuePair | None] | None = None

    files_raw: strawberry.Private[list | None] = None
    parents_raw: strawberry.Private[list | None] = None
    children_raw: strawberry.Private[list | None] = None

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
    created: DateTime
    task_type: TaskSubType
    duration: float | None = None
    model_type: ModelType | None = None
    # Links this AT to its parent GeneralTask. When set, the resolver
    # validates the AT's `arguments` against the GT's swept_arguments
    # (mirrors graphql_api/schema/custom/automation_task.py:197-234).
    general_task_id: strawberry.ID | None = None
    arguments: list[KeyValuePairInput | None] | None = None
    environment: list[KeyValuePairInput | None] | None = None
    metrics: list[KeyValuePairInput | None] | None = None
    client_mutation_id: str | None = client_mutation_id_input_field()


@strawberry.input
class UpdateAutomationTaskInput:
    task_id: strawberry.ID
    state: EventState | None = None
    result: EventResult | None = None
    duration: float | None = None
    arguments: list[KeyValuePairInput | None] | None = None
    environment: list[KeyValuePairInput | None] | None = None
    metrics: list[KeyValuePairInput | None] | None = None
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
        "general_task_id": str(input.general_task_id)
        if hasattr(input, "general_task_id") and input.general_task_id
        else None,
        "arguments": _kv_input_to_list(input.arguments) if input.arguments else None,
        "environment": _kv_input_to_list(input.environment) if input.environment else None,
        "metrics": _kv_input_to_list(input.metrics) if input.metrics else None,
    }


def _validate_at_arguments_against_gt(dynamodb, gt_id: str, at_arguments: list | None) -> None:
    """Validate that an AT's arguments satisfy the parent GT's swept_arguments.

    Mirrors graphql_api/schema/custom/automation_task.py:197-234. Raises
    ValueError with one of four legacy-compatible messages:

      - "is not a `GeneralTask`"           — global ID's type_name isn't GeneralTask
      - "was not found"                    — GT lookup miss
      - "was not found in new AutomationTask." — AT missing a key the GT marks as swept
      - "not a member of GeneralTask.swept_arguments values" — AT value not in GT's list

    Called only when input.general_task_id is set. If unset, validation is
    skipped — matches the legacy "skip validation with no gt" behaviour
    exercised by test_argument_skip_validation_with_no_gt_OK.
    """
    from graphql_api.models.general_task import GeneralTask  # noqa: PLC0415

    try:
        gid = GlobalID.from_id(gt_id)
    except Exception as exc:
        raise ValueError(f"the given id {gt_id} is not a valid Relay GlobalID: {exc}") from exc

    if gid.type_name != "GeneralTask":
        raise ValueError(f"the given id {gt_id} type: {gid.type_name} is not a `GeneralTask`")

    data = get_thing(dynamodb, gid.node_id)
    if not data:
        raise ValueError(f"GeneralTask {gt_id} was not found")

    gt = GeneralTask.from_dict(data)
    swept_keys = [item.k for item in (gt.argument_lists or []) if len(item.v) > 1]
    if not swept_keys:
        return

    at_args_map = {arg.k: arg.v for arg in (at_arguments or [])}
    gt_args_map = {item.k: list(item.v) for item in (gt.argument_lists or [])}

    for swept_key in swept_keys:
        if swept_key not in at_args_map:
            raise ValueError(
                f"swept key {swept_key} from GeneralTask.swept_arguments was not found in new AutomationTask."
            )
        if at_args_map[swept_key] not in gt_args_map[swept_key]:
            raise ValueError(
                f"argument `{swept_key}` value: `{at_args_map[swept_key]}` in new AutomationTask"
                f" not a member of GeneralTask.swept_arguments values: `{gt_args_map[swept_key]}`."
            )


def mutate_create_automation_task(info: Info, input: CreateAutomationTaskInput) -> AutomationTask:
    if input.general_task_id:
        _validate_at_arguments_against_gt(info.context["dynamodb"], str(input.general_task_id), input.arguments)
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
