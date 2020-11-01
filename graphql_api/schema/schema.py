'''
Created on 28/10/2020

@author: chrisbc
'''
import graphene
from graphene import relay
from graphql_api.data_s3 import DataManager
from graphql_api.schema.opensha_task import OpenshaRuptureGenResultConnection,  CreateOpenshaRuptureGenResult
from graphql_api.schema.data_file import CreateDataFileMutation, DataFile, DataFileConnection
from .task_file import TaskFile, TaskFileConnection, CreateTaskFile

from .task_result import TaskResult
from graphql_api.schema import opensha_task, data_file, task_result, task_file

class Query(graphene.ObjectType):
    rupture_generator_results = relay.ConnectionField(
        OpenshaRuptureGenResultConnection, description="The OpenshaRuptureGenResults."
    )

    data_files = relay.ConnectionField(
        DataFileConnection, description="The DataFiles."
    )
    #     opensha_rupture_get_results = graphene.Field(OpenshaRuptureGenResult)
    node = relay.Node.Field()
    data_file = relay.Node.Field(DataFile, id=graphene.ID(required=True))


    # def resolve_data_file(root, info, id):
    #     return db_root.file.get_one(id)

    def resolve_rupture_generator_results(root, info):
        return db_root.task.get_all()

    def resolve_data_files(root, info):
        return db_root.file.get_all()

class Mutation(graphene.ObjectType):
    create_task_result = CreateOpenshaRuptureGenResult.Field()
    create_data_file = CreateDataFileMutation.Field()
    create_task_file = CreateTaskFile.Field()

client_args = dict(aws_access_key_id='S3RVER', 
              aws_secret_access_key='S3RVER',
              endpoint_url='http://localhost:4569')
#client_args = {}

db_root = DataManager(client_args)
opensha_task.db_root = db_root
data_file.db_root = db_root
task_result.db_root = db_root
task_file.db_root = db_root

schema = graphene.Schema(query=Query, mutation=Mutation)