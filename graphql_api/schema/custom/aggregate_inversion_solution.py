#!python3
"""
This module contains the schema definition for a AggregateInversionSolution.

"""
import copy
import logging
from datetime import datetime as dt

import graphene
from graphene import relay
from graphql_relay import from_global_id

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.schema.file import CreateFile, File, FileInterface

from .common import AggregationFn, PredecessorsInterface
from .helpers import resolve_node
from .inversion_solution import InversionSolutionInterface

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

log = logging.getLogger(__name__)


class AggregateInversionSolution(graphene.ObjectType):
    """
    Represents a Aggregate Inversion Solution file produced fby applying the
    aggregate_fn to the rates of each source solution.
    """

    class Meta:
        interfaces = (relay.Node, FileInterface, PredecessorsInterface, InversionSolutionInterface)

    common_rupture_set = graphene.Field(File)
    source_solutions = graphene.List(
        'graphql_api.schema.custom.source_solution_union.SourceSolutionUnion',
        description="The solutions used to build the aggregate",
    )
    aggregation_fn = graphene.Field(AggregationFn, description="aggregation function on rupture rates.")

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().file.get_one(_id, "AggregateInversionSolution")
        return node

    def resolve_source_solutions(root, info, **args):
        for ssid in root.source_solutions:
            _type, nid = from_global_id(ssid)
            yield get_data_manager().file.get_one(nid)

    def resolve_common_rupture_set(root, info, **args):
        return resolve_node(root, info, 'common_rupture_set', 'file')


class CreateAggregateInversionSolution(relay.ClientIDMutation):
    """
    Create a AggregateInversionSolution file
    """

    class Input:
        common_rupture_set = graphene.ID(
            required=True,
            description='ID of common rupture set. Aggregations must use solutions based on the same rupture set.',
        )
        source_solutions = graphene.List(
            graphene.ID, required=True, description="The solutions used to build the aggregate"
        )
        aggregation_fn = graphene.Field(
            AggregationFn, required=True, description="aggregation function on rupture rates."
        )

        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta

        produced_by = graphene.ID()
        created = graphene.DateTime(description="When the solution was created")
        predecessors = graphene.List(
            'graphql_api.schema.custom.predecessor.PredecessorInput', required=False, description="list of predecessors"
        )

    solution = graphene.Field(AggregateInversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        log.info(f"CreateAggregateInversionSolution mutate_and_get_payload {kwargs}")

        json_ready_input = copy.copy(kwargs)

        for fld in ['aggregation_fn']:
            json_ready_input[fld] = json_ready_input[fld].value

        solution = get_data_manager().file.create('AggregateInversionSolution', **json_ready_input)
        db_metrics.put_duration(__name__, 'CreateAggregateInversionSolution.mutate_and_get_payload', dt.utcnow() - t0)
        return CreateAggregateInversionSolution(solution=solution, ok=True)
