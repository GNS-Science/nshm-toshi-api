"""
This module contains the schema definitions used by NSHM Rupture Generation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

The core class RuptureGenNewTask implements the `graphql_api.schema.task.Task` Interface.

"""


import graphene
import datetime as dt
import logging

from graphene import relay
from graphene import Enum
# from benedict import benedict


from graphql_api.schema.event import EventResult, EventState
from graphql_api.schema.thing import Thing
from graphql_api.data_s3 import get_data_manager
from .common import GitReferencesInput, GitReferencesOutput, KeyValuePair

logger = logging.getLogger(__name__)


# class RuptureGenerationArgsInput(RuptureGenerationArgs, graphene.InputObjectType):
#     """Arguments passed into the opensha Rupture Generator"""

# class RuptureGenerationArgsOutput(RuptureGenerationArgs, graphene.ObjectType):
#     """Arguments passed into the opensha Rupture Generator"""


# class RuptureGenerationMetrics():
#     """output metrics from the opensha Rupture Generator"""

# class RuptureGenerationMetricsInput(RuptureGenerationMetrics, graphene.InputObjectType):
#     """The metrics returned from the opensha Rupture Generator"""

# class RuptureGenerationMetricsOutput(RuptureGenerationMetrics, graphene.ObjectType):
#     """The metrics returned from the opensha Rupture Generator"""

class RuptureGenNewTask(graphene.ObjectType):
    """An RuptureGenNewTask in the NSHM process"""
    class Meta:
        interfaces = (relay.Node, Thing)

    result = EventResult()
    state = EventState()

    created = graphene.DateTime(description="The time the event was created")
    duration = graphene.Float(description="the final duraton of the event in seconds")

    parents = relay.ConnectionField(
        'graphql_api.schema.task_task_relation.TaskTaskRelationConnection',
        description="parent task(s) of this task")

    arguments = graphene.List(KeyValuePair)
    rupture_count = graphene.Int(description="Count of ruptures produced.")
    git_refs = graphene.Field(GitReferencesOutput)

    def resolve_parents(self, info, **args):
        # Transform the instance thing_ids into real instances
        if not self.parents: return []
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
        return RuptureGenNewTask(**jsondata)

class RuptureGenNewTaskConnection(relay.Connection):
    """A list of RuptureGenNewTask items"""
    class Meta:
        node = RuptureGenNewTask

class CreateRuptureGenNewTask(relay.ClientIDMutation):
    class Input:
        result = EventResult(required=True)
        state = EventState(required=True)
        created = graphene.DateTime(required=True, description="The time the task was created", )
        duration = graphene.Float(description="The final duraton of the task in seconds")

        arguments = graphene.List(KeyValuePair, description="input arguments for the Rupture generator")
        rupture_count = graphene.Int(description="Count of ruptures produced.")

        metrics = RuptureGenerationMetricsInput(description="The metrics from rupture generation")
        git_refs = GitReferencesInput(description="The git references for the software")

    task_result = graphene.Field(RuptureGenNewTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        task_result = get_data_manager().thing.create('RuptureGenNewTask', **kwargs)
        return CreateRuptureGenNewTask(task_result=task_result)


class UpdateRuptureGenNewTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)
        result = EventResult(required=False)
        state = EventState(required=False)
        created = graphene.DateTime(required=False, description="The time the task was created")
        duration = graphene.Float(required=False, description="The final duraton of the task in seconds")
        
        arguments = graphene.List(KeyValuePair, required=False, description="input arguments for the Rupture generator")
        rupture_count = graphene.Int(description="Count of ruptures produced.")
        metrics = RuptureGenerationMetricsInput(required=False, description="The metrics from rupture generation")
        git_refs = GitReferencesInput(description="The git references for the software")

    task_result = graphene.Field(RuptureGenNewTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        thing_id = kwargs.pop('task_id')
        task_result = get_data_manager().thing.update('RuptureGenNewTask', thing_id, **kwargs)

        return UpdateRuptureGenNewTask(task_result=task_result)