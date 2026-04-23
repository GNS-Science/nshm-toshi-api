"""
Root schema — Query + Mutation.

Compare with graphql_api/schema/schema.py (311 lines, complex wiring).
This file achieves the same surface area for all POC types in ~120 lines.
"""
from typing import Iterable, Optional

import strawberry
from strawberry import relay

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

    @strawberry.mutation
    def create_sms_file(
        self, info: strawberry.types.Info, input: CreateSmsFileInput
    ) -> SmsFile:
        return mutate_create_sms_file(info, input)

    @strawberry.mutation
    def create_strong_motion_station(
        self, info: strawberry.types.Info, input: CreateStrongMotionStationInput
    ) -> StrongMotionStation:
        return mutate_create_strong_motion_station(info, input)

    @strawberry.mutation
    def create_automation_task(
        self, info: strawberry.types.Info, input: CreateAutomationTaskInput
    ) -> AutomationTask:
        return mutate_create_automation_task(info, input)

    @strawberry.mutation
    def create_rupture_generation_task(
        self, info: strawberry.types.Info, input: CreateAutomationTaskInput
    ) -> RuptureGenerationTask:
        return mutate_create_rupture_generation_task(info, input)

    @strawberry.mutation
    def update_rupture_generation_task(
        self, info: strawberry.types.Info, input: UpdateAutomationTaskInput
    ) -> Optional[RuptureGenerationTask]:
        return mutate_update_rupture_generation_task(info, input)

    @strawberry.mutation
    def create_file_relation(
        self, info: strawberry.types.Info, input: CreateFileRelationInput
    ) -> bool:
        return mutate_create_file_relation(info, input)

    @strawberry.mutation
    def create_task_relation(
        self, info: strawberry.types.Info, input: CreateTaskRelationInput
    ) -> TaskTaskRelation:
        return mutate_create_task_relation(info, input)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    # All relay.Node subtypes auto-discovered from the schema graph
)
