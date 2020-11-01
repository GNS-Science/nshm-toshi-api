'''
Created on 28/10/2020

@author: chrisbc
'''
from graphql_api.schema.schema import schema
from graphql_api.schema.opensha_task import OpenshaRuptureGenResult, OpenshaRuptureGenResultConnection,  CreateOpenshaRuptureGenResult
from graphql_api.schema.task_result import TaskResult, TaskResultType
from graphql_api.schema.data_file import DataFile, DataFileConnection, CreateDataFileMutation
from graphql_api.schema.task_file import TaskFile