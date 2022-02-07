"""
This module contains the schema definitions used by NSHM Rupture Generation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

The core class RuptureGenerationTask implements the `graphql_api.schema.task.Task` Interface.

"""

import graphene
import datetime as dt
import logging

from graphene import relay
from graphene import Enum

from graphql_api.schema.event import EventResult, EventState
from graphql_api.schema.thing import Thing
from graphql_api.data_s3 import get_data_manager
from .common import KeyValuePair, KeyValuePairInput
from .automation_task_base import AutomationTaskInterface, AutomationTaskBase, AutomationTaskInput, AutomationTaskUpdateInput

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
        print("payload: ", input)
        task_result = get_data_manager().thing.create('RuptureGenerationTask', **input)
        return CreateRuptureGenerationTask(task_result=task_result)

class UpdateRuptureGenerationTask(graphene.Mutation):
    class Arguments:
        input = AutomationTaskUpdateInput(required=True)

    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate(cls, root, info, input):
        print("mutate: ", input)
        thing_id = input.pop('task_id')
        task_result = get_data_manager().thing.update('RuptureGenerationTask', thing_id, **input)

        return UpdateRuptureGenerationTask(task_result=task_result)