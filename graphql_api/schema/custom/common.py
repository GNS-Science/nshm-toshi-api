import graphene
from graphql_relay import from_global_id
from enum import Enum

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
    SOLUTION_TO_NRML = "solution_to_nrml"
    OPENQUAKE_HAZARD = "openquake_hazard"

class ModelType(graphene.Enum):
    CRUSTAL = "crustal"
    SUBDUCTION = "subduction"
    COMPOSITE = "composite"


class AncestryLabel(Enum):
    sibling = 0
    parent = -1
    grandparent = -2
    great_grandparent = -3
    great_great_grandparent = -4

class Predecessor(graphene.ObjectType):
    """
    Represents a something that came before this thing.

    """
    id = graphene.ID(description="The id of the predecessor object")
    typename = graphene.Field(graphene.String, description="The typename of the predecessor object")
    depth = graphene.Field(graphene.Int, description="The predecessor relationship numerically")
    relationship = graphene.Field(graphene.String, description="The predecessor relationship in Title case.")

    def resolve_typename(root, info, **args):
        idn = getattr(root, 'id')
        typename, ident = from_global_id(idn)
        return typename

    def resolve_relationship(root, info, **args):
        d = int(getattr(root, 'depth'))
        return str(AncestryLabel(d).name.title())


class PredecessorInput(graphene.InputObjectType):
    """
    Represents a something that came before this thing.

    """
    id = Predecessor.id
    depth = graphene.Field(graphene.Int, description="The predecessor relationship numerically")
