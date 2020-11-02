'''
Created on 28/10/2020

@author: chrisbc
'''
import graphene
from graphene import relay
from graphql_api.data_s3 import DataManager
from graphql_api.schema.opensha_task import OpenshaRuptureGenResultConnection,  CreateOpenshaRuptureGenResult
from graphql_api.schema.file import CreateFile, File, FileConnection
from graphql_api.schema import opensha_task, file, task_result, task_file
from .task_file import CreateTaskFile

class Query(graphene.ObjectType):
    rupture_generation_tasks = relay.ConnectionField(
        OpenshaRuptureGenResultConnection,
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
    create_task = CreateOpenshaRuptureGenResult.Field()
    create_file = CreateFile.Field()
    create_task_file = CreateTaskFile.Field()

client_args = dict(aws_access_key_id='S3RVER', 
              aws_secret_access_key='S3RVER',
              endpoint_url='http://localhost:4569')
#client_args = {}

db_root = DataManager(client_args)
opensha_task.db_root = db_root
file.db_root = db_root
task_result.db_root = db_root
task_file.db_root = db_root

schema = graphene.Schema(query=Query, mutation=Mutation)