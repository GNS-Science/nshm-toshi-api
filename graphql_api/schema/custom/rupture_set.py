#!python3
"""
This module contains the schema definition for a RuptureSet.

"""
import logging
from datetime import datetime as dt
from datetime import timezone

import graphene
from graphene import relay
from graphql_relay import from_global_id

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.schema.file import CreateFile, FileInterface

from .common import KeyValuePair, KeyValuePairInput, PredecessorsInterface
from .helpers import resolve_node

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)
log = logging.getLogger(__name__)


class RuptureSet(graphene.ObjectType):
    """
    Represents a Rupture Set file
    """

    class Meta:
        interfaces = (relay.Node, FileInterface, PredecessorsInterface)

    fault_models = graphene.List(
        graphene.String, description='a list of one or more fault models used to create this rupture set.'
    )
    metrics = graphene.List(KeyValuePair, description="metrics, as a list of Key Value pairs.")
    produced_by = graphene.Field(
        'graphql_api.schema.custom.RuptureGenerationTask', description="The task that produced this solution"
    )

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().file.get_one(_id, "RuptureSet")
        return node

    def resolve_produced_by(root, info, **args):
        return resolve_node(root, info, 'produced_by', 'thing')


class CreateRuptureSet(relay.ClientIDMutation):
    """
    Create a RuptureSet file
    """

    class Input:
        # From the FileInterface schema
        file_name = CreateFile.Arguments.file_name
        md5_digest = CreateFile.Arguments.md5_digest
        file_size = CreateFile.Arguments.file_size
        meta = CreateFile.Arguments.meta
        created = CreateFile.Arguments.created

        # from this schema
        produced_by = graphene.ID(required=True)
        fault_models = graphene.List(
            graphene.String,
            description="fault models used to build the rupture set",
        )
        metrics = graphene.List(
            KeyValuePairInput,
            required=False,
            description="rupture set metrics.",
        )

    rupture_set = graphene.Field(RuptureSet)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.now(timezone.utc)

        log.debug(f'mutate_and_get_payload: {kwargs}')
        produced_by = kwargs.get('produced_by')
        assert from_global_id(produced_by)[0] == 'RuptureGenerationTask'

        rupture_set = get_data_manager().file.create('RuptureSet', **kwargs)
        db_metrics.put_duration(__name__, 'CreateRuptureSet.mutate_and_get_payload', dt.now(timezone.utc) - t0)
        return CreateRuptureSet(rupture_set=rupture_set, ok=True)
