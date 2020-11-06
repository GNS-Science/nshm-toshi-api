import graphene
from graphene import relay
from graphene_file_upload.scalars import Upload
from graphene import Enum

global db_root

# class TaskResultType(Enum):
#     TEST_RESULT = "test_result"
#     JOB_RESULT = "job_result"

class Task(graphene.Interface):
    """A Task in the NSHM saga"""
    class Meta:
        interfaces = (relay.Node, ) 
    
    started = graphene.DateTime(description="The time the task was started")
    duration = graphene.Float(description="the final duraton of the task in seconds")  
    
    input_files = relay.ConnectionField(
         'graphql_api.schema.task_file.TaskFileConnection', description="input files used for this task."
    )

    def resolve_input_files(self, info, **args):
        # Transform the instance ship_ids into real instances
        return [db_root.task_file.get_one(_id) for _id in self.input_files]
    



