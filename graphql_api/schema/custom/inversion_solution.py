#!python3
"""
This module contains the schema definition for an InversionSolution.

"""
import copy
import datetime
import logging
import uuid

# from importlib import import_module
from datetime import datetime as dt

import graphene
from graphene import relay
from graphql_relay import from_global_id

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.schema.file import CreateFile, FileInterface
from graphql_api.schema.table import Table

from .automation_task import AutomationTask
from .common import KeyValuePair, KeyValuePairInput, PredecessorsInterface
from .helpers import resolve_node
from .labelled_table_relation import LabelledTableRelation, LabelledTableRelationInput
from .rupture_generation_task import RuptureGenerationTask

log = logging.getLogger(__name__)

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)


class AutomationTaskUnion(graphene.Union):
    class Meta:
        types = (RuptureGenerationTask, AutomationTask)


class InversionSolutionInterface(graphene.Interface):
    """A interface for things like Inversion Solution"""

    # class Meta:
    #     interfaces = (relay.Node, FileInterface)

    created = graphene.DateTime(
        description="When the solution was created",
    )
    metrics = graphene.List(KeyValuePair, description="result metrics from the task, as a list of Key Value pairs.")

    # produced_by_id = graphene.ID(description='deprecated')
    mfd_table_id = graphene.ID(description='deprecated')

    hazard_table_id = graphene.ID(description='deprecated')
    hazard_table = graphene.Field(Table, description='deprecated')

    mfd_table = graphene.Field(
        Table, description='was deprecated, but now returns the V2 MFD curve table if one is found'
    )

    def resolve_mfd_table(root, info, **args):
        if root.tables:
            for table in root.tables:
                if table.get('table_type').upper() == 'MFD_CURVES_V2':
                    _clazz, _id = from_global_id(table['table_id'])
                    return Table.get_node(None, _id)

    produced_by = graphene.Field(AutomationTaskUnion)

    def resolve_produced_by(root, info, **args):
        log.info('resolve_produced_by')
        return resolve_node(root, info, 'produced_by', 'thing')

    tables = graphene.List(LabelledTableRelation)

    def resolve_tables(root, info, **args):
        if root.tables:
            for table in root.tables:
                yield LabelledTableRelation(**table)


class InversionSolution(graphene.ObjectType):
    """
    Represents an Inversion Solution file
    """

    class Meta:
        interfaces = (relay.Node, InversionSolutionInterface, FileInterface, PredecessorsInterface)

    @classmethod
    def get_node(cls, info, _id):
        # log.info(f'InversionSolution.get_node {cls} {info} {_id}' )
        t0 = dt.utcnow()
        node = get_data_manager().file.get_one(_id)
        db_metrics.put_duration(__name__, 'InversionSolution.resolve_node', dt.utcnow() - t0)
        return node


class CreateInversionSolution(relay.ClientIDMutation):
    """
    Create an Inversion Solution file
    """

    class Input:
        file_name = FileInterface.file_name
        md5_digest = FileInterface.md5_digest
        file_size = FileInterface.file_size
        meta = CreateFile.Arguments.meta

        produced_by = graphene.ID()
        mfd_table_id = InversionSolutionInterface.mfd_table_id
        hazard_table_id = InversionSolutionInterface.hazard_table_id
        predecessors = graphene.List(
            'graphql_api.schema.custom.predecessor.PredecessorInput', equired=False, description="list of predecessors"
        )

        tables = graphene.List(LabelledTableRelationInput, required=False)

        created = InversionSolutionInterface.created

        metrics = graphene.List(
            KeyValuePairInput,
            required=False,
            description="result metrics from the solution, as a list of Key Value pairs.",
        )

    inversion_solution = graphene.Field(InversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        log.info(f"CreateInversionSolution mutate_and_get_payload {kwargs}")
        inversion_solution = get_data_manager().file.create('InversionSolution', **kwargs)
        db_metrics.put_duration(__name__, 'CreateInversionSolution.mutate_and_get_payload', dt.utcnow() - t0)
        solution = CreateInversionSolution(inversion_solution=inversion_solution, ok=True)
        log.info(f"solution: {solution}")
        return solution


class AppendInversionSolutionTables(relay.ClientIDMutation):
    """
    Append LabelledTableRelationTable to an existing Inversion Solution
    """

    class Input:
        id = graphene.ID()
        tables = graphene.List(LabelledTableRelationInput, required=True)

    inversion_solution = graphene.Field(InversionSolution)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        t0 = dt.utcnow()
        type, nid = from_global_id(kwargs.get('id'))
        inversion_solution = get_data_manager().file.get_one_raw(nid)

        # inversion_solution = InversionSolution(inversion_solution)
        # TODO this is schema migration , need a cleaner way
        if not inversion_solution.get('clazz_name') == 'InversionSolution':
            print(f"Upgrading {inversion_solution.get('clazz_name')} to InversionSolution")
            inversion_solution['clazz_name'] = 'InversionSolution'
        if not inversion_solution.get('tables'):
            inversion_solution['tables'] = []

        # table updates...
        for table in kwargs['tables']:
            table_relation = copy.copy(table)
            table_relation['identity'] = str(uuid.uuid4())
            table_relation['created'] = dt.now(datetime.timezone.utc).isoformat()
            table_relation['table_type'] = table_relation['table_type'].value  # ENUM
            inversion_solution['tables'].append(table_relation)

        inversion_solution = get_data_manager().file.update(nid, inversion_solution)
        print('inversion_solution', inversion_solution)
        db_metrics.put_duration(__name__, 'AppendInversionSolutionTables.mutate_and_get_payload', dt.utcnow() - t0)
        return AppendInversionSolutionTables(inversion_solution, ok=True)
