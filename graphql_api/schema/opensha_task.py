"""
This module contains the schema definitions used by NSHM Rupture Generation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

The core class RuptureGenerationTask implements the `graphql_api.schema.task_result.TestResult` Interface.

"""
import graphene
from graphene import relay
from graphene import Enum

from graphql_api.schema.task import Task

global db_root

class RupturePermutationStrategy(Enum):
    """The available rupture generation strategies"""
    UCERF3 = 'ucerf3'
    DOWNDIP = 'downdip'
    POINTS = 'points'

class RuptureGenerationArgs():
    """Arguments passed into the opensha Rupture Generator"""
    max_jump_distance = graphene.Float(required=True,
        description="Maximum jump distance in km")
    max_sub_section_length = graphene.Float(required=True,
        description="maximum ratio of subsection length to DDW for building subsections. Default is 0.5")
    min_sub_sections_per_parent = graphene.Int(required=True,
        description="Minimum subsections per parent allowed in a rupture. Default is 2")
    max_cumulative_azimuth = graphene.Float(required=True,
        description="Maximum aggregated azimuth change allowed in a rupture.")
    permutation_strategy = RupturePermutationStrategy(required=True,
        description="The rupture permutation strategy to use")
    #git repo refs
    opensha_ucerf3_git_ref = graphene.String(required=True,
        description="git ref for opensha-ucerf3")
    opensha_commons_git_ref = graphene.String(required=True,
        description="git ref for opensha-commons")
    opensha_core_git_ref = graphene.String(required=True,
        description="git ref for opensha-core")
    nshm_nz_opensha_git_ref = graphene.String(required=True,
        description="git ref for nshm-nz-opensha")

class RuptureGenerationArgsInput(RuptureGenerationArgs, graphene.InputObjectType):
    """Arguments passed into the opensha Rupture Generator"""

class RuptureGenerationArgsOutput(RuptureGenerationArgs, graphene.ObjectType):
    """Arguments passed into the opensha Rupture Generator"""

class RuptureGenerationMetrics():
    """output metrics from the opensha Rupture Generator"""
    rupture_count = graphene.Int(required=True,
        description="Count of ruptures produced.")
    subsection_count = graphene.Int(required=True,
        description="Count of fault subsections produced.")
    possible_cluster_connection_count = graphene.Int(required=False,
        description="Count of cluster connections (deprecated")
    cluster_connection_count = graphene.Int(required=True,
        description="Count of cluster connections produced. NB both jump directions are considered.")

class RuptureGenerationMetricsInput(RuptureGenerationMetrics, graphene.InputObjectType):
    """The metrics returned from the opensha Rupture Generator"""

class RuptureGenerationMetricsOutput(RuptureGenerationMetrics, graphene.ObjectType):
    """The metrics returned from the opensha Rupture Generator"""


class RuptureGenerationTask(graphene.ObjectType):
    """An RuptureGenerationTask in the NSHM process"""
    class Meta:
        interfaces = (relay.Node, Task)

    arguments = graphene.Field(RuptureGenerationArgsOutput)
    metrics = graphene.Field(RuptureGenerationMetricsOutput)

    @classmethod
    def get_node(cls, info, _id):
        node =  db_root.task.get_one(_id)
        #print('NODE', node, node.id, node.type )
        return node

class RuptureGenerationTaskConnection(relay.Connection):
    """A list of RuptureGenerationTask items"""
    class Meta:
        node = RuptureGenerationTask

class CreateRuptureGenerationTask(relay.ClientIDMutation):
    class Input:
        started = graphene.DateTime(required=True, description="The time the task was started")
        duration = graphene.Float(required=False, description="The final duraton of the task in seconds")
        arguments = RuptureGenerationArgsInput(description="The input arguments for the Rupture generator")
        metrics =RuptureGenerationMetricsInput(required=False)

    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        task_result = db_root.task.create(**kwargs)
        print("task_result", task_result.started)
        return CreateRuptureGenerationTask(task_result=task_result)


class UpdateRuptureGenerationTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)
        started = graphene.DateTime(required=False, description="The time the task was started", )
        duration = graphene.Float(required=False, description="The final duraton of the task in seconds")
        arguments = RuptureGenerationArgsInput(required=False, description="The input arguments for the Rupture generator")
        metrics = RuptureGenerationMetricsInput(required=False, description="The metrics from rupture generation")

    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)

        task_result = db_root.task.update(**kwargs)
        print("task_result", task_result.started)
        return UpdateRuptureGenerationTask(task_result=task_result)