import graphene
from graphene import relay
from graphene import Enum
from graphql_relay import from_global_id

from graphql_api.data import get_data_manager
from graphql_api.schema.custom import (GeneralTask, RuptureGenerationTask, AutomationTask)

from datetime import datetime as dt
from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)

class ChildTaskUnion(graphene.Union):
    class Meta:
        types = (GeneralTask, RuptureGenerationTask, AutomationTask)

class TaskTaskRelation(graphene.ObjectType):

    # class Meta:
    #     interfaces = (relay.Node, )

    parent = graphene.Field(GeneralTask, required=False)
    child = graphene.Field(ChildTaskUnion, required=False)
    
    parent_id = graphene.String()
    child_id = graphene.String()
    
    @staticmethod
    def resolve_parent(root, info, *args, **kwargs):
        if not root.parents:
            return []
        return [get_data_manager().thing.get_one(parent.parent_id) for parent in root.parents]

    @staticmethod
    def resolve_child(root, info, *args, **kwargs):
        return get_data_manager().thing.get_one(root.id)

class TaskTaskRelationConnection(relay.Connection):
    class Meta:
        node = TaskTaskRelation

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)

class CreateTaskTaskRelation(graphene.Mutation):
    class Arguments:
        parent_id = graphene.ID(required=True)
        child_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    thing_relation = graphene.Field(TaskTaskRelation)

    def mutate(self, info, **kwargs):
        t0 = dt.utcnow()
        print("CreateTaskTaskRelation.mutate: ", kwargs)
        parent_type, parent_id = from_global_id(kwargs.pop('parent_id'))
        child_type, child_id = from_global_id(kwargs.pop('child_id'))
        thing_relation = get_data_manager().thing_relation.create(parent_type, child_type, parent_id, child_id, **kwargs)
        db_metrics.put_duration(__name__, 'CreateTaskTaskRelation.mutate' , dt.utcnow()-t0)
        return CreateTaskTaskRelation(ok=True, thing_relation=thing_relation)
