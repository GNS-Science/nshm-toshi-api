import graphene
from graphene import relay
from graphene_file_upload.scalars import Upload
from graphene import Enum

from graphql_api.schema.data_file import DataFileConnection

global db_root

class TaskResultType(Enum):
    TEST_RESULT = "test_result"
    JOB_RESULT = "job_result"

class TaskResult(graphene.Interface):
    """A TaskResult in the NSHM saga"""
    class Meta:
        interfaces = (relay.Node, ) 
        
    name = graphene.String() # deprecated
    tasktype = graphene.Field(TaskResultType) #deprecated
    started = graphene.DateTime(description="The time the task was started")
    duration = graphene.Float(description="the final duraton of the task in seconds")  
    data_files = relay.ConnectionField(
        DataFileConnection, description="The files linked to the test result."
    )

    def resolve_data_files(self, info, **args):
        # Transform the instance ship_ids into real instances
        return [db_root.task.get_files()]
        # return [data_file(data_file_id) for data_file_id in self.data_files]
    



