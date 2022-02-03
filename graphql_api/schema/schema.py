'''

'''
import os
import boto3
import graphene
from graphene import relay
from graphql_relay import from_global_id, to_global_id

from graphql_api.data_s3.data_manager import DataManager
from .custom.rupture_generation_task import RuptureGenerationTaskConnection, CreateRuptureGenerationTask,\
    UpdateRuptureGenerationTask, RuptureGenerationTask
from requests_aws4auth import AWS4Auth

from .file import CreateFile, File, FileConnection
from .file_relation import CreateFileRelation, FileRelationConnection
from .search_manager import SearchManager

from graphql_api.schema import file, event, thing
from .custom.strong_motion_station import CreateStrongMotionStation, StrongMotionStation,\
    StrongMotionStationConnection
from .custom.strong_motion_station_file import CreateSmsFile, SmsFile
from graphql_api.data_s3 import get_data_manager

from .custom.general_task import GeneralTask, CreateGeneralTask, UpdateGeneralTask
from .task_task_relation import CreateTaskTaskRelation

from .table import CreateTable , Table
from .custom.automation_task import AutomationTask, CreateAutomationTask, UpdateAutomationTask

#from .custom.inversion_solution import
from graphql_api.schema.custom.inversion_solution import InversionSolution, CreateInversionSolution, AppendInversionSolutionTables, LabelledTableRelationInput

from graphql_api.config import IS_OFFLINE, ES_REGION, ES_ENDPOINT, ES_INDEX

credentials = boto3.Session().get_credentials() if not IS_OFFLINE else None
awsauth = AWS4Auth(
            credentials.access_key, credentials.secret_key,
            ES_REGION, 'es', session_token=credentials.token) if not IS_OFFLINE else None

s3_client_args = dict(aws_access_key_id='S3RVER',
        aws_secret_access_key='S3RVER',
        endpoint_url='http://localhost:4569') if IS_OFFLINE else {}

search_manager = SearchManager(endpoint=ES_ENDPOINT, es_index=ES_INDEX, awsauth=awsauth)
db_root = DataManager(search_manager, s3_client_args)

class FileUnion(graphene.Union):
    class Meta:
        types = (SmsFile, File, InversionSolution)

class SearchResult(graphene.Union):
    class Meta:
        types = (File, RuptureGenerationTask, StrongMotionStation, SmsFile, GeneralTask, Table, InversionSolution, AutomationTask)

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

class QueryRoot(graphene.ObjectType):
    """This is the entry point for all graphql query operations"""

    rupture_generation_tasks = relay.ConnectionField(
        RuptureGenerationTaskConnection,
        description="List Opensha Rupture Generation tasks."
    )

    files = relay.ConnectionField(
        FileConnection,
        description="The files."
    )

    node = relay.Node.Field()

    nodes = graphene.Field(NodeFilter, id_in=graphene.List(graphene.ID))

    search = graphene.Field(Search, search_term=graphene.String())
    file = relay.Node.Field(File, id=graphene.ID(required=True))

    strong_motion_station = graphene.Field(StrongMotionStation, id=graphene.ID(required=True))
    strong_motion_stations = relay.ConnectionField(
        StrongMotionStationConnection,
        description="The list of strong motion stations"
    )

    def resolve_strong_motion_stations(root, info):
        return db_root.thing.get_all('StrongMotionStation')


    def resolve_strong_motion_station(root, info, id):
        _type, _id = from_global_id(id)
        return db_root.thing.get_one(_id)


    @staticmethod
    def resolve_rupture_generation_tasks(root, info):
        """
        Returns:
            list: rupture generation task list
        """
        return db_root.thing.get_all('RuptureGenerationTask')

    @staticmethod
    def resolve_files(root, info):
        """
        Returns:
            list: file list
        """
        return db_root.file.get_all()

    @staticmethod
    def resolve_search(root, info, **kwargs):
        search_result = db_root.search_manager.search(kwargs.get('search_term'))
        return Search(ok=True, search_result=search_result)

    @staticmethod
    def resolve_nodes(root, info, id_in,**kwargs):
        print(id_in, kwargs)
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
                raise ValueError("unable to resolve, object id", obj['_source'])

        #result =  = db_root.search_manager.search(kwargs.get('search_term'))
        return NodeFilter(ok=True, result =result)



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

root_schema = graphene.Schema(query=QueryRoot, mutation=MutationRoot, auto_camelcase=False)
