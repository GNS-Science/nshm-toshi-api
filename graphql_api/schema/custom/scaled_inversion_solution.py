#!python3
"""
This module contains the schema definition for an InversionSolution.

"""
# import copy
import graphene
# import uuid
# import datetime
from graphene import relay
# from graphql_relay import from_global_id

# from importlib import import_module
from datetime import datetime as dt

from graphql_api.data import get_data_manager
from graphql_api.schema.file import FileInterface, CreateFile
# from graphql_api.schema.table import Table

from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

from .helpers import resolve_node
from .inversion_solution import InversionSolution

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration",
    resolution=CW_METRICS_RESOLUTION)

class ScaledInversionSolution(graphene.ObjectType):
    """
    Represents a Scaled Inversion Solution file
    """
    class Meta:
        interfaces = (relay.Node, FileInterface)

    created = FileInterface.created #graphene.DateTime(description="When the task record was created", )
    source_solution = graphene.Field(InversionSolution, description="The original soloution as produced by opensha")

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().file.get_one(_id, "ScaledInversionSolution")
        return node

    def resolve_source_solution(root, info, **args):
        return resolve_node(root, info, 'source_solution', 'file')

class CreateScaledInversionSolution(relay.ClientIDMutation):
    """
    Create an Inversion Solution file
    """
    class Input:
        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta
        source_solution = graphene.ID()
        created = ScaledInversionSolution.created

    solution = graphene.Field(ScaledInversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        solution = get_data_manager().file.create('ScaledInversionSolution', **kwargs)
        db_metrics.put_duration(__name__, 'CreateScaledInversionSolution.mutate_and_get_payload' , dt.utcnow()-t0)
        return CreateScaledInversionSolution(solution=solution, ok=True)
