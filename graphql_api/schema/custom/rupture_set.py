#!python3
"""
This module contains the schema definition for a RuptureSet.

"""
from datetime import datetime as dt
from datetime import timezone

import graphene
from graphene import relay

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.schema.file import CreateFile, FileInterface

from .common import KeyValuePair, KeyValuePairInput
from .helpers import resolve_node

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)


class RuptureSet(graphene.ObjectType):
    """
    Represents a Scaled Inversion Solution file

    NB the  arguments used to scaling this solution (relatve to the source_solution)
    should be captured as in meta field.
    """

    class Meta:
        interfaces = (relay.Node, FileInterface)

    fault_models = graphene.List(
        graphene.String, description='a list of one or fault models used to create this rupture set.'
    )
    arguments = graphene.List(KeyValuePair, description="result metrics from the task, as a list of Key Value pairs.")
    metrics = graphene.List(KeyValuePair, description="result metrics from the task, as a list of Key Value pairs.")

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().file.get_one(_id, "RuptureSet")
        return node


class CreateRuptureSet(relay.ClientIDMutation):
    """
    Create a RuptureSet file
    """

    class Input:
        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta
        produced_by = graphene.ID()
        created = graphene.DateTime(description="When the file was created")

        fault_models = graphene.List(
            graphene.String,
            description="fasult models used to build the rupture set",
        )
        metrics = graphene.List(
            KeyValuePairInput,
            required=False,
            description="metrics from the rupture set, as a list of Key Value pairs.",
        )

        arguments = graphene.List(
            KeyValuePairInput,
            required=False,
            description="arguments used to build the rupture set, as a list of Key Value pairs.",
        )

    rupture_set = graphene.Field(RuptureSet)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.now(timezone.utc)
        rupture_set = get_data_manager().file.create('RuptureSet', **kwargs)
        db_metrics.put_duration(__name__, 'CreateRuptureSet.mutate_and_get_payload', dt.now(timezone.utc) - t0)
        return CreateRuptureSet(rupture_set=rupture_set, ok=True)
