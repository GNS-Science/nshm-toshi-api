'''

'''
import os
import boto3
import graphene
from graphene import relay
from graphql_relay import from_global_id, to_global_id

from graphql_api.data_s3.data_manager import DataManager
from .custom.rupture_generation import RuptureGenerationTaskConnection, CreateRuptureGenerationTask,\
    UpdateRuptureGenerationTask, RuptureGenerationTask
from requests_aws4auth import AWS4Auth

from .file import CreateFile, File, FileConnection
from .file_relation import CreateFileRelation, FileRelationConnection
from .search_manager import SearchManager

from graphql_api.schema import file, event, thing
#from .custom import strong_motion_station, strong_motion_station_file, sms_file_link, rupture_generation

from .custom.strong_motion_station import CreateStrongMotionStation, StrongMotionStation,\
    StrongMotionStationConnection
from .custom.strong_motion_station_file import CreateSmsFile, SmsFile
from graphql_api.data_s3 import get_data_manager
# from .custom.sms_file_link import SmsFileLink, SmsFileLinkConnection, CreateSmsFileLink, SmsFileType
from .custom.grand_inversion import GrandInversionTask, CreateGrandInversionTask, GrandInversionTaskConnection
from .custom.general_task import GeneralTask, CreateGeneralTask
from .task_task_relation import CreateTaskTaskRelation

if ("-local" in os.environ.get('S3_BUCKET_NAME', "-local")):
    #S3 local credentials
    client_args = dict(aws_access_key_id='S3RVER',
        aws_secret_access_key='S3RVER',
        endpoint_url='http://localhost:4569')
    awsauth = None
    ES_ENDPOINT = "http://localhost:9200"
    ES_INDEX = "toshi-index"
else:
    #AWS S3 creds set up by sls
    client_args = {}
    credentials = boto3.Session().get_credentials()
    # region = '' # e.g. us-west-1
    SERVICE = 'es'
    ES_ENDPOINT = os.getenv("ES_ENDPOINT")
    ES_INDEX = os.getenv("ES_INDEX")
    ES_REGION = os.getenv("ES_REGION")
    ES_DOMAIN_NAME = os.getenv("ES_DOMAIN_NAME")
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
            ES_REGION, SERVICE, session_token=credentials.token)

search_manager = SearchManager(endpoint=ES_ENDPOINT, es_index=ES_INDEX, awsauth=awsauth)
db_root = DataManager(search_manager, client_args)

class SearchResult(graphene.Union):
    class Meta:
        types = (File, RuptureGenerationTask, StrongMotionStation, SmsFile, GeneralTask, GrandInversionTask)

class SearchResultConnection(relay.Connection):
    class Meta:
        node = SearchResult
    total_count = graphene.Field(graphene.Int, default_value=11)

class Search(graphene.ObjectType):
    ok = graphene.Boolean()
    search_result = relay.ConnectionField(SearchResultConnection)


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

    search = graphene.Field(Search, search_term=graphene.String())
    file = relay.Node.Field(File, id=graphene.ID(required=True))

    strong_motion_station = graphene.Field(StrongMotionStation, id=graphene.ID(required=True))
    strong_motion_stations = relay.ConnectionField(
        StrongMotionStationConnection,
        description="The list of strong motion stations"
    )

    def resolve_strong_motion_stations(root, info):
        return db_root.thing.get_all()


    def resolve_strong_motion_station(root, info, id):
        _type, _id = from_global_id(id)
        return db_root.thing.get_one(_id)


    @staticmethod
    def resolve_rupture_generation_tasks(root, info):
        """
        Returns:
            list: rupture generation task list
        """
        return db_root.thing.get_all() #TODO : this needs to use ES to constrain results to correct type

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

class MutationRoot(graphene.ObjectType):
    create_rupture_generation_task = CreateRuptureGenerationTask.Field()
    update_rupture_generation_task = UpdateRuptureGenerationTask.Field()
    create_file = CreateFile.Field()
    create_file_relation = CreateFileRelation.Field()
    create_strong_motion_station = CreateStrongMotionStation.Field()
    create_sms_file = CreateSmsFile.Field()
    create_general_task = CreateGeneralTask.Field()
    create_task_relation = CreateTaskTaskRelation.Field()
    create_grand_inversion_task = CreateGrandInversionTask.Field()

root_schema = graphene.Schema(query=QueryRoot, mutation=MutationRoot, auto_camelcase=False)
