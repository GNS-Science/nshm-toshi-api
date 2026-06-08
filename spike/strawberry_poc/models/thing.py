"""
Thing and AutomationTaskInterface — shared interfaces for entity/task types.

Implements ADR-002 Category 1: adopt the two interfaces declared in the
legacy Graphene schema. weka uses both via fragment queries:

    ... on Thing { children { edges { node { ... } } } }
    ... on AutomationTaskInterface { parents { edges { ... } } }

Without these interface declarations, those queries fail at GraphQL
validation time. The concrete types (GeneralTask, AutomationTask, etc.)
already declare the underlying fields independently — this module just
factors them up to a shared interface so fragment queries resolve.

Pattern: the interface declares the relay-connection resolvers with the
shared private-field naming convention used by every concrete Thing-like
type in the POC (`files_raw`, `parents_raw`, `children_raw`, `pk`).
Concrete types inherit the resolvers from the interface; only the
private fields need to be populated in their `from_dict` classmethods.
"""

from typing import TYPE_CHECKING

import strawberry
from strawberry import relay
from strawberry.types import Info

from .common import EventResult, EventState, KeyValuePair, ModelType, TaskSubType

# `created` is typed `str | None` here to match the spike base. Once
# strawberry-poc-phase1-scalars (#303) lands, flip both interfaces to
# `created: DateTime | None`.
from .relations import (
    FileRelation,
    FileRelationsConnection,
    TaskRelationsConnection,
    TaskTaskRelation,
    build_file_relations_for_thing,
    build_task_children,
    build_task_parents,
)

if TYPE_CHECKING:
    pass


# ── Thing interface ──────────────────────────────────────────────────────────


@strawberry.interface
class Thing:
    """A Thing in the NSHM saga — anything stored in ToshiThingObject.

    Provides the four shared fields (`created`, `files`, `parents`, `children`)
    that every concrete Thing-like type exposes. Mirrors the legacy
    `interface Thing` declaration so weka's `... on Thing { ... }` fragment
    queries work against the POC.

    Concrete types implementing Thing must populate the `pk` and the three
    `_raw` private fields in their `from_dict` constructors. The resolvers
    here are inherited; no per-type overrides needed.
    """

    pk: strawberry.Private[str] = ""
    created: str | None = None
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


# ── AutomationTaskInterface ──────────────────────────────────────────────────


@strawberry.interface
class AutomationTaskInterface:
    """Interface shared by AutomationTask, RuptureGenerationTask, OpenquakeHazardTask.

    Provides the event-tracking + arguments/environment/metrics fields that
    every automation-task-like concrete type exposes. Mirrors the legacy
    `interface AutomationTaskInterface` so weka's deep-traversal pattern
    `... on AutomationTaskInterface { parents { edges { node { parent { ... } } } } }`
    works against the POC.

    The interface does NOT inherit from Thing because legacy keeps them
    separate (different field sets, slightly different semantics around
    `task_type` and `general_task_id`). Concrete types may declare both
    interfaces — that's the legacy pattern too.
    """

    pk: strawberry.Private[str] = ""
    state: EventState | None = None
    result: EventResult | None = None
    created: str | None = None
    duration: float | None = None
    general_task_id: strawberry.ID | None = None
    task_type: TaskSubType | None = None
    model_type: ModelType | None = None
    arguments: list[KeyValuePair] | None = None
    environment: list[KeyValuePair] | None = None
    metrics: list[KeyValuePair] | None = None

    parents_raw: strawberry.Private[list | None] = None

    @relay.connection(TaskRelationsConnection)
    def parents(self, info: Info) -> list[TaskTaskRelation]:
        return build_task_parents(self.pk, self.parents_raw or [])
