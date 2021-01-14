"""
This module contains the schema definitions used by NSHM Grand Inversion tasks.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

The core class GrandInversionTask implements the `graphql_api.schema.task.Task` Interface.

"""
import graphene
import datetime as dt
import logging

from graphene import relay
from graphene import Enum

from graphql_api.schema.event import EventResult, EventState
from graphql_api.schema.thing import Thing
from graphql_api.data_s3 import get_data_manager
from .common import GitReferencesInput, GitReferencesOutput

logger = logging.getLogger(__name__)

class EnergyChangeCompletionCriteria():
    energy_delta = graphene.Float(description="The minimum absolute delta (previousE - e ) to signifiy completion. Set to 0 to ignore.")
    energy_percent_delta = graphene.Float(description="The minimum percentage delta (e as percentage of previousE) to signifiy completion. Set to 0 to ignore.")
    look_back_mins = graphene.Float(description="How many minutes to look back for the previousE value")

class EnergyChangeCompletionCriteriaInput(EnergyChangeCompletionCriteria, graphene.InputObjectType):
     """Arguments passed into the opensha Grand Inversion task"""

class EnergyChangeCompletionCriteriaOutput(EnergyChangeCompletionCriteria, graphene.ObjectType):
    """Arguments passed into the opensha Grand Inversion task"""

class TimeCompletionCriteria():
    minutes = graphene.Int(description="the number of minutes to run (maximum)")

class TimeCompletionCriteriaInput(TimeCompletionCriteria, graphene.InputObjectType):
    pass

class TimeCompletionCriteriaOutput(TimeCompletionCriteria, graphene.ObjectType):
    pass

class GrandInversionConstraintType(Enum):
    """supported contraints"""
    MFD_Inequality = 'mfd_equality'
    MFD_Equality = 'mfd_inequality'
    Slip_Rate = 'slip_rate'

class GrandInversionConstraint():
    """Arguments for opensha GrandInversionConstraints"""
    constraint_type = graphene.Field(GrandInversionConstraintType)
    constraint_weight =  graphene.Int(description="Weighting for this constraint")

class GrandInversionConstraintInput(GrandInversionConstraint, graphene.InputObjectType):
     """Arguments passed into the opensha Grand Inversion task"""

class GrandInversionConstraintOutput(GrandInversionConstraint, graphene.ObjectType):
     """Arguments passed into the opensha Grand Inversion task"""

class GutenbergRichterMFD():
    """Arguments for the opensha GutenbergRichterMagFreqDist"""
    total_rate_m5 = graphene.Float(
        description="The expected number of M>=5's ruptures per year. TODO: OK? ref David Rhodes/Chris Roland? [KKS, CBC]")
    b_value =  graphene.Float(
        description="G-R b-value")
    mfd_min = graphene.Float(
        description="Minimum magnitude 5.05d")
    mfd_max = graphene.Float(
        description="Maximum magnitude 8.85d")
    mfd_transition_mag = graphene.Float(
        description="magnitude to switch from MFD equality to MFD inequality. TODO: how to validate this number for NZ? (ref Morgan Page in USGS/UCERF3) [KKS, CBC]")
    mfd_num = graphene.Int(
        description="Number of MFD buckets?")
    # mfd_equality_constraint_weight =  graphene.Int(
    #     description="Weighting for MFD equality constraint")
    # mfd_inequality_constraint_weight = graphene.Int(
    #     description="Weighting for the MFD inequality constraint")
    # smoothness_constraint_weight = graphene.Int(
    #     description="Weighting for the entropy-maximization constraint (not used in UCERF3)")

class GutenbergRichterMFDInput(GutenbergRichterMFD, graphene.InputObjectType):
    pass

class GutenbergRichterMFDOutput(GutenbergRichterMFD, graphene.ObjectType):
    pass


class GrandInversionArgsInput(graphene.InputObjectType):
    """Arguments passed into the opensha Grand Inversion task"""
    sync_interval = graphene.Int(description="interval in seconds between annealing thread syncs")
    gutenberg_richter_mfd = graphene.Field(GutenbergRichterMFDInput)
    energy_completion_criteria = graphene.Field(EnergyChangeCompletionCriteriaInput)
    time_completion_criteria = graphene.Field(TimeCompletionCriteriaInput)
    constraints = graphene.List(GrandInversionConstraintInput)

class GrandInversionArgsOutput(graphene.ObjectType):
    """Arguments passed into the opensha Grand Inversion task"""
    sync_interval = graphene.Int(description="interval in seconds between annealing thread syncs")
    gutenberg_richter_mfd = graphene.Field(GutenbergRichterMFDOutput)
    energy_completion_criteria = graphene.Field(EnergyChangeCompletionCriteriaOutput)
    time_completion_criteria = graphene.Field(TimeCompletionCriteriaOutput)
    constraints = graphene.List(GrandInversionConstraintOutput)

class GrandInversionMetrics():
    """output metrics from the opensha Rupture Generator"""
    total_energy = graphene.Float(
        description="Final inversion energy total.")
    subsection_count = graphene.Int(
        description="Count of fault subsections.")

class GrandInversionMetricsInput(GrandInversionMetrics, graphene.InputObjectType):
    """The metrics returned from the opensha Rupture Generator"""

class GrandInversionMetricsOutput(GrandInversionMetrics, graphene.ObjectType):
    """The metrics returned from the opensha Rupture Generator"""


class GrandInversionTask(graphene.ObjectType):
    """An GrandInversionTask in the NSHM process"""
    class Meta:
        interfaces = (relay.Node, Thing)

    result = EventResult()
    state = EventState()

    created = graphene.DateTime(description="The time the event was created")
    duration = graphene.Float(description="the final duraton of the event in seconds")

    parents = relay.ConnectionField(
        'graphql_api.schema.task_task_relation.TaskTaskRelationConnection',
        description="parent task(s) of this task")

    arguments = graphene.Field(GrandInversionArgsOutput)
    metrics = graphene.Field(GrandInversionMetricsOutput)
    git_refs = graphene.Field(GitReferencesOutput)

    def resolve_parents(self, info, **args):
        # Transform the instance thing_ids into real instances
        if not self.parents: return []
        return [get_data_manager().thing_relation.get_one(_id) for _id in self.parents]


    @classmethod
    def get_node(cls, info, _id):
        return  get_data_manager().thing.get_one(_id)

    @staticmethod
    def from_json(jsondata):
        #Field type transforms...
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.datetime.fromisoformat(created)
        logger.info("from_json: %s" % str(jsondata))
        return GrandInversionTask(**jsondata)

class GrandInversionTaskConnection(relay.Connection):
    """A list of GrandInversionTask items"""
    class Meta:
        node = GrandInversionTask

class CreateGrandInversionTask(relay.ClientIDMutation):
    class Input:
        result = EventResult(required=True)
        state = EventState(required=True)
        created = graphene.DateTime(description="The time the task was created", )
        duration = graphene.Float(description="The final duraton of the task in seconds")
        arguments = GrandInversionArgsInput(description="The input arguments for the Rupture generator")
        metrics = GrandInversionMetricsInput(description="The metrics from rupture generation")
        git_refs = GitReferencesInput(description="The git references for the software")

    task_result = graphene.Field(GrandInversionTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        task_result = get_data_manager().thing.create('GrandInversionTask', **kwargs)
        return CreateGrandInversionTask(task_result=task_result)


class UpdateGrandInversionTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)
        result = EventResult(required=False)
        state = EventState(required=False)
        created = graphene.DateTime(required=False, description="The time the task was created")
        duration = graphene.Float(required=False, description="The final duraton of the task in seconds")
        arguments = GrandInversionArgsInput(required=False, description="The input arguments for the  Grand Inversion task")
        metrics = GrandInversionMetricsInput(required=False, description="The metrics from the Inversion task")
        git_refs = GitReferencesInput(description="The git references for the software")

    task_result = graphene.Field(GrandInversionTask)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        thing_id = kwargs.pop('task_id')
        task_result = get_data_manager().thing.update('GrandInversionTask', thing_id, **kwargs)

        return UpdateGrandInversionTask(task_result=task_result)