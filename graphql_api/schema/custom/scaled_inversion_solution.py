#!python3
"""
This module contains the schema definition for a ScaledInversionSolution.

"""
import graphene
from graphene import relay
from datetime import datetime as dt

from graphql_api.data import get_data_manager
from graphql_api.schema.file import FileInterface, CreateFile
from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

from .common import PredecessorsInterface
from .helpers import resolve_node
from .inversion_solution import InversionSolutionInterface

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration",
    resolution=CW_METRICS_RESOLUTION)

class ScaledInversionSolution(graphene.ObjectType):
    """
    Represents a Scaled Inversion Solution file

    NB the  arguments used to scaling this solution (relatve to the source_solution)
    should be captured as in meta field.
    """
    class Meta:
        interfaces = (relay.Node, FileInterface, PredecessorsInterface, InversionSolutionInterface)

    source_solution = graphene.Field('graphql_api.schema.custom.inversion_solution.InversionSolution',
         description="The original soloution as produced by opensha")

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().file.get_one(_id, "ScaledInversionSolution")
        return node

    def resolve_source_solution(root, info, **args):
        return resolve_node(root, info, 'source_solution', 'file')


class CreateScaledInversionSolution(relay.ClientIDMutation):
    """
    Create a ScaledInversionSolution file
    """
    class Input:
        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta
        source_solution = graphene.ID()
        produced_by = graphene.ID()
        created =  graphene.DateTime(description="When the solution was created")
        predecessors = graphene.List('graphql_api.schema.custom.predecessor.PredecessorInput', required=False, description="list of predecessors")

    solution = graphene.Field(ScaledInversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        solution = get_data_manager().file.create('ScaledInversionSolution', **kwargs)
        db_metrics.put_duration(__name__, 'CreateScaledInversionSolution.mutate_and_get_payload' , dt.utcnow()-t0)
        return CreateScaledInversionSolution(solution=solution, ok=True)
