#!python3 labelled_table_relation
"""
This module contains the schema definition for an LabelledTableRelation.

"""
import graphene

from graphql_api.schema.custom.common import KeyValueListPair, KeyValueListPairInput
from graphql_api.schema.table import Table, TableType

from .helpers import resolve_node


class LabelledTableRelation(graphene.ObjectType):
    """
    a unique, labelled table relationship.

    This is intended to be used as an internal structure within an InversionSolution (or similar).
    It must be stored internally in the parent object, so does not implement the node interface. New instances must be mutated via the
    parent class.
    """

    identity = graphene.String(description="an internal unique UUID to support mutations.")
    created = graphene.DateTime(
        description="When the task record was created.",
    )

    produced_by_id = graphene.ID(description="the object responsible for creating this relationship.")
    label = graphene.String(description="Label used to differentiate this relationsip for humans.")
    table_id = graphene.ID(description="the ID of the table")

    table = graphene.Field(Table)

    table_type = graphene.Field(TableType, description="table type")
    dimensions = graphene.List(
        KeyValueListPair, required=False, description="table dimensions, as a list of Key Value List pairs."
    )

    def resolve_table(root, info, **args):
        # print('resolve',  'LabelledTableRelation', args)
        return resolve_node(root, info, 'table_id', 'table')


class LabelledTableRelationInput(graphene.InputObjectType):
    produced_by_id = LabelledTableRelation.produced_by_id
    label = LabelledTableRelation.label
    table_id = LabelledTableRelation.table_id
    table_type = LabelledTableRelation.table_type
    dimensions = graphene.List(
        KeyValueListPairInput, required=False, description="table dimensions, as a list of Key Value List pairs."
    )
