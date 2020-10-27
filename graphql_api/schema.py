import graphene
from graphene import relay
from graphene_file_upload.scalars import Upload
from graphene import Enum

from .data_s3 import TaskResultData, get_faction

class TaskResultType(Enum):
    TEST_RESULT = "test_result"
    JOB_RESULT = "job_result"

class RupturePermutationStrategy(Enum):
    UCERF3 = 'ucerf3'
    DOWNDIP = 'downdip'
    POINTS = 'points'
    
class RuptureGeneratorArgs():
    max_jump_distance = graphene.Float()
    max_sub_section_length = graphene.Float()
    min_sub_sections_per_parent = graphene.Int()
    max_cumulative_azimuth = graphene.Float()
    permutation_strategy = RupturePermutationStrategy()
    
class RuptureGeneratorArgsInput(RuptureGeneratorArgs, graphene.InputObjectType):
    pass

class RuptureGeneratorArgsOutput(RuptureGeneratorArgs, graphene.ObjectType):  
    pass      

class TaskResult(graphene.Interface):
    """A TaskResult in the NSHM saga"""
    class Meta:
        interfaces = (relay.Node, ) 
        
    name = graphene.String() # deprecated
    tasktype = graphene.Field(TaskResultType) #deprecated
    started = graphene.DateTime(description="The time the task was started")
    duration = graphene.Float(description="the final duraton of the task in seconds")  
                              
class OpenshaRuptureGenResult(graphene.ObjectType):
    """An OpenshaRuptureGenResult in the NSHM process"""
    class Meta:
        interfaces = (relay.Node, TaskResult)
 
    rupture_generator_args = graphene.Field(RuptureGeneratorArgsOutput)

    @classmethod
    def get_node(cls, info, _id):
        node =  db_root.get_one(_id)
        #print('NODE', node, node.id, node.type )
        return node   
    
class OpenshaRuptureGenResultConnection(relay.Connection):
    class Meta:
        node = OpenshaRuptureGenResult
      
class CreateOpenshaRuptureGenResult(relay.ClientIDMutation):
    class Input:
        name = graphene.String() # deprecated
        tasktype = graphene.Field(TaskResultType) #deprecated        
        started = graphene.DateTime(description="The time the task was started")
        duration = graphene.Float(description="The final duraton of the task in seconds")
        rupture_generator_args = RuptureGeneratorArgsInput()
        
    task_result = graphene.Field(OpenshaRuptureGenResult)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        task_result = db_root.create(**kwargs)
        print("task_result", task_result.started)
        return CreateOpenshaRuptureGenResult(task_result=task_result)


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
