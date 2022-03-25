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
from .openquake_hazard_config import OpenquakeHazardConfig
from .helpers import resolve_node

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)

logger = logging.getLogger(__name__)

class OpenquakeHazardTask(graphene.ObjectType, AutomationTaskBase):
    """An OpenquakeHazardTask in the NSHM process"""
    class Meta:
        interfaces = (relay.Node, Thing, AutomationTaskInterface)

    config = graphene.Field(OpenquakeHazardConfig, description = "The task configuration")

    @staticmethod
    def from_json(jsondata):
        return OpenquakeHazardTask(**AutomationTaskBase.from_json(jsondata))

    def resolve_config(root, info, **args):
        return resolve_node(root, info, 'config', 'thing')

# class OpenquakeHazardTaskConnection(relay.Connection):
#     """A list of OpenquakeHazardTask items"""
#     class Meta:
#         node = OpenquakeHazardTask

#     total_count = graphene.Int()

#     @staticmethod
#     def resolve_total_count(root, info, *args, **kwargs):
#         return len(root.edges)

class CreateOpenquakeHazardTask(relay.ClientIDMutation):
    class Input:
        config = graphene.ID()
        created = AutomationTaskInterface.created

    ok = graphene.Boolean()
    openquake_hazard_task = graphene.Field(OpenquakeHazardTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        logger.debug(f"payload: {kwargs}")
        openquake_hazard_task = get_data_manager().thing.create('OpenquakeHazardTask', **kwargs)
        db_metrics.put_duration(__name__, 'CreateOpenquakeHazardTask.mutate_and_get_payload' , dt.utcnow()-t0)
        return CreateOpenquakeHazardTask(openquake_hazard_task=openquake_hazard_task)

class UpdateOpenquakeHazardTask(relay.ClientIDMutation):
    class Input:
        # config = = graphene.ID()
        # created = AutomationTaskBase.created
        pass

    ok = graphene.Boolean()
    task_result = graphene.Field(OpenquakeHazardTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        logger.debug(f"payload: {kwargs}")
        thing_id = input.pop('task_id')
        task_result = get_data_manager().thing.update('OpenquakeHazardTask', thing_id, **input)
        db_metrics.put_duration(__name__, 'UpdateOpenquakeHazardTask.mutate_and_get_payload' , dt.utcnow()-t0)
        return UpdateOpenquakeHazardTask(task_result=task_result)