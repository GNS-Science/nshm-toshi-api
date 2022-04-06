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
from graphql_relay import from_global_id
from graphene import Enum

from graphql_api.schema.event import EventResult, EventState
from graphql_api.schema.thing import Thing
from graphql_api.data import get_data_manager
from .common import ModelType
from .automation_task_base import (AutomationTaskInterface, AutomationTaskBase,
    AutomationTaskInput, AutomationTaskUpdateInput)

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
    model_type = ModelType()

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

class OpenquakeHazardTaskInput(AutomationTaskInput):
    config = graphene.ID(required=True)
    model_type = ModelType(required=True)

class CreateOpenquakeHazardTask(graphene.Mutation):

    class Arguments:
        input = OpenquakeHazardTaskInput(required=True)

    ok = graphene.Boolean()
    openquake_hazard_task = graphene.Field(OpenquakeHazardTask)

    @classmethod
    def mutate(cls, root, info, input):
        t0 = dt.utcnow()
        logger.debug(f"CreateOpenquakeHazardTask.mutate payload: {input}")
        #Validation!
        input_type, nid = from_global_id(input.config)
        assert input_type == "OpenquakeHazardConfig"
        ref = get_data_manager().thing.get_one(nid)
        logger.debug(f"Got a ref to a real thing: {ref} with thing id: {nid}")
        if not ref:
            raise Exception("Broken input")
        openquake_hazard_task = get_data_manager().thing.create('OpenquakeHazardTask', **input)
        db_metrics.put_duration(__name__, 'CreateOpenquakeHazardTask.mutate' , dt.utcnow()-t0)
        return CreateOpenquakeHazardTask(openquake_hazard_task=openquake_hazard_task)

class UpdateOpenquakeHazardTask(graphene.Mutation):
    class Arguments:
        input = AutomationTaskUpdateInput(required=True)

    ok = graphene.Boolean()
    openquake_hazard_task = graphene.Field(OpenquakeHazardTask)

    @classmethod
    def mutate(cls, root, info, input):
        t0 = dt.utcnow()
        logger.debug(f"UpdateOpenquakeHazardTask.mutate payload: {input}")
        thing_id = input.pop('task_id')
        openquake_hazard_task = get_data_manager().thing.update('OpenquakeHazardTask', thing_id, **input)
        db_metrics.put_duration(__name__, 'UpdateOpenquakeHazardTask.mutate' , dt.utcnow()-t0)
        return UpdateOpenquakeHazardTask(openquake_hazard_task=openquake_hazard_task, ok=True)
