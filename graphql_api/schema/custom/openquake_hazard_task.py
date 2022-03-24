"""
This module contains the schema definitions used by NSHM Rupture Generation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

The core class OpenquakeHazardTask implements the `graphql_api.schema.task.Task` Interface.

"""

import graphene
import datetime as dt
import logging

from graphene import relay
from graphene import Enum

from graphql_api.schema.event import EventResult, EventState
from graphql_api.schema.thing import Thing
from graphql_api.data import get_data_manager
from .common import KeyValuePair, KeyValuePairInput
from .automation_task_base import AutomationTaskInterface, AutomationTaskBase, AutomationTaskInput, AutomationTaskUpdateInput

from datetime import datetime as dt
from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)

logger = logging.getLogger(__name__)

class OpenquakeHazardTask(graphene.ObjectType, AutomationTaskBase):
    """An OpenquakeHazardTask in the NSHM process"""
    class Meta:
        interfaces = (relay.Node, Thing, AutomationTaskInterface)

    @staticmethod
    def from_json(jsondata):
        return OpenquakeHazardTask(**AutomationTaskBase.from_json(jsondata))

class OpenquakeHazardTaskConnection(relay.Connection):
    """A list of OpenquakeHazardTask items"""
    class Meta:
        node = OpenquakeHazardTask

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)

class CreateOpenquakeHazardTask(graphene.Mutation):
    class Arguments:
        input = AutomationTaskInput(required=True)

    task_result = graphene.Field(OpenquakeHazardTask)

    @classmethod
    def mutate(cls, root, info, input):
        t0 = dt.utcnow()
        print("payload: ", input)
        task_result = get_data_manager().thing.create('OpenquakeHazardTask', **input)
        db_metrics.put_duration(__name__, 'CreateOpenquakeHazardTask.mutate_and_get_payload' , dt.utcnow()-t0)
        return CreateOpenquakeHazardTask(task_result=task_result)

class UpdateOpenquakeHazardTask(graphene.Mutation):
    class Arguments:
        input = AutomationTaskUpdateInput(required=True)

    task_result = graphene.Field(OpenquakeHazardTask)

    @classmethod
    def mutate(cls, root, info, input):
        t0 = dt.utcnow()
        print("mutate: ", input)
        thing_id = input.pop('task_id')
        task_result = get_data_manager().thing.update('OpenquakeHazardTask', thing_id, **input)
        db_metrics.put_duration(__name__, 'UpdateOpenquakeHazardTask.mutate_and_get_payload' , dt.utcnow()-t0)
        return UpdateOpenquakeHazardTask(task_result=task_result)