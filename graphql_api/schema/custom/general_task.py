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
from graphql_api.data import get_data_manager
from .common import KeyValueListPair, KeyValueListPairInput, KeyValuePair, KeyValuePairInput, TaskSubType, ModelType
from graphql_api.schema.event import EventResult

from datetime import datetime as dt
from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)

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


class UpdateGeneralTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)
        created = GeneralTask.created
        updated = GeneralTask.updated
        agent_name = GeneralTask.agent_name
        title = GeneralTask.title
        description = GeneralTask.description
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
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        #print("mutate_and_get_payload: ", kwargs)
        thing_id = kwargs.pop('task_id')
        general_task = get_data_manager().thing.update('GeneralTask', thing_id, **kwargs)
        #print("general_task", general_task.created)
        db_metrics.put_duration(__name__, 'UpdateGeneralTask.mutate_and_get_payload' , dt.utcnow()-t0)
        return UpdateGeneralTask(general_task=general_task, ok=True)
