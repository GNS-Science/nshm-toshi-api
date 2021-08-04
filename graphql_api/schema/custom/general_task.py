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
from graphene import Enum
from graphql_api.schema.thing import Thing
from graphql_api.data_s3 import get_data_manager
from .common import KeyValueListPair, KeyValueListPairInput, KeyValuePair, KeyValuePairInput
from graphql_api.schema.event import EventResult

class TaskSubType(Enum):
    RUPTURE_SETS = "rupture_sets"
    INVERSIONS = "inversions"
    HAZARD = "HAZARD"

class ModelType(Enum):
    CRUSTAL = "crustal"
    SUBDUCTION = "subduction"


class ModelType(Enum):
    CRUSTAL = "crustal"
    SUBDUCTION = "subduction"


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
    argument_lists = graphene.List(KeyValueListPair,
        description="subtask arguments, as a list of Key Value List pairs.")
    swept_arguments = graphene.List(graphene.String, description='list of keys for items having >1 value in argument_lists')
    meta = graphene.List(KeyValuePair, description="arbitrary metadata for the task, as a list of Key Value pairs.")
    notes = graphene.String(description='notes about the task, potentially Markdown')

    #fields to replave the Job Control sheeet
    subtask_count = graphene.Int(description='count of subtasks')
    subtask_type = graphene.Field(TaskSubType, )
    model_type = graphene.Field(ModelType, )
    subtask_result = EventResult() #added PARTIAL option since some GT will have mixed subtask results

    #duration = graphene.Float(description="the final duration of the event in seconds")

    children = relay.ConnectionField(
        'graphql_api.schema.task_task_relation.TaskTaskRelationConnection',
        description="sub-tasks of this task")

    parents = relay.ConnectionField(
        'graphql_api.schema.task_task_relation.TaskTaskRelationConnection',
        description="parent task(s) of this task")

    def resolve_swept_arguments(self, info, **args):
        if self.argument_lists:
            for itm in self.argument_lists:
                if len(itm['v']) > 1:
                    yield itm['k']

    def resolve_children(self, info, **args):
        # Transform the instance thing_ids into real instances
        if not self.children: return []
        if len(info.field_asts[0].selection_set.selections)==1:
            if info.field_asts[0].selection_set.selections[0].name.value == 'total_count':
                from graphql_api.schema.task_task_relation import TaskTaskRelationConnection
                return TaskTaskRelationConnection(edges= [None for x in range(len(self.children))])
        return [get_data_manager().thing_relation.get_one(_id) for _id in self.children]

    def resolve_parents(self, info, **args):
        # Transform the instance thing_ids into real instances
        if not self.parents: return []
        if len(info.field_asts[0].selection_set.selections)==1:
            if info.field_asts[0].selection_set.selections[0].name.value == 'total_count':
                from graphql_api.schema.task_task_relation import TaskTaskRelationConnection
                return TaskTaskRelationConnection(edges= [None for x in range(len(self.parents))])
        return [get_data_manager().thing_relation.get_one(_id) for _id in self.parents]

    @classmethod
    def get_node(cls, info, id):
        return get_data_manager().thing.get_one(id)

class GeneralTaskConnection(relay.Connection):
    """A list of GeneralTask items"""
    class Meta:
        node = GeneralTask

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)


class CreateGeneralTask(relay.ClientIDMutation):
    class Input:
        created = graphene.DateTime(description="When the taskrecord was created", )
        updated = graphene.DateTime(description="When task was updated", )
        agent_name = graphene.String(description='The name of the person or process responsible for the task')
        title = graphene.String(description='A title always helps')
        description = graphene.String(description='Some description of the task, potentially Markdown')
        argument_lists = graphene.List(KeyValueListPairInput,
            description="subtask arguments, as a list of Key Value List pairs.")
        meta = graphene.List(KeyValuePairInput,
            description="arbitrary metadata for the task, as a list of Key Value pairs.")
        notes =  GeneralTask.notes

        subtask_count = GeneralTask.subtask_count
        subtask_type = GeneralTask.subtask_type
        model_type = GeneralTask.model_type
        subtask_result = GeneralTask.subtask_result

    general_task = graphene.Field(GeneralTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        general_task = get_data_manager().thing.create('GeneralTask', **kwargs)
        return CreateGeneralTask(general_task=general_task)
