#!python3
"""
This module contains the schema definition for InversionSolutionNrml.

"""
import graphene
from datetime import datetime as dt
from graphene import relay

from graphql_api.data import get_data_manager
from graphql_api.schema.file import FileInterface, CreateFile
# from graphql_api.schema.table import Table

from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

from .helpers import resolve_node
from .inversion_solution import InversionSolution
from .common import PredecessorsInterface

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration",
    resolution=CW_METRICS_RESOLUTION)

class InversionSolutionNrml(graphene.ObjectType):
    """
    Represents a InversionSolutionNrml archive file

    This is a zip archive containing two XML source files that have been converted from the source_solution

    NB any arguments used to generate this object should be captured as in meta field.
    """
    class Meta:
        interfaces = (relay.Node, FileInterface, PredecessorsInterface)

    created = graphene.DateTime(description="When the scaled solution file was created" )
    source_solution = graphene.Field(InversionSolution, description="The original soloution as produced by opensha")

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().file.get_one(_id, "InversionSolutionNrml")
        return node

    def resolve_source_solution(root, info, **args):
        return resolve_node(root, info, 'source_solution', 'file')

class CreateInversionSolutionNrml(relay.ClientIDMutation):
    """
    Create a InversionSolutionNrml file
    """
    class Input:
        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta
        source_solution = graphene.ID()
        created = InversionSolutionNrml.created
        predecessors = graphene.List('graphql_api.schema.custom.predecessor.PredecessorInput', required=False, description="list of predecessors")

    inversion_solution_nrml = graphene.Field(InversionSolutionNrml)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        inversion_solution_nrml = get_data_manager().file.create('InversionSolutionNrml', **kwargs)
        db_metrics.put_duration(__name__, 'CreateInversionSolutionNrml.mutate_and_get_payload' , dt.utcnow()-t0)
        return CreateInversionSolutionNrml(inversion_solution_nrml=inversion_solution_nrml, ok=True)
