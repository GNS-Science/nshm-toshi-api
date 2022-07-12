import graphene

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

class KeyValuePair(graphene.ObjectType):
    """Simple container for string-based KV pair data"""
    k = graphene.String(description="key")
    v = graphene.String(description="value")


class KeyValuePairInput(graphene.InputObjectType):
    """Simple container for string-based KV pair data"""
    k = graphene.String(description="key")
    v = graphene.String(description="value")


class KeyValueListPair(graphene.ObjectType):
    """Simple container for KVL lists of strings"""
    k = graphene.String(description="key")
    v = graphene.List(graphene.String, description="list of values")


class KeyValueListPairInput(graphene.InputObjectType):
    """Simple container for KVL lists of strings"""
    k = KeyValueListPair.k
    v = KeyValueListPair.v

class TaskSubType(graphene.Enum):
    RUPTURE_SET = "rupture_set"
    INVERSION = "inversion"
    HAZARD = "hazard"
    REPORT = "report"
    SCALE_SOLUTION = "scale_solution"
    AGGREGATE_SOLUTION = "aggregate_solution"
    SOLUTION_TO_NRML = "solution_to_nrml"
    OPENQUAKE_HAZARD = "openquake_hazard"
    TIME_DEPENDENT_SOLUTION = "time_dependent_solution"

class ModelType(graphene.Enum):
    CRUSTAL = "crustal"
    SUBDUCTION = "subduction"
    COMPOSITE = "composite"

class AggregationFn(graphene.Enum):
    MEAN = "mean"

class PredecessorsInterface(graphene.Interface):
    """A interface for things having predecessors"""

    predecessors = graphene.List('graphql_api.schema.custom.predecessor.Predecessor', required=False,
        description="list of predecessor info")
 