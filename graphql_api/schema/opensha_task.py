"""
This module contains the schema definitions used by NSHM Rupture Generation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

The core class RuptureGenerationTask implements the `graphql_api.schema.task.Task` Interface.

"""
import graphene
from graphene import relay
from graphene import Enum

from graphql_api.schema.task import Task, TaskResult, TaskState

global db_root

class RupturePermutationStrategy(Enum):
    """The available rupture generation strategies"""
    UCERF3 = 'ucerf3'
    DOWNDIP = 'downdip'
    POINTS = 'points'

class RuptureGenerationArgs():
    """Arguments passed into the opensha Rupture Generator"""
    max_jump_distance = graphene.Float(
        description="Maximum jump distance in km")
    max_sub_section_length = graphene.Float(
        description="maximum ratio of subsection length to DDW for building subsections. Default is 0.5")
    min_sub_sections_per_parent = graphene.Int(
        description="Minimum subsections per parent allowed in a rupture. Default is 2")
    max_cumulative_azimuth = graphene.Float(
        description="Maximum aggregated azimuth change allowed in a rupture.")
    permutation_strategy = RupturePermutationStrategy(
        description="The rupture permutation strategy to use")

class RuptureGenerationArgsInput(RuptureGenerationArgs, graphene.InputObjectType):
    """Arguments passed into the opensha Rupture Generator"""

class RuptureGenerationArgsOutput(RuptureGenerationArgs, graphene.ObjectType):
    """Arguments passed into the opensha Rupture Generator"""


class GitReferences():
    """Source code git references (from `git log --oneline -1`)"""
    opensha_ucerf3 = graphene.String(
        description="git ref for opensha-ucerf3")
    opensha_commons = graphene.String(
        description="git ref for opensha-commons")
    opensha_core = graphene.String(
        description="git ref for opensha-core")
    nshm_nz_opensha = graphene.String(
        description="git ref for nshm-nz-opensha")

class GitReferencesInput(GitReferences, graphene.InputObjectType):
    """Arguments passed into the opensha Rupture Generator"""

class GitReferencesOutput(GitReferences, graphene.ObjectType):
    """Arguments passed into the opensha Rupture Generator"""


class RuptureGenerationMetrics():
    """output metrics from the opensha Rupture Generator"""
    rupture_count = graphene.Int(
        description="Count of ruptures produced.")
    subsection_count = graphene.Int(
        description="Count of fault subsections produced.")
    possible_cluster_connection_count = graphene.Int(
        description="Count of cluster connections (deprecated")
    cluster_connection_count = graphene.Int(
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
    git_refs = graphene.Field(GitReferencesOutput)

    @classmethod
    def get_node(cls, info, _id):
        return  db_root.task.get_one(_id)

class RuptureGenerationTaskConnection(relay.Connection):
    """A list of RuptureGenerationTask items"""
    class Meta:
        node = RuptureGenerationTask

class CreateRuptureGenerationTask(relay.ClientIDMutation):
    class Input:
        result = TaskResult(required=True)
        state = TaskState(required=True)
        started = graphene.DateTime(description="The time the task was started", )
        duration = graphene.Float(description="The final duraton of the task in seconds")
        arguments = RuptureGenerationArgsInput(description="The input arguments for the Rupture generator")
        metrics = RuptureGenerationMetricsInput(description="The metrics from rupture generation")
        git_refs = GitReferencesInput(description="The git references for the software")

    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        task_result = db_root.task.create(**kwargs)
        return CreateRuptureGenerationTask(task_result=task_result)


class UpdateRuptureGenerationTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)
        result = TaskResult(required=False)
        state = TaskState(required=False)
        started = graphene.DateTime(required=False, description="The time the task was started")
        duration = graphene.Float(required=False, description="The final duraton of the task in seconds")
        arguments = RuptureGenerationArgsInput(required=False, description="The input arguments for the Rupture generator")
        metrics = RuptureGenerationMetricsInput(required=False, description="The metrics from rupture generation")
        git_refs = GitReferencesInput(description="The git references for the software")

    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        task_result = db_root.task.update(**kwargs)

        return UpdateRuptureGenerationTask(task_result=task_result)