'''

'''
import logging
import os
from datetime import datetime as dt

import boto3
import graphene
from flask import request
from graphene import relay
from graphql_relay import from_global_id, to_global_id
from requests_aws4auth import AWS4Auth

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import ES_ENDPOINT, ES_INDEX, ES_REGION, IS_OFFLINE, STACK_NAME, TESTING
from graphql_api.data import get_data_manager
from graphql_api.data.data_manager import DataManager
from graphql_api.schema import event, file, thing
from graphql_api.schema.custom.aggregate_inversion_solution import (
    AggregateInversionSolution,
    CreateAggregateInversionSolution,
)
from graphql_api.schema.custom.inversion_solution import (
    AppendInversionSolutionTables,
    CreateInversionSolution,
    InversionSolution,
    LabelledTableRelationInput,
)
from graphql_api.schema.custom.inversion_solution_nrml import CreateInversionSolutionNrml, InversionSolutionNrml
from graphql_api.schema.custom.openquake_hazard_config import CreateOpenquakeHazardConfig, OpenquakeHazardConfig
from graphql_api.schema.custom.openquake_hazard_solution import CreateOpenquakeHazardSolution, OpenquakeHazardSolution
from graphql_api.schema.custom.openquake_hazard_task import (
    CreateOpenquakeHazardTask,
    OpenquakeHazardTask,
    UpdateOpenquakeHazardTask,
)
from graphql_api.schema.custom.scaled_inversion_solution import CreateScaledInversionSolution, ScaledInversionSolution
from graphql_api.schema.custom.time_dependent_inversion_solution import (
    CreateTimeDependentInversionSolution,
    TimeDependentInversionSolution,
)

from .custom.automation_task import AutomationTask, CreateAutomationTask, UpdateAutomationTask
from .custom.general_task import CreateGeneralTask, GeneralTask, UpdateGeneralTask
from .custom.rupture_generation_task import (
    CreateRuptureGenerationTask,
    RuptureGenerationTask,
    RuptureGenerationTaskConnection,
    UpdateRuptureGenerationTask,
)
from .custom.strong_motion_station import CreateStrongMotionStation, StrongMotionStation, StrongMotionStationConnection
from .custom.strong_motion_station_file import CreateSmsFile, SmsFile
from .file import CreateFile, File, FileConnection
from .file_relation import CreateFileRelation, FileRelation, FileRelationConnection
from .get_datastore_handler import get_datastore_handler
from .object_identities import (
    ObjectIdentitiesConnection,
    iterate_dynamodb_nodes,
    iterate_legacy_s3_nodes,
    paginated_object_identities,
)
from .search_manager import SearchManager
from .table import CreateTable, Table
from .task_task_relation import CreateTaskTaskRelation

log = logging.getLogger(__name__)

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=1)

credentials = boto3.Session().get_credentials() if not IS_OFFLINE else None
awsauth = (
    AWS4Auth(credentials.access_key, credentials.secret_key, ES_REGION, 'es', session_token=credentials.token)
    if not IS_OFFLINE
    else None
)

s3_client_args = (
    dict(aws_access_key_id='S3RVER', aws_secret_access_key='S3RVER', endpoint_url='http://localhost:4569')
    if not TESTING and IS_OFFLINE
    else {}
)

search_manager = SearchManager(endpoint=ES_ENDPOINT, es_index=ES_INDEX, awsauth=awsauth)
db_root = DataManager(search_manager, s3_client_args)


class FileUnion(graphene.Union):
    class Meta:
        types = (
            SmsFile,
            File,
            InversionSolution,
            ScaledInversionSolution,
            AggregateInversionSolution,
            InversionSolutionNrml,
            TimeDependentInversionSolution,
        )


class SearchResult(graphene.Union):
    class Meta:
        types = (
            AggregateInversionSolution,
            AutomationTask,
            File,
            GeneralTask,
            InversionSolution,
            InversionSolutionNrml,
            OpenquakeHazardConfig,
            OpenquakeHazardSolution,
            OpenquakeHazardTask,
            RuptureGenerationTask,
            ScaledInversionSolution,
            SmsFile,
            StrongMotionStation,
            TimeDependentInversionSolution,
        )


class SearchResultConnection(relay.Connection):
    class Meta:
        node = SearchResult

    total_count = graphene.Field(graphene.Int)

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)


class Search(graphene.ObjectType):
    ok = graphene.Boolean()
    search_result = relay.ConnectionField(SearchResultConnection)


class NodeFilter(graphene.ObjectType):
    ok = graphene.Boolean()
    result = relay.ConnectionField(SearchResultConnection)


class ReindexResult(graphene.ObjectType):
    ok = graphene.Boolean()


class QueryRoot(graphene.ObjectType):
    """This is the entry point for all graphql query operations"""

    rupture_generation_tasks = relay.ConnectionField(
        RuptureGenerationTaskConnection, description="List Opensha Rupture Generation tasks."
    )

    files = relay.ConnectionField(FileConnection, description="The files.")

    node = relay.Node.Field()
    nodes = graphene.Field(NodeFilter, id_in=graphene.List(graphene.ID))

    reindex = graphene.Field(
        NodeFilter, id_in=graphene.List(graphene.ID), description="reindex objects with the Search (ES) service"
    )

    search = graphene.Field(Search, search_term=graphene.String())

    object_identities = graphene.ConnectionField(
        ObjectIdentitiesConnection, object_type=graphene.Argument(graphene.String)
    )

    legacy_object_identities = graphene.ConnectionField(
        ObjectIdentitiesConnection, store_type=graphene.Argument(graphene.String)
    )

    strong_motion_station = graphene.Field(StrongMotionStation, id=graphene.ID(required=True))
    strong_motion_stations = relay.ConnectionField(
        StrongMotionStationConnection, description="The list of strong motion stations"
    )

    def resolve_strong_motion_stations(root, info):
        t0 = dt.utcnow()
        sms = db_root.thing.get_all('StrongMotionStation')
        db_metrics.put_duration(__name__, 'resolve_strong_motion_stations', dt.utcnow() - t0)
        return sms

    def resolve_strong_motion_station(root, info, id):
        t0 = dt.utcnow()
        _type, _id = from_global_id(id)
        sms = db_root.thing.get_one(_id)
        db_metrics.put_duration(__name__, 'resolve_strong_motion_station', dt.utcnow() - t0)
        return sms

    @staticmethod
    def resolve_rupture_generation_tasks(root, info):
        """
        Returns:
            list: rupture generation task list
        """
        t0 = dt.utcnow()
        tasks = db_root.thing.get_all('RuptureGenerationTask')
        db_metrics.put_duration(__name__, 'resolve_rupture_generation_tasks', dt.utcnow() - t0)
        return tasks

    @staticmethod
    def resolve_files(root, info):
        """
        Returns:
            list: file list
        """
        t0 = dt.utcnow()
        files = db_root.file.get_all()
        db_metrics.put_duration(__name__, 'resolve_files', dt.utcnow() - t0)
        return files

    @staticmethod
    def resolve_search(root, info, **kwargs):
        t0 = dt.utcnow()
        search_result = db_root.search_manager.search(kwargs.get('search_term'))
        db_metrics.put_duration(__name__, 'resolve_search', dt.utcnow() - t0)
        return Search(ok=True, search_result=search_result)

    @staticmethod
    def resolve_object_identities(root, info, object_type, **kwargs):
        log.info(f'resolve_object_identities args: {kwargs}')
        t0 = dt.utcnow()
        # search_result = db_root.search_manager.search(kwargs.get('search_term'))
        # db_metrics.put_duration(__name__, 'resolve_search', dt.utcnow() - t0)
        nodes = iterate_dynamodb_nodes(object_type, **kwargs)
        return paginated_object_identities(nodes, **kwargs)

    @staticmethod
    def resolve_legacy_object_identities(root, info, store_type, **kwargs):
        assert store_type in ['File', 'Thing', 'Table']
        log.info(f'resolve_object_identities args: {kwargs}')
        t0 = dt.utcnow()
        # search_result = db_root.search_manager.search(kwargs.get('search_term'))
        # db_metrics.put_duration(__name__, 'resolve_search', dt.utcnow() - t0)
        nodes = iterate_legacy_s3_nodes(store_type, **kwargs)
        return paginated_object_identities(nodes, **kwargs)

    @staticmethod
    def resolve_nodes(root, info, id_in, **kwargs):
        #    print(id_in, kwargs)
        t0 = dt.utcnow()
        result = []
        for gid in id_in:
            _type, _id = from_global_id(gid)
            if _type in ['RuptureGenerationTask', 'StrongMotionStation', 'GeneralTask', 'AutomationTask']:
                result.append(db_root.thing.get_one(_id))
            elif _type in ['File', 'SmsFile', 'InversionSolution']:
                result.append(db_root.file.get_one(_id))
            elif _type in ['Table']:
                result.append(db_root.table.get_one(_id))
            else:
                raise ValueError("unable to resolve, object id")
        db_metrics.put_duration(__name__, 'resolve_nodes', dt.utcnow() - t0)
        # result =  = db_root.search_manager.search(kwargs.get('search_term'))
        return NodeFilter(ok=True, result=result)

    @staticmethod
    def resolve_reindex(root, info, id_in, **kwargs):
        t0 = dt.utcnow()
        result = []
        log.info(f'resolve_resolve_reindex id_in: {id_in}')
        for gid in id_in:
            object_type, object_id = from_global_id(gid)
            handler = get_datastore_handler(object_type)
            es_key = f"{handler.prefix}_{object_id}"
            body = handler.get_one_raw(object_id)
            search_manager.index_document(es_key, body)

        db_metrics.put_duration(__name__, 'resolve_reindex', dt.utcnow() - t0)
        # result =  = db_root.search_manager.search(kwargs.get('search_term'))
        return ReindexResult(ok=True)


class MutationRoot(graphene.ObjectType):
    append_inversion_solution_tables = AppendInversionSolutionTables.Field()
    create_automation_task = CreateAutomationTask.Field()
    create_file = CreateFile.Field()
    create_file_relation = CreateFileRelation.Field()
    create_general_task = CreateGeneralTask.Field()
    create_inversion_solution = CreateInversionSolution.Field()
    create_rupture_generation_task = CreateRuptureGenerationTask.Field()
    create_sms_file = CreateSmsFile.Field()
    create_strong_motion_station = CreateStrongMotionStation.Field()
    create_table = CreateTable.Field()
    create_task_relation = CreateTaskTaskRelation.Field()
    update_automation_task = UpdateAutomationTask.Field()
    update_general_task = UpdateGeneralTask.Field()
    update_rupture_generation_task = UpdateRuptureGenerationTask.Field()
    create_aggregate_inversion_solution = CreateAggregateInversionSolution.Field()
    create_scaled_inversion_solution = CreateScaledInversionSolution.Field()
    create_time_dependent_inversion_solution = CreateTimeDependentInversionSolution.Field()
    create_inversion_solution_nrml = CreateInversionSolutionNrml.Field()
    create_openquake_hazard_solution = CreateOpenquakeHazardSolution.Field()
    create_openquake_hazard_config = CreateOpenquakeHazardConfig.Field()
    create_openquake_hazard_task = CreateOpenquakeHazardTask.Field()
    update_openquake_hazard_task = UpdateOpenquakeHazardTask.Field()


root_schema = graphene.Schema(query=QueryRoot, mutation=MutationRoot, auto_camelcase=False)
