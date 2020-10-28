#!python3
import graphene
from graphene import relay
from graphene import Enum

from graphql_api.schema.task_result import TaskResult, TaskResultType

class RupturePermutationStrategy(Enum):
    UCERF3 = 'ucerf3'
    DOWNDIP = 'downdip'
    POINTS = 'points'
    
class RuptureGeneratorArgs():
    """Arguments passed into the Rupture Generator"""
    max_jump_distance = graphene.Float()
    max_sub_section_length = graphene.Float()
    min_sub_sections_per_parent = graphene.Int()
    max_cumulative_azimuth = graphene.Float()
    permutation_strategy = RupturePermutationStrategy()
    
class RuptureGeneratorArgsInput(RuptureGeneratorArgs, graphene.InputObjectType):
    """Arguments passed into the Rupture Generator"""


class RuptureGeneratorArgsOutput(RuptureGeneratorArgs, graphene.ObjectType):
    """Arguments passed into the Rupture Generator"""


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
    