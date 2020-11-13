'''
Created on 28/10/2020

@author: chrisbc
'''
import os
import graphene
from graphene import relay
from graphql_api.data_s3 import DataManager
from graphql_api.schema.opensha_task import RuptureGenerationTaskConnection, CreateRuptureGenerationTask,\
    UpdateRuptureGenerationTask
from graphql_api.schema.file import CreateFile, File, FileConnection
from graphql_api.schema import opensha_task, file, task, task_file
from .task_file import CreateTaskFile
from .search_manager import SearchManager


class Search(graphene.Mutation):
    class Arguments:
        search_term = graphene.String(required=True)

    ok = graphene.Boolean()
    search_result = graphene.String()

    def mutate(root, info, search_term, **kwargs):
        # print("CreateFile.mutate: ", file_in, kwargs)
        print('mutate(self, info, search_term= ', search_term )
        search_result = db_root.search_manager.search(search_term)
        return Search(ok=True, search_result=search_result)

class Query(graphene.ObjectType):
    """This is the entry point for all graphql query operations"""

    rupture_generation_tasks = relay.ConnectionField(
        RuptureGenerationTaskConnection,
        description="The OpenshaRuptureGen tasks."
    )

    files = relay.ConnectionField(
        FileConnection,
        description="The files."
    )

    node = relay.Node.Field()
    file = relay.Node.Field(File, id=graphene.ID(required=True))

    @staticmethod
    def resolve_rupture_generation_tasks(root, info):
        """
        Returns:
            list: rupture generation task list
        """
        return db_root.task.get_all()

    @staticmethod
    def resolve_files(root, info):
        """
        Returns:
            list: file list
        """
        return db_root.file.get_all()

class Mutation(graphene.ObjectType):
    create_rupture_generation_task = CreateRuptureGenerationTask.Field()
    update_rupture_generation_task = UpdateRuptureGenerationTask.Field()
    create_file = CreateFile.Field()
    create_task_file = CreateTaskFile.Field()
    search = Search.Field()

if ("-local" in os.environ.get('S3_BUCKET_NAME', "-local")):
    #S3 local credentials
    client_args = dict(aws_access_key_id='S3RVER',
              aws_secret_access_key='S3RVER',
              endpoint_url='http://localhost:4569')
else:
    #AWS S3 creds set up by sls
    client_args = {}


search_manager = SearchManager()
db_root = DataManager(search_manager, client_args)

opensha_task.db_root = db_root
file.db_root = db_root
task.db_root = db_root
task_file.db_root = db_root

schema = graphene.Schema(query=Query, mutation=Mutation)