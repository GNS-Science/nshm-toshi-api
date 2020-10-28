import graphene
from graphene import relay
from graphene_file_upload.scalars import Upload
from graphene import Enum

from graphql_api.data_s3 import TaskResultData, get_faction

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
                              
class CreateDataFileMutation(graphene.Mutation):
    class Arguments:
        file_name = graphene.String() # deprecated
        file_in = Upload(required=True)
        hex_digest = graphene.String("The sha256 hexdigest of the file")
        file_size = graphene.Int()

    ok = graphene.Boolean()

    def mutate(self, info, file_in, **kwargs):
        # do something with your file
        for line in file_in:
            print(line)
        print(kwargs)
        return CreateDataFileMutation(ok=True)

