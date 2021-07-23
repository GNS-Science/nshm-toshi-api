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
from importlib import import_module

from graphql_api.data_s3 import get_data_manager

def resolve_node(root, info, id_field, dm_type):
    """
    Optimisation function, looks are the query and avoids a fetch if
    we only want to resolve the id field.
    """
    assert dm_type in ["table", "thing"]

    node_id = getattr(root, id_field)
    if not node_id:
        return

    type, nid = from_global_id(node_id)

    if len(info.field_asts[0].selection_set.selections)==1 and \
        (info.field_asts[0].selection_set.selections[0].name.value == 'id'):

        #create an instance with just it's id attribute set
        clazz = getattr(import_module('graphql_api.schema'), type)
        return clazz(id=nid)
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
        return resolve_node(root, info, 'hazard_table_id',  'table')

    def resolve_mfd_table(root, info, **args):
        return resolve_node(root, info, 'mfd_table_id', 'table')

    def resolve_produced_by(root, info, **args):
        return resolve_node(root, info, 'produced_by_id', 'thing')

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

        produced_by_id = InversionSolution.produced_by_id
        mfd_table_id = InversionSolution.mfd_table_id
        hazard_table_id = InversionSolution.hazard_table_id
        created = InversionSolution.created
        metrics = graphene.List(KeyValuePairInput, required=False,
            description="result metrics from the solution, as a list of Key Value pairs.")

    inversion_solution = graphene.Field(InversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        inversion_solution = get_data_manager().file.create('InversionSolution', **kwargs)
        return CreateInversionSolution(inversion_solution=inversion_solution, ok=True)
