#!python3
"""
This module contains the schema definition for OpenquakeHazardSolution.

"""
import graphene
from datetime import datetime as dt
from graphene import relay

from graphql_api.data import get_data_manager
from graphql_api.schema.file import File
from graphql_api.schema.thing import Thing
from graphql_api.schema.custom.common import KeyValuePair, KeyValuePairInput

from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

from .helpers import resolve_node
from .inversion_solution import InversionSolution
from .openquake_hazard_config import OpenquakeHazardConfig
# from .openquake_hazard_task import OpenquakeHazardTask


db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration",
    resolution=CW_METRICS_RESOLUTION)

class OpenquakeHazardSolution(graphene.ObjectType):
    """
    Represents a OpenquakeHazardSolution

    This has :
     - config an OpenquakeHazardConfig
     - export_archive File a zip archive containing hazard outputs (`oq engine --export ....)
     - hdf5_archive File a zip archive containing the raw hdf5 compressed

    NB any arguments used to generate this object should be captured as in meta field.
    """
    class Meta:
        interfaces = (relay.Node, Thing)

    created = graphene.DateTime(
        description="When it was created (UTZ)")
    config = graphene.Field(OpenquakeHazardConfig,
        description="the configuration used to produce this solution")
    csv_archive = graphene.Field(File,
        description="a zip archive containing hazard csv outputs (`oq engine --export-outputs ....)" )
    hdf5_archive = graphene.Field(File,
        description="a zip archive containing containing the raw hdf5")

    metrics = graphene.List(KeyValuePair,
            description="result metrics from the solution, as a list of Key Value pairs.")

    meta = graphene.List(KeyValuePair,
            description="result metrics from the solution, as a list of Key Value pairs.")

    #all_the_meta FUTURE
    produced_by = graphene.Field('graphql_api.schema.custom.OpenquakeHazardTask', description="The task that produced this solution")

    @classmethod
    def get_node(cls, info, _id):
        return get_data_manager().thing.get_one(_id)

    def resolve_produced_by(root, info, **args):
        return resolve_node(root, info, 'produced_by', 'thing')

    def resolve_config(root, info, **args):
        return resolve_node(root, info, 'config', 'thing')

    def resolve_csv_archive(root, info, **args):
        return resolve_node(root, info, 'csv_archive', 'file')

    def resolve_hdf5_archive(root, info, **args):
        return resolve_node(root, info, 'hdf5_archive', 'file')


# class OpenquakeHazardSolutionUpdateInput(graphene.InputObjectType):
#     node_id = graphene.ID(required=True)

#     csv_archive = graphene.ID(required=False)
#     hdf5_archive = graphene.ID( required=False)

#     arguments = graphene.List(KeyValuePairInput, required=False,
#         description="input arguments for the rupture generation task, as a list of Key Value pairs.")

#     metrics = graphene.List(KeyValuePairInput, required=False,
#         description="result metrics from the task, as a list of Key Value pairs.")

class CreateOpenquakeHazardSolution(relay.ClientIDMutation): #graphene.Mutation):
    """
    Create an OpenquakeHazardSolution
    """
    class Input:
        created = OpenquakeHazardSolution.created
        config = graphene.ID(required=True)
        produced_by = graphene.ID(required=True)

        csv_archive = graphene.ID(required=False)
        hdf5_archive = graphene.ID( required=False)

        meta = graphene.List(KeyValuePairInput, required=False,
            description="additional file meta data, as a list of Key Value pairs.")

        metrics = graphene.List(KeyValuePairInput, required=False,
            description="result metrics from the solution, as a list of Key Value pairs.")

    openquake_hazard_solution = graphene.Field(OpenquakeHazardSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        openquake_hazard_solution = get_data_manager().thing.create('OpenquakeHazardSolution', **kwargs)
        db_metrics.put_duration(__name__, 'CreateOpenquakeHazardSolution.mutate_and_get_payload' , dt.utcnow()-t0)
        return CreateOpenquakeHazardSolution(openquake_hazard_solution=openquake_hazard_solution, ok=True)
