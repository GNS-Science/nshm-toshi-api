"""
This module contains the schema definitions used by NSHM Automation task interfaces.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

"""

import graphene
import datetime as dt
import logging

from graphene import relay
# from graphene import Enum

from graphql_api.schema.event import EventResult, EventState
# from graphql_api.schema.thing import Thing
from graphql_api.data_s3 import get_data_manager
from .common import KeyValuePair, KeyValuePairInput, TaskSubType, ModelType

logger = logging.getLogger(__name__)

class AutomationTaskBase():

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
        return jsondata


class AutomationTask(graphene.Interface):
    """An AutomationTask in the NSHM process"""
    result = EventResult()
    state = EventState()

    created = graphene.DateTime(description="The time the event was created")
    duration = graphene.Float(description="the final duration of the event in seconds")

    parents = relay.ConnectionField(
        'graphql_api.schema.task_task_relation.TaskTaskRelationConnection',
        description="parent task(s) of this task")

    arguments = graphene.List(KeyValuePair, required=False,
        description="input arguments for the rupture generation task, as a list of Key Value pairs.")
    environment = graphene.List(KeyValuePair, required=False,
        description="execution environment details, as a list of Key Value pairs.")
    metrics = graphene.List(KeyValuePair, required=False,
        description="result metrics from the task, as a list of Key Value pairs.")

class AutomationTaskInput(graphene.InputObjectType):
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

class AutomationTaskUpdateInput(graphene.InputObjectType):
    task_id = graphene.ID(required=True)
    result =  EventResult()
    state = EventState()
    duration = graphene.Float(description="The final duraton of the task in seconds")

    arguments = graphene.List(KeyValuePairInput, required=False,
        description="input arguments for the rupture generation task, as a list of Key Value pairs.")
    environment = graphene.List(KeyValuePairInput, required=False,
        description="execution environment details, as a list of Key Value pairs.")
    metrics = graphene.List(KeyValuePairInput, required=False,
        description="result metrics from the task, as a list of Key Value pairs.")