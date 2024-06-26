"""
This module contains the configuration for openquake hazard job

"""

# import datetime as dt
import logging
from datetime import datetime as dt

import graphene
from graphene import relay
from graphql_relay import from_global_id

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.schema.file import File
from graphql_api.schema.thing import Thing

from .helpers import resolve_node
from .inversion_solution_nrml import InversionSolutionNrml

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

logger = logging.getLogger(__name__)


class OpenquakeNrmlUnion(graphene.Union):
    """
    Some NRML files are just files i.e BG seismicity XML.
    """

    class Meta:
        types = (File, InversionSolutionNrml)


class OpenquakeHazardConfig(graphene.ObjectType):
    """An OpenquakeHazardConfig in the NSHM process"""

    class Meta:
        interfaces = (relay.Node, Thing)

    source_models = graphene.List(OpenquakeNrmlUnion, description="List of Source NRML files")
    template_archive = graphene.Field(
        File, description="An archive of all the configuration files (besides those in source_models"
    )

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().thing.get_one(_id)
        return node

    def resolve_source_models(root, info, **args):
        t0 = dt.utcnow()
        if root.source_models:
            for obj_id in root.source_models:
                clazz, key = from_global_id(obj_id)
                logger.info(f'resolve source_model {(clazz, key)} from {obj_id}')
                yield get_data_manager().file.get_one(key)
        db_metrics.put_duration(__name__, 'OpenquakeHazardConfig.resolve_source_models', dt.utcnow() - t0)

    def resolve_template_archive(root, info, **args):
        logger.debug(f'root {root}, info {info}, args {args}')
        if root.template_archive:
            return resolve_node(root, info, 'template_archive', 'file')


# class OpenquakeHazardConfigConnection(relay.Connection):
#     """A list of OpenquakeHazardConfig items"""
#     class Meta:
#         node = OpenquakeHazardConfig
#
#     total_count = graphene.Int()
#
#     @staticmethod
#     def resolve_total_count(root, info, *args, **kwargs):
#         return len(root.edges)


class CreateOpenquakeHazardConfig(relay.ClientIDMutation):
    class Input:
        # meta = CreateFile.Arguments.meta
        created = Thing.created
        source_models = graphene.List(graphene.ID, description="List of Source NRML")
        template_archive = graphene.ID(description="ID of an archive file, containing the config inputs.")
        # solution_sources = OpenquakeHazardConfig.solution_sources

    config = graphene.Field(OpenquakeHazardConfig)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        logger.debug(f"payload: {kwargs}")
        config = get_data_manager().thing.create('OpenquakeHazardConfig', **kwargs)
        db_metrics.put_duration(__name__, 'CreateOpenquakeHazardConfig.mutate_and_get_payload', dt.utcnow() - t0)
        return CreateOpenquakeHazardConfig(config=config, ok=True)


# class UpdateOpenquakeHazardConfig(graphene.Mutation):
#     class Arguments:
#         input = AutomationTaskUpdateInput(required=True)

#     task_result = graphene.Field(OpenquakeHazardConfig)

#     @classmethod
#     def mutate(cls, root, info, input):
#         t0 = dt.utcnow()
#         print("mutate: ", input)
#         thing_id = input.pop('task_id')
#         task_result = get_data_manager().thing.update('OpenquakeHazardConfig', thing_id, **input)
#         db_metrics.put_duration(__name__, 'UpdateOpenquakeHazardConfig.mutate_and_get_payload' , dt.utcnow()-t0)
#         return UpdateOpenquakeHazardConfig(task_result=task_result)
