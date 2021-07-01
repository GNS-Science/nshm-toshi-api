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

logger = logging.getLogger(__name__)


class RuptureGenerationTask(graphene.ObjectType):
    """An RuptureGenerationTask in the NSHM process"""
    class Meta:
        interfaces = (relay.Node, Thing)

    result = EventResult()
    state = EventState()

    created = graphene.DateTime(description="The time the event was created")
    duration = graphene.Float(description="the final duraton of the event in seconds")

    parents = relay.ConnectionField(
        'graphql_api.schema.task_task_relation.TaskTaskRelationConnection',
        description="parent task(s) of this task")

    arguments = graphene.List(KeyValuePair, required=False,
        description="input arguments for the rupture generation task, as a list of Key Value pairs.")
    environment = graphene.List(KeyValuePair, required=False,
        description="execution environment details, as a list of Key Value pairs.")
    metrics = graphene.List(KeyValuePair, required=False,
        description="result metrics from the task, as a list of Key Value pairs.")


    def resolve_parents(self, info, **args):
        # Transform the instance thing_ids into real instances
        if not self.parents: return []
        if len(info.field_asts[0].selection_set.selections)==1:
            if info.field_asts[0].selection_set.selections[0].name.value == 'total_count':
                from graphql_api.schema.task_task_relation import TaskTaskRelationConnection
                return TaskTaskRelationConnection(edges=[None for x in range(len(self.parents))])
        return [get_data_manager().thing_relation.get_one(_id) for _id in self.parents]

    @classmethod
    def get_node(cls, info, _id):
        return  get_data_manager().thing.get_one(_id)

    @staticmethod
    def from_json(jsondata):
        #Field type transforms...
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.datetime.fromisoformat(started)
        return RuptureGenerationTask(**jsondata)

class RuptureGenerationTaskConnection(relay.Connection):
    """A list of RuptureGenerationTask items"""
    class Meta:
        node = RuptureGenerationTask

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)


class CreateRuptureGenerationTask(relay.ClientIDMutation):
    class Input:
        result = EventResult(required=True)
        state = EventState(required=True)
        created = graphene.DateTime(required=True, description="The time the task was created", )
        duration = graphene.Float(description="The final duraton of the task in seconds")

        arguments = graphene.List(KeyValuePairInput, required=False,
            description="input arguments for the rupture generation task, as a list of Key Value pairs.")
        environment = graphene.List(KeyValuePairInput, required=False,
            description="execution environment details, as a list of Key Value pairs.")
        metrics = graphene.List(KeyValuePairInput, required=False,
            description="result metrics from the task, as a list of Key Value pairs.")


    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        task_result = get_data_manager().thing.create('RuptureGenerationTask', **kwargs)
        return CreateRuptureGenerationTask(task_result=task_result)


class UpdateRuptureGenerationTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)
        result = EventResult(required=False)
        state = EventState(required=False)
        created = graphene.DateTime(required=False,
            description="The time the task was created")
        duration = graphene.Float(required=False,
            description="The final duraton of the task in seconds")

        arguments = graphene.List(KeyValuePairInput, required=False,
            description="input arguments for the rupture generation task, as a list of Key Value pairs.")
        environment = graphene.List(KeyValuePairInput, required=False,
            description="execution environment details, as a list of Key Value pairs.")
        metrics = graphene.List(KeyValuePairInput, required=False,
            description="result metrics from the task, as a list of Key Value pairs.")

    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        thing_id = kwargs.pop('task_id')
        task_result = get_data_manager().thing.update('RuptureGenerationTask', thing_id, **kwargs)

        return UpdateRuptureGenerationTask(task_result=task_result)