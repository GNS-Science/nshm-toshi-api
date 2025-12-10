"""
DEPRECATED - use AutomationTask instead.

This module contains the schema definitions used by NSHM Rupture Generation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql
schema, which is generated automatically by Graphene.

The core class RuptureGenerationTask implements the `graphql_api.schema.task.Task` Interface.

"""

import logging

import graphene
from graphene import relay

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.schema.thing import Thing

from .automation_task_base import AutomationTaskBase, AutomationTaskInterface

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

log = logging.getLogger(__name__)


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
