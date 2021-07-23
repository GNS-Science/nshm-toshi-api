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

    name = graphene.String(description="a name for the table")
    object_id = graphene.ID(description="ID of the object this data relates to", )
    created = graphene.DateTime(description="When the task record was created", )
    column_headers = graphene.List(graphene.String, description="column headings")
    column_types = graphene.List(RowItemType, description="column types" )
    rows = graphene.List(graphene.List(graphene.String), description="The table rows. Each row is a list of strings that can be coerced according to column_types.")

    @classmethod
    def get_node(cls, info, _id):
        return  get_data_manager().table.get_one(_id)


class CreateTable(relay.ClientIDMutation):
    class Input:
        name = Table.name
        object_id = Table.object_id
        created = Table.created
        column_headers = Table.column_headers
        column_types = Table.column_types
        rows = Table.rows

    table = graphene.Field(Table)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        table = get_data_manager().table.create('Table', **kwargs)
        return CreateTable(table=table)
