"""
Module entry point
"""
from graphql_api.schema.custom import SmsFile, StrongMotionStation
from graphql_api.schema.custom.aggregate_inversion_solution import (
    AggregateInversionSolution,
    CreateAggregateInversionSolution,
)
from graphql_api.schema.custom.automation_task import AutomationTask, CreateAutomationTask, UpdateAutomationTask
from graphql_api.schema.custom.general_task import GeneralTask
from graphql_api.schema.custom.inversion_solution import CreateInversionSolution, InversionSolution
from graphql_api.schema.custom.inversion_solution_nrml import CreateInversionSolutionNrml, InversionSolutionNrml
from graphql_api.schema.custom.openquake_hazard_config import CreateOpenquakeHazardConfig, OpenquakeHazardConfig
from graphql_api.schema.custom.openquake_hazard_solution import CreateOpenquakeHazardSolution, OpenquakeHazardSolution
from graphql_api.schema.custom.openquake_hazard_task import CreateOpenquakeHazardTask, OpenquakeHazardTask
from graphql_api.schema.custom.rupture_generation_task import (
    CreateRuptureGenerationTask,
    RuptureGenerationTask,
    RuptureGenerationTaskConnection,
)
from graphql_api.schema.custom.scaled_inversion_solution import CreateScaledInversionSolution, ScaledInversionSolution
from graphql_api.schema.custom.time_dependent_inversion_solution import (
    CreateTimeDependentInversionSolution,
    TimeDependentInversionSolution,
)
from graphql_api.schema.event import EventResult, EventState
from graphql_api.schema.file import CreateFile, File, FileConnection
from graphql_api.schema.file_relation import FileRelation
from graphql_api.schema.schema import root_schema
from graphql_api.schema.search_manager import SearchManager
from graphql_api.schema.table import Table
from graphql_api.schema.task_task_relation import TaskTaskRelation
from graphql_api.schema.thing import Thing, ThingConnection
