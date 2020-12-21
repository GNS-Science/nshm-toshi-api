"""
This module contains the schema definitions used by NSHM Rupture Generation tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

The core class RuptureGenerationTask implements the `graphql_api.schema.task.Task` Interface.

"""


import graphene
import datetime as dt
import logging

from graphene import relay
from graphene import Enum
# from benedict import benedict


from graphql_api.schema.event import EventResult, EventState
from graphql_api.schema.thing import Thing
from graphql_api.data_s3 import get_data_manager


logger = logging.getLogger(__name__)


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

def rename(dict_obj, from_name, to_name):
    """Rename a dict field if it exists
    Args:
        dict_obj (dict): container dict
        from_name (String): original field name
        to_name (String): ned field name
    """
    ren = dict_obj.pop(from_name, None)
    if ren:
        dict_obj[to_name] = ren

class RuptureGenerationTask(graphene.ObjectType):
    """An RuptureGenerationTask in the NSHM process"""
    class Meta:
        interfaces = (relay.Node, Thing)

    result = EventResult()
    state = EventState()

    created = graphene.DateTime(description="The time the event was created")
    duration = graphene.Float(description="the final duraton of the event in seconds")

    arguments = graphene.Field(RuptureGenerationArgsOutput)
    metrics = graphene.Field(RuptureGenerationMetricsOutput)
    git_refs = graphene.Field(GitReferencesOutput)

    @classmethod
    def get_node(cls, info, _id):
        return  get_data_manager().thing.get_one(_id)

    @staticmethod
    def from_json(jsondata):
        #Field type transforms...
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.datetime.fromisoformat(started)
        logger.info("get_one: %s" % str(jsondata))

        # arguments = jsondata.pop("rupture_generation_args", None)
        # if arguments:
        #     jsondata['arguments'] = arguments
        # arguments = jsondata.pop("rupture_generator_args", None)
        # if arguments:
        #     jsondata['arguments'] = arguments

        #remove deprecated field(s)...
        jsondata.pop('input_files', None)
        # jsondata.pop('data_files', None)
        jsondata.pop('client_mutation_id', None)

        #rename fields
        # jsondata.rename('input_files', 'files')
        rename(jsondata, 'rupture_generator_args', 'rupture_generation_args')
        rename(jsondata, 'rupture_generation_args', 'arguments')

        # #add new fields
        if not jsondata.get('input_files'):
            jsondata['input_files'] = []
        if not jsondata.get('state'):
            jsondata['state'] = EventState.UNDEFINED
        if not jsondata.get('result'):
            jsondata['result'] = EventResult.UNDEFINED
        if not jsondata.get('files'):
             jsondata['files'] = []


        ren = jsondata.pop('input_files', None)
        if ren:
            jsondata['files'] = ren

        # print('updated json', jsondata)
        return RuptureGenerationTask(**jsondata)

class RuptureGenerationTaskConnection(relay.Connection):
    """A list of RuptureGenerationTask items"""
    class Meta:
        node = RuptureGenerationTask

class CreateRuptureGenerationTask(relay.ClientIDMutation):
    class Input:
        result = EventResult(required=True)
        state = EventState(required=True)
        created = graphene.DateTime(description="The time the task was created", )
        duration = graphene.Float(description="The final duraton of the task in seconds")
        arguments = RuptureGenerationArgsInput(description="The input arguments for the Rupture generator")
        metrics = RuptureGenerationMetricsInput(description="The metrics from rupture generation")
        git_refs = GitReferencesInput(description="The git references for the software")

    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        task_result = get_data_manager().thing.create('RuptureGenerationTask', **kwargs)
        return CreateRuptureGenerationTask(task_result=task_result)


class UpdateRuptureGenerationTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)
        result = EventResult(required=False)
        state = EventState(required=False)
        created = graphene.DateTime(required=False, description="The time the task was created")
        duration = graphene.Float(required=False, description="The final duraton of the task in seconds")
        arguments = RuptureGenerationArgsInput(required=False, description="The input arguments for the Rupture generator")
        metrics = RuptureGenerationMetricsInput(required=False, description="The metrics from rupture generation")
        git_refs = GitReferencesInput(description="The git references for the software")

    task_result = graphene.Field(RuptureGenerationTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        thing_id = kwargs.pop('task_id')
        task_result = get_data_manager().thing.update('RuptureGenerationTask', thing_id, **kwargs)

        return UpdateRuptureGenerationTask(task_result=task_result)