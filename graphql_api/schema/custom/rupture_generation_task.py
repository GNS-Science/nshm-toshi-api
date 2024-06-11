"""
This module contains the schema definitions used by NSHM Rupture Generation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql
schema, which is generated automatically by Graphene.

The core class RuptureGenerationTask implements the `graphql_api.schema.task.Task` Interface.

"""

import logging
from datetime import datetime as dt

import graphene
from graphene import relay

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.schema.thing import Thing

from .automation_task_base import (
    AutomationTaskBase,
    AutomationTaskInput,
    AutomationTaskInterface,
    AutomationTaskUpdateInput,
)

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

logger = logging.getLogger(__name__)


class RuptureGenerationTask(graphene.ObjectType, AutomationTaskBase):
    """An RuptureGenerationTask in the NSHM process"""

    class Meta:
        interfaces = (relay.Node, Thing, AutomationTaskInterface)

    @staticmethod
    def from_json(jsondata):
        return RuptureGenerationTask(**AutomationTaskBase.from_json(jsondata))


class RuptureGenerationTaskConnection(relay.Connection):
    """A list of RuptureGenerationTask items"""

    class Meta:
        node = RuptureGenerationTask

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)


class CreateRuptureGenerationTask(graphene.Mutation):
    class Arguments:
        input = AutomationTaskInput(required=True)

    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate(cls, root, info, input):
        t0 = dt.utcnow()
        print("payload: ", input)
        task_result = get_data_manager().thing.create('RuptureGenerationTask', **input)
        db_metrics.put_duration(__name__, 'CreateRuptureGenerationTask.mutate_and_get_payload', dt.utcnow() - t0)
        return CreateRuptureGenerationTask(task_result=task_result)


class UpdateRuptureGenerationTask(graphene.Mutation):
    class Arguments:
        input = AutomationTaskUpdateInput(required=True)

    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate(cls, root, info, input):
        t0 = dt.utcnow()
        print("mutate: ", input)
        thing_id = input.pop('task_id')
        task_result = get_data_manager().thing.update('RuptureGenerationTask', thing_id, **input)
        db_metrics.put_duration(__name__, 'UpdateRuptureGenerationTask.mutate_and_get_payload', dt.utcnow() - t0)
        return UpdateRuptureGenerationTask(task_result=task_result)
