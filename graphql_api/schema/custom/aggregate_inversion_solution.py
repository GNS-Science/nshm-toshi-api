#!python3
"""
This module contains the schema definition for a AggregateInversionSolution.

"""
import graphene
from graphene import relay
from datetime import datetime as dt

from graphql_relay import from_global_id
from graphql_api.data import get_data_manager
from graphql_api.schema.file import FileInterface, CreateFile
from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

from .common import PredecessorsInterface, AggregationFn
from .helpers import resolve_node
from .automation_task import AutomationTask
from .inversion_solution import InversionSolutionInterface


db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration",
    resolution=CW_METRICS_RESOLUTION)


class AggregateInversionSolution(graphene.ObjectType):
    """
    Represents a Aggregate Inversion Solution file produced fby applying the 
    aggregate_fn to the rates of each source solution. 
    """
    class Meta:
        interfaces = (relay.Node, FileInterface, PredecessorsInterface, InversionSolutionInterface)

    common_rupture_set = graphene.ID(
        description='aggregations must use solutions based on the saem rupture set.')
    source_solutions = graphene.List('graphql_api.schema.custom.inversion_solution_nrml.SourceSolutionUnion',
        description="The solutions used to build the aggregate")
    aggregation_fn = graphene.Field(AggregationFn, 
        description="aggregation function on rupture rates.")

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
        common_rupture_set = AggregateInversionSolution.common_rupture_set
        source_solutions = graphene.List(graphene.ID)
        aggregation_fn = AggregateInversionSolution.aggregation_fn
        
        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta
        
        produced_by = graphene.ID()
        created = graphene.DateTime(description="When the solution was created")
        predecessors = graphene.List('graphql_api.schema.custom.predecessor.PredecessorInput',
            required=False, description="list of predecessors")

    solution = graphene.Field(AggregateInversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        solution = get_data_manager().file.create('AggregateInversionSolution', **kwargs)
        db_metrics.put_duration(__name__, 'CreateAggregateInversionSolution.mutate_and_get_payload' , dt.utcnow()-t0)
        return CreateAggregateInversionSolution(solution=solution, ok=True)
