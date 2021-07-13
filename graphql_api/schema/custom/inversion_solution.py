#!python inversion_solution
"""
This module contains the schema definition for an InversionSolution.

"""
import graphene
from graphene import relay
from graphql_api.schema.file import FileInterface
from graphql_api.schema.table import Table
from .rupture_generation import RuptureGenerationTask

from graphql_api.data_s3 import get_data_manager
from graphql_api.schema.custom.common import KeyValuePairInput

class InversionSolution(graphene.ObjectType):
    """

    """
    class Meta:
        interfaces = (relay.Node, FileInterface)

    produced_by = graphene.ID()
    mfd_table = graphene.ID()


class CreateInversionSolution(relay.ClientIDMutation):
    class Input:
        file_name = graphene.String()
        md5_digest = graphene.String(description="The base64-encoded md5 digest of the file")
        file_size = graphene.Int()
        produced_by = graphene.ID(required=False,)
        mfd_table = graphene.ID(required=False,)

        meta = graphene.List(KeyValuePairInput, required=False,
            description="additional file meta data, as a list of Key Value pairs.")

    inversion_solution = graphene.Field(InversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        inversion_solution = get_data_manager().file.create('InversionSolution', **kwargs)
        return CreateInversionSolution(inversion_solution=inversion_solution, ok=True)
