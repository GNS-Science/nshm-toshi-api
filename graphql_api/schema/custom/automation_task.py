"""
This module contains the schema definitions used by NSHM Automation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

The core class AutomationTask implements the `graphql_api.schema.task.Task` Interface.

"""

import graphene
import datetime as dt
import logging

from graphene import relay
from graphene import Enum

from graphql_api.schema.event import EventResult, EventState
from graphql_api.schema.thing import Thing
from graphql_api.data_s3 import get_data_manager

from .common import KeyValuePair, KeyValuePairInput, TaskSubType, ModelType
from .automation_task_base import AutomationTaskInterface, AutomationTaskBase, AutomationTaskInput, AutomationTaskUpdateInput

logger = logging.getLogger(__name__)

class AutomationTask(graphene.ObjectType, AutomationTaskBase):
    """An AutomationTask in the NSHM process"""
    class Meta:
        interfaces = (relay.Node, Thing, AutomationTaskInterface)

    model_type = ModelType()
    task_type = TaskSubType()

    @staticmethod
    def from_json(jsondata):
        return AutomationTask(**AutomationTaskBase.from_json(jsondata))

class AutomationTaskConnection(relay.Connection):
    """A list of AutomationTask items"""
    class Meta:
        node = AutomationTask


    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)


class NewAutomationTaskInput(AutomationTaskInput):
    model_type = ModelType(required=False)
    task_type = TaskSubType(required=True)

class CreateAutomationTask(graphene.Mutation):
    class Arguments:
        input = NewAutomationTaskInput(required=True)

    task_result = graphene.Field(AutomationTask)

    @classmethod
    def mutate(cls, root, info, input):
        print("payload: ", input)
        task_result = get_data_manager().thing.create('AutomationTask', **input)
        return CreateAutomationTask(task_result=task_result)

class UpdateAutomationTask(graphene.Mutation):
    class Arguments:
        input = AutomationTaskUpdateInput(required=True)

    task_result = graphene.Field(AutomationTask)

    @classmethod
    def mutate(cls, root, info, input):
        print("mutate: ", input)
        thing_id = input.pop('task_id')
        task_result = get_data_manager().thing.update('AutomationTask', thing_id, **input)

        return UpdateAutomationTask(task_result=task_result)