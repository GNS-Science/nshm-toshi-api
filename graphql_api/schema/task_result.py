import graphene
from graphene import relay
from graphene_file_upload.scalars import Upload
from graphene import Enum

from graphql_api.data_s3 import TaskResultData, get_faction

class TaskResultType(Enum):
    TEST_RESULT = "test_result"
    JOB_RESULT = "job_result"

class DataFile(graphene.ObjectType):
    """A data file used in some TaskResult """
    class Meta:
        interfaces = (relay.Node, )
 
    file_name = graphene.String(description="The name of the file")
    hex_digest = graphene.String(description="The sha256 hexdigest of the file")
    file_size = graphene.Int(description="The size of the file in bytes")
    
    @classmethod
    def get_node(cls, info, _id):
        #node =  db_root.get_one(_id)
        #return node   
        pass
    
class DataFileConnection(relay.Connection):
    """A Relay connection listing DataFiles"""
    class Meta:
        node = DataFile

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
        return []
        return [data_file(data_file_id) for data_file_id in self.data_files]
    
                             
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

