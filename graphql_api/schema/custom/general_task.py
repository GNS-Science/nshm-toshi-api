"""
This module contains the schema definition for a GeneralTask.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.


  - related files (with reader/writer role) (from thing)
    agent_name: the name of the person or process responsible for the task
    title
    description
    created
"""
import graphene
from graphene import relay
from graphql_api.schema.thing import Thing
from graphql_api.data_s3 import get_data_manager

class GeneralTask(graphene.ObjectType):
    """
    A General Task capture metadata and related inputs/outputs for arbitrary tasks
    that may not happen often enough to justify automation and/or a custom schema type.
    """
    class Meta:
        interfaces = (relay.Node, Thing)

    created = graphene.DateTime(description="When the task record was created", )
    updated = graphene.DateTime(description="When the task record was last updated", )
    agent_name = graphene.String(description='The name of the person or process responsible for the task')
    title = graphene.String(description='A title always helps')
    description = graphene.String(description='Some description of the task, potentially Markdown')

    children = relay.ConnectionField(
        'graphql_api.schema.task_task_relation.TaskTaskRelationConnection', description="sub-tasks of this task")

    parents = relay.ConnectionField(
        'graphql_api.schema.task_task_relation.TaskTaskRelationConnection',
        description="parent task(s) of this task")

    def resolve_children(self, info, **args):
        # Transform the instance thing_ids into real instances
        if not self.children: return []
        return [get_data_manager().thing_relation.get_one(_id) for _id in self.children]

    def resolve_parents(self, info, **args):
        # Transform the instance thing_ids into real instances
        if not self.parents: return []
        return [get_data_manager().thing_relation.get_one(_id) for _id in self.parents]

class GeneralTaskConnection(relay.Connection):
    """A list of GeneralTask items"""
    class Meta:
        node = GeneralTask

class CreateGeneralTask(relay.ClientIDMutation):
    class Input:
        created = graphene.DateTime(description="When the taskrecord was created", )
        updated = graphene.DateTime(description="When task was updated", )
        agent_name = graphene.String(description='The name of the person or process responsible for the task')
        title = graphene.String(description='A title always helps')
        description = graphene.String(description='Some description of the task, potentially Markdown')

    general_task = graphene.Field(GeneralTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        general_task = get_data_manager().thing.create('GeneralTask', **kwargs)
        return CreateGeneralTask(general_task=general_task)
