#!python3
"""
This module contains the schema definition for a TimeDependentInversionSolution.

"""
from datetime import datetime as dt

import graphene
from graphene import relay

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.schema.file import CreateFile, FileInterface

from .common import PredecessorsInterface
from .helpers import resolve_node
from .inversion_solution import InversionSolutionInterface

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)


class TimeDependentInversionSolution(graphene.ObjectType):
    """
    Represents a TimeDependent Inversion Solution file

    NB the  arguments used to scaling this solution (relatve to the source_solution)
    should be captured as in meta field.
    """

    class Meta:
        interfaces = (relay.Node, FileInterface, PredecessorsInterface, InversionSolutionInterface)

    source_solution = graphene.Field(
        'graphql_api.schema.custom.inversion_solution.InversionSolution',
        description="The original soloution as produced by opensha",
    )

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().file.get_one(_id, "TimeDependentInversionSolution")
        return node

    def resolve_source_solution(root, info, **args):
        return resolve_node(root, info, 'source_solution', 'file')


class CreateTimeDependentInversionSolution(relay.ClientIDMutation):
    """
    Create a TimeDependentInversionSolution file
    """

    class Input:
        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta
        source_solution = graphene.ID()
        produced_by = graphene.ID()
        created = graphene.DateTime(description="When the solution was created")
        predecessors = graphene.List(
            'graphql_api.schema.custom.predecessor.PredecessorInput', required=False, description="list of predecessors"
        )

    solution = graphene.Field(TimeDependentInversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        solution = get_data_manager().file.create('TimeDependentInversionSolution', **kwargs)
        db_metrics.put_duration(
            __name__, 'CreateTimeDependentInversionSolution.mutate_and_get_payload', dt.utcnow() - t0
        )
        return CreateTimeDependentInversionSolution(solution=solution, ok=True)
