#!python3
"""
FileDataTable

This module contains the schema definition for an FileDataTable

  - file_id the ID of the file (InversionSolution)
  - created - timestamp
  - headers - list of the headers in the data set
  - rows - list of row_data objects,
"""

import graphene
from graphene import relay
from graphene import Enum
from graphql_api.schema.thing import Thing
from graphql_api.data_s3 import get_data_manager

class RowItemType(Enum):
    """
    Data type
    """
    integer = 'INT'
    double = 'DBL'
    string = 'STR'
    boolean = "BOO"

class Table(graphene.ObjectType):
    """
    CSV-list structure for floats Distribution
    """
    class Meta:
        interfaces = (relay.Node,)

    object_id = graphene.ID(description="ID of the object this data relates to", )
    created = graphene.DateTime(description="When the task record was created", )

    column_headers = graphene.List(graphene.String, )
    column_types = graphene.List(RowItemType, )
    rows = graphene.List(graphene.List(graphene.String))

    # files = graphene.String(description="do not use")

    @classmethod
    def get_node(cls, info, _id):
        return  get_data_manager().table.get_one(_id)


class CreateTable(relay.ClientIDMutation):
    class Input:
        object_id = graphene.ID(description="ID of the object this data relates to", )
        created = graphene.DateTime(description="When the taskrecord was created", )
        column_headers = graphene.List(graphene.String, )
        column_types = graphene.List(RowItemType, )
        rows = graphene.List(graphene.List(graphene.String))

    table = graphene.Field(Table)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        table = get_data_manager().table.create('Table', **kwargs)
        return CreateTable(table=table)
