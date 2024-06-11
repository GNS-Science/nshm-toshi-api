import logging
from datetime import datetime as dt

import graphene
from graphene import relay
from graphql_relay import from_global_id

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.schema.custom import AutomationTask, GeneralTask, OpenquakeHazardTask, RuptureGenerationTask

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

logger = logging.getLogger(__name__)


class ChildTaskUnion(graphene.Union):
    class Meta:
        types = (GeneralTask, RuptureGenerationTask, AutomationTask, OpenquakeHazardTask)


class TaskTaskRelation(graphene.ObjectType):
    parent = graphene.Field(GeneralTask, required=False)
    child = graphene.Field(ChildTaskUnion, required=False)

    parent_id = graphene.String()
    child_id = graphene.String()

    @staticmethod
    def resolve_parent(root, info, *args, **kwargs):
        # logger.debug(f'ROOT {root.parent_id} ')
        return get_data_manager().thing.get_one(root.parent_id)

    @staticmethod
    def resolve_child(root, info, *args, **kwargs):
        # logger.debug(f'ROOT {root.child_id} ')
        return get_data_manager().thing.get_one(root.child_id)


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
        logger.debug(f"CreateTaskTaskRelation.mutate: {kwargs}")
        parent_type, parent_id = from_global_id(kwargs.pop('parent_id'))
        child_type, child_id = from_global_id(kwargs.pop('child_id'))

        thing_relation = get_data_manager().thing_relation.create(
            parent_type, child_type, parent_id, child_id, **kwargs
        )
        logger.info(f"CreateTaskTaskRelation.mutate: thing_relation {thing_relation}")

        db_metrics.put_duration(__name__, 'CreateTaskTaskRelation.mutate', dt.utcnow() - t0)
        return CreateTaskTaskRelation(ok=True, thing_relation=thing_relation)
