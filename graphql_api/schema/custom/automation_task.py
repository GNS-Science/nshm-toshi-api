"""
This module contains the schema definitions used by NSHM Automation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema,
which is generated automatically by Graphene.

The core class AutomationTask implements the `graphql_api.schema.task.Task` Interface.

"""

import logging
from datetime import datetime as dt

import graphene
from graphene import relay

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager

# from .inversion_solution import InversionSolution
from graphql_api.schema.file_relation import FileRole
from graphql_api.schema.thing import Thing

from .automation_task_base import (
    AutomationTaskBase,
    AutomationTaskInput,
    AutomationTaskInterface,
    AutomationTaskUpdateInput,
)
from .common import ModelType, TaskSubType

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

log = logging.getLogger(__name__)


class AutomationTask(graphene.ObjectType, AutomationTaskBase):
    """An AutomationTask in the NSHM process"""

    class Meta:
        interfaces = (relay.Node, Thing, AutomationTaskInterface)

    model_type = ModelType()
    task_type = TaskSubType()
    inversion_solution = graphene.Field(
        'graphql_api.schema.custom.inversion_solution_union.InversionSolutionUnion',
        description="the result of this task. NB only available for task_types:"
        "INVERSION, SCALE_SOLUTION, AGGREGATE_SOLUTION, TIME_DEPENDENT_SOLUTION.",
    )

    @staticmethod
    def from_json(jsondata):
        return AutomationTask(**AutomationTaskBase.from_json(jsondata))

    @staticmethod
    def resolve_inversion_solution(root, info, **args):

        log.info(f"resolve_inversion_solution {root.task_type}")
        resolvable_types = [
            TaskSubType.INVERSION.value,
            TaskSubType.SCALE_SOLUTION.value,
            TaskSubType.AGGREGATE_SOLUTION.value,
            TaskSubType.TIME_DEPENDENT_SOLUTION.value,
        ]

        if not len(root.files):
            return
        if root.task_type not in resolvable_types:
            log.info(f"Cannot resove inversion_soluton for {root.task_type}")
            return

        t0 = dt.utcnow()
        res = None

        # TODO this is an ugly hack....
        #  - It gets the inversion solution by traversing the file_relations until it finds
        #     an InversionSolution subtype.
        #  - Instead this attribute needs to be a first-class one-to-one relationship
        for file_id in root.files:
            if isinstance(file_id, dict):  # new form, files is list of objects
                if not file_id['file_role'] == FileRole.WRITE.value:
                    continue
                file_relation = get_data_manager().file_relation.build_one(
                    file_id['file_id'], root.id, file_id['file_role']
                )
            else:  # old form, files is list of strings
                file_relation = get_data_manager().file_relation.get_one(file_id)
                if not file_relation.role == FileRole.WRITE.value:
                    continue
            file = get_data_manager().file.get_one(file_relation.file_id)
            if 'InversionSolution' in file.__class__.__name__:
                res = file
                log.info(f"resolved inversion_solution file {file}")
                break

        db_metrics.put_duration(__name__, 'AutomationTask.resolve_inversion_solution', dt.utcnow() - t0)
        return res


class AutomationTaskConnection(relay.Connection):
    """A list of AutomationTask items"""

    class Meta:
        node = AutomationTask

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)


class NewAutomationTaskInput(AutomationTaskInput):
    model_type = graphene.Field(ModelType, required=False)
    task_type = graphene.Field(TaskSubType, required=True)


class CreateAutomationTask(graphene.Mutation):
    class Arguments:
        input = NewAutomationTaskInput(required=True)

    task_result = graphene.Field(AutomationTask)

    @classmethod
    def mutate(cls, root, info, input):
        t0 = dt.utcnow()
        task_result = get_data_manager().thing.create('AutomationTask', **input)
        log.info(f"task_result: {task_result}")
        db_metrics.put_duration(__name__, 'CreateAutomationTask.mutate', dt.utcnow() - t0)
        return CreateAutomationTask(task_result=task_result)


class UpdateAutomationTask(graphene.Mutation):
    class Arguments:
        input = AutomationTaskUpdateInput(required=True)

    task_result = graphene.Field(AutomationTask)

    @classmethod
    def mutate(cls, root, info, input):
        t0 = dt.utcnow()
        log.debug("mutate: ", input)
        thing_id = input.pop('task_id')
        task_result = get_data_manager().thing.update('AutomationTask', thing_id, **input)
        db_metrics.put_duration(__name__, 'UpdateAutomationTask.mutate', dt.utcnow() - t0)
        return UpdateAutomationTask(task_result=task_result)
