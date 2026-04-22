"""
Root schema — Query + Mutation.

Compare with graphql_api/schema/schema.py (311 lines, complex wiring).
This file achieves the same surface area for 3 types in ~60 lines.
"""
from typing import Iterable, Optional

import strawberry
from strawberry import relay

from models.file import CreateFileInput, ToshiFile, mutate_create_file, resolve_files
from models.general_task import (
    CreateGeneralTaskInput,
    GeneralTask,
    UpdateGeneralTaskInput,
    mutate_create_general_task,
    mutate_update_general_task,
    resolve_general_tasks,
)
from models.rupture_set import (
    CreateRuptureSetInput,
    RuptureGenerationTask,
    RuptureSet,
    mutate_create_rupture_set,
    resolve_rupture_sets,
)


@strawberry.type
class Query:
    # Relay node lookup by global ID — dispatches to the correct type's resolve_node()
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


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_general_task(
        self, info: strawberry.types.Info, input: CreateGeneralTaskInput
    ) -> GeneralTask:
        return mutate_create_general_task(info, input)

    @strawberry.mutation
    def update_general_task(
        self, info: strawberry.types.Info, input: UpdateGeneralTaskInput
    ) -> Optional[GeneralTask]:
        return mutate_update_general_task(info, input)

    @strawberry.mutation
    def create_rupture_set(
        self, info: strawberry.types.Info, input: CreateRuptureSetInput
    ) -> RuptureSet:
        return mutate_create_rupture_set(info, input)

    @strawberry.mutation
    def create_file(
        self, info: strawberry.types.Info, input: CreateFileInput
    ) -> ToshiFile:
        return mutate_create_file(info, input)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    # All relay.Node subtypes auto-discovered from the schema graph
)
