'''
Created on 28/10/2020

@author: chrisbc
'''
import graphene
from graphene import relay
from graphql_api.schema.opensha_task import OpenshaRuptureGenResultConnection,  CreateOpenshaRuptureGenResult
from graphql_api.schema.task_result import CreateDataFileMutation
from graphql_api.data_s3 import TaskResultData

class Query(graphene.ObjectType):
    rupture_generator_results = relay.ConnectionField(
        OpenshaRuptureGenResultConnection, description="The OpenshaRuptureGenResults."
    )
    #     opensha_rupture_get_results = graphene.Field(OpenshaRuptureGenResult)
    node = relay.Node.Field()

    def resolve_rupture_get_result(root, info):
        return db_root.get_one()

    def resolve_rupture_generator_results(root, info):
        return db_root.get_all()

class Mutation(graphene.ObjectType):
    create_task_result = CreateOpenshaRuptureGenResult.Field()
    create_data_file = CreateDataFileMutation.Field()

db_root = TaskResultData()
schema = graphene.Schema(query=Query, mutation=Mutation)