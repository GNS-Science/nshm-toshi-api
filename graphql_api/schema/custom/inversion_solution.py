#!python3
"""
This module contains the schema definition for an InversionSolution.

"""
import graphene
from graphene import relay
from graphql_relay import from_global_id

from graphql_api.schema.file import FileInterface, CreateFile
from graphql_api.schema.table import Table
from graphql_api.schema.custom.rupture_generation import RuptureGenerationTask
from .common import KeyValuePair, KeyValuePairInput

from graphql_api.data_s3 import get_data_manager

def resolve_node(node_id, info, dm_type):
    assert dm_type in ["table", "thing"]
    if node_id:
        type, nid = from_global_id(node_id)
        if len(info.field_asts[0].selection_set.selections)==1:
            if info.field_asts[0].selection_set.selections[0].name.value == 'id':
                return nid #no need to fecth if the only field needed is id
        else:
            return getattr(get_data_manager(), dm_type).get_one(nid)

class InversionSolution(graphene.ObjectType):
    """
    Represents an Inversion Solution file
    """
    class Meta:
        interfaces = (relay.Node, FileInterface)

    created = graphene.DateTime(description="When the task record was created", )
    metrics = graphene.List(KeyValuePair, description="result metrics from the task, as a list of Key Value pairs.")

    produced_by_id = graphene.ID()
    mfd_table_id = graphene.ID()
    hazard_table_id = graphene.ID()

    hazard_table = graphene.Field(Table)
    mfd_table = graphene.Field(Table)
    produced_by = graphene.Field(RuptureGenerationTask)

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().file.get_one(_id)
        return node

    def resolve_hazard_table(root, info, **args):
        return resolve_node(root.hazard_table_id, info, 'table')

    def resolve_mfd_table(root, info, **args):
        return resolve_node(root.mfd_table_id, info, 'table')

    def resolve_produced_by(root, info, **args):
        return resolve_node(root.produced_by_id, info, 'thing')

    @staticmethod
    def from_json(jsondata):
        #Field type transforms...
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.datetime.fromisoformat(started)
        return RuptureGenerationTask(**jsondata)

class CreateInversionSolution(relay.ClientIDMutation):
    """
    Create an Inversion Solution file
    """
    class Input:
        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta

        produced_by_id = InversionSolution.produced_by_id   #graphene.ID(required=False,)
        mfd_table_id = InversionSolution.mfd_table_id       #graphene.ID(required=False,)
        hazard_table_id = InversionSolution.hazard_table_id #graphene.ID(required=False,)
        created = InversionSolution.created
        metrics = graphene.List(KeyValuePairInput, required=False,
            description="result metrics from the solution, as a list of Key Value pairs.")

    inversion_solution = graphene.Field(InversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        inversion_solution = get_data_manager().file.create('InversionSolution', **kwargs)
        return CreateInversionSolution(inversion_solution=inversion_solution, ok=True)
