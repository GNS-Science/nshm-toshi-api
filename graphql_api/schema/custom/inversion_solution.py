#!python3
"""
This module contains the schema definition for an InversionSolution.

"""
import graphene
from graphene import relay
from graphql_api.schema.file import FileInterface, CreateFile

from graphql_api.data_s3 import get_data_manager


class InversionSolution(graphene.ObjectType):
    """
    Represents an Inversion Solution file
    """
    class Meta:
        interfaces = (relay.Node, FileInterface)

    produced_by = graphene.ID()
    mfd_table = graphene.ID()
    hazard_table = graphene.ID()

class CreateInversionSolution(relay.ClientIDMutation):
    """
    Create an Inversion Solution file
    """
    class Input:
        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta

        produced_by = graphene.ID(required=False,)
        mfd_table = graphene.ID(required=False,)
        hazard_table = graphene.ID(required=False,)

    inversion_solution = graphene.Field(InversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        inversion_solution = get_data_manager().file.create('InversionSolution', **kwargs)
        return CreateInversionSolution(inversion_solution=inversion_solution, ok=True)
