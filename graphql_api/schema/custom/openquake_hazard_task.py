"""
This module contains the schema definitions used by NSHM Rupture Generation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema,
 which is generated automatically by Graphene.

The core class OpenquakeHazardTask implements the `graphql_api.schema.task.Task` Interface.

"""

import logging
from datetime import datetime as dt

import graphene
from graphene import relay
from graphql_relay import from_global_id

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
from .common import ModelType, OpenquakeTaskType
from .helpers import resolve_node
from .openquake_hazard_config import OpenquakeHazardConfig
from .openquake_hazard_solution import OpenquakeHazardSolution

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

log = logging.getLogger(__name__)


class OpenquakeHazardTask(graphene.ObjectType, AutomationTaskBase):
    """An OpenquakeHazardTask in the NSHM process"""

    class Meta:
        interfaces = (relay.Node, Thing, AutomationTaskInterface)

    config = graphene.Field(
        OpenquakeHazardConfig,
        description="The task configuration",
        required=False,
        deprecation_reason="We no longer store this value.",
    )
    hazard_solution = graphene.Field(OpenquakeHazardSolution, description="The openquake solution")

    model_type = ModelType()
    task_type = OpenquakeTaskType()

    @staticmethod
    def from_json(jsondata):
        return OpenquakeHazardTask(**AutomationTaskBase.from_json(jsondata))

    def resolve_config(root, info, **args):
        return resolve_node(root, info, 'config', 'thing')

    def resolve_hazard_solution(root, info, **args):
        return resolve_node(root, info, 'hazard_solution', 'thing')

    def resolve_task_type(root, info, **args):
        if task_type := root.task_type:
            return task_type
        return OpenquakeTaskType.UNDEFINED


# class OpenquakeHazardTaskConnection(relay.Connection):
#     """A list of OpenquakeHazardTask items"""
#     class Meta:
#         node = OpenquakeHazardTask

#     total_count = graphene.Int()

#     @staticmethod
#     def resolve_total_count(root, info, *args, **kwargs):
#         return len(root.edges)


class OpenquakeHazardTaskInput(AutomationTaskInput):
    # we're keeping this in here so that we can create old-fashioned entries for tests to ensure we can still read them
    config = graphene.Field(graphene.ID, required=False, deprecation_reason="We no longer store this config")
    model_type = ModelType(required=True)
    task_type = OpenquakeTaskType(default_value=OpenquakeTaskType.HAZARD)


class CreateOpenquakeHazardTask(graphene.Mutation):
    class Arguments:
        input = OpenquakeHazardTaskInput(required=True)

    ok = graphene.Boolean()
    openquake_hazard_task = graphene.Field(OpenquakeHazardTask)

    @classmethod
    def mutate(cls, root, info, input):
        t0 = dt.utcnow()
        log.info(f"CreateOpenquakeHazardTask.mutate payload: {input}")
        if input.config:
            # Validation!
            input_type, nid = from_global_id(input.config)
            assert input_type == "OpenquakeHazardConfig"

            ref = get_data_manager().thing.get_one(nid)
            log.debug(f"Got a ref to a real thing: {ref} with thing id: {nid}")
            if not ref:
                raise Exception("Broken input")
        openquake_hazard_task = get_data_manager().thing.create('OpenquakeHazardTask', **input)
        db_metrics.put_duration(__name__, 'CreateOpenquakeHazardTask.mutate', dt.utcnow() - t0)
        return CreateOpenquakeHazardTask(openquake_hazard_task=openquake_hazard_task)


class OpenquakeHazardTaskUpdateInput(AutomationTaskUpdateInput):
    hazard_solution = graphene.ID()


class UpdateOpenquakeHazardTask(graphene.Mutation):
    class Arguments:
        input = OpenquakeHazardTaskUpdateInput()

    ok = graphene.Boolean()
    openquake_hazard_task = graphene.Field(OpenquakeHazardTask)

    @classmethod
    def mutate(cls, root, info, input):
        t0 = dt.utcnow()
        log.debug(f"UpdateOpenquakeHazardTask.mutate payload: {input}")
        thing_id = input.pop('task_id')

        openquake_hazard_task = get_data_manager().thing.update('OpenquakeHazardTask', thing_id, **input)
        db_metrics.put_duration(__name__, 'UpdateOpenquakeHazardTask.mutate', dt.utcnow() - t0)
        return UpdateOpenquakeHazardTask(openquake_hazard_task=openquake_hazard_task, ok=True)
