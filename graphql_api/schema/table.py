#!python3
"""
Table

This module contains the schema definition for an Table

  - file_id the ID of the file (InversionSolution)
  - created - timestamp
  - headers - list of the headers in the data set
  - rows - list of row_data objects,
  - meta - meata attrbutes from the producer
  - table_type - let's constrain this
  - dimensions - list of the main table dimensions
"""
from datetime import datetime as dt

import graphene
from graphene import Enum, relay

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.schema.custom.common import KeyValueListPair, KeyValueListPairInput, KeyValuePair, KeyValuePairInput

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)


class RowItemType(Enum):
    """
    Data type
    """

    integer = 'INT'
    double = 'DBL'
    string = 'STR'
    boolean = "BOO"


class TableType(Enum):
    """
    Data type
    """

    HAZARD_GRIDDED = 'hazard_gridded'
    HAZARD_SITES = 'hazard_sites'
    MFD_CURVES = 'mfd_curves'
    MFD_CURVES_V2 = 'mfd_curves_v2'
    GENERAL = 'general'


class Table(graphene.ObjectType):
    """
    CSV-list structure for floats Distribution
    """

    class Meta:
        interfaces = (relay.Node,)

    name = graphene.String(description="a name for the table")
    object_id = graphene.ID(
        description="ID of the object this data relates to",
    )
    created = graphene.DateTime(
        description="When the task record was created",
    )
    column_headers = graphene.List(graphene.String, description="column headings")
    column_types = graphene.List(RowItemType, description="column types")
    rows = graphene.List(
        graphene.List(graphene.String),
        description="The table rows. Each row is a list of strings that can be coerced according to column_types.",
    )
    meta = graphene.List(
        KeyValuePair, required=False, description="additional meta data, as a list of Key Value pairs."
    )
    table_type = graphene.Field(TableType, description="table type")
    dimensions = graphene.List(
        KeyValueListPair, required=False, description="table dimensions, as a list of Key Value List pairs."
    )

    @classmethod
    def get_node(cls, info, _id):
        t0 = dt.utcnow()
        res = get_data_manager().table.get_one(_id)
        db_metrics.put_duration(__name__, 'Table.get_node', dt.utcnow() - t0)
        return res

    @staticmethod
    def get_object_store_handler():
        return get_data_manager()._table

class CreateTable(relay.ClientIDMutation):
    class Input:
        name = Table.name
        object_id = Table.object_id
        created = Table.created
        column_headers = Table.column_headers
        column_types = Table.column_types
        rows = Table.rows
        meta = graphene.List(
            KeyValuePairInput, required=False, description="additional meta data, as a list of Key Value pairs."
        )
        table_type = graphene.Field(TableType, required=True)
        dimensions = graphene.List(
            KeyValueListPairInput, required=False, description="table dimensions, as a list of Key Value List pairs."
        )

    table = graphene.Field(Table)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        print("mutate_and_get_payload: ", kwargs)
        table = get_data_manager().table.create('Table', **kwargs)
        db_metrics.put_duration(__name__, 'CreateTable.mutate', dt.utcnow() - t0)
        return CreateTable(table=table)
