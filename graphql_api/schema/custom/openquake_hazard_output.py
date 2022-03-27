#!python3
"""
This module contains the schema definition for OpenquakeHazardOutput.

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

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration",
    resolution=CW_METRICS_RESOLUTION)

class OpenquakeHazardOutput(graphene.ObjectType):
    """
    Represents a OpenquakeHazardOutput archive file

    This is a zip archive containing hazard outputs (`oq engine --export ....)

    NB any arguments used to generate this object should be captured as in meta field.
    """
    class Meta:
        interfaces = (relay.Node, FileInterface)

    created = graphene.DateTime(description="When the scaled solution file was created" )
    produced_by = graphene.Field(InversionSolution, description="The original soloution as produced by opensha")

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().file.get_one(_id, "OpenquakeHazardOutput")
        return node

    def resolve_produced_by(root, info, **args):
        return resolve_node(root, info, 'produced_by', 'thing')

class CreateOpenquakeHazardOutput(relay.ClientIDMutation):
    """
    Create a OpenquakeHazardOutput file
    """
    class Input:
        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta
        produced_by = graphene.ID()
        created = OpenquakeHazardOutput.created

    openquake_hazard_output = graphene.Field(OpenquakeHazardOutput)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        openquake_hazard_output = get_data_manager().file.create('OpenquakeHazardOutput', **kwargs)
        db_metrics.put_duration(__name__, 'CreateOpenquakeHazardOutput.mutate_and_get_payload' , dt.utcnow()-t0)
        return CreateOpenquakeHazardOutput(openquake_hazard_output=openquake_hazard_output, ok=True)
