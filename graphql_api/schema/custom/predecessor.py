import graphene
from enum import Enum
from graphql_relay import from_global_id
from .scaled_inversion_solution import ScaledInversionSolution
from .inversion_solution_nrml import InversionSolutionNrml
from .inversion_solution import InversionSolution
from graphql_api.schema.file import File

from graphql_api.data import get_data_manager

class AncestryLabel(Enum):
    sibling = 0
    parent = -1
    grandparent = -2
    great_grandparent = -3
    great_great_grandparent = -4

class PredecessorUnion(graphene.Union):
    class Meta:
        types = (File, InversionSolution, ScaledInversionSolution, InversionSolutionNrml)

class Predecessor(graphene.ObjectType):
    """
    Represents a something that came before this thing.

    """
    id = graphene.ID(description="The id of the predecessor object")
    typename = graphene.Field(graphene.String, description="The typename of the predecessor object")
    depth = graphene.Field(graphene.Int, description="The predecessor relationship numerically")
    relationship = graphene.Field(graphene.String, description="The predecessor relationship in Title case.")
    node = graphene.Field(PredecessorUnion)

    def resolve_typename(root, info, **args):
        idn = getattr(root, 'id')
        typename, ident = from_global_id(idn)
        return typename

    def resolve_relationship(root, info, **args):
        d = int(getattr(root, 'depth'))
        return str(AncestryLabel(d).name.title())

    def resolve_node(root, info, **args):
        node_id = getattr(root, 'id')
        _type, nid = from_global_id(node_id)
        print(f'Predecessor.resolve_node: {_type} {nid}')

        return get_data_manager().file.get_one(nid)

class PredecessorInput(graphene.InputObjectType):
    """
    Represents a something that came before this thing.

    """
    id = Predecessor.id
    depth = graphene.Field(graphene.Int, description="The predecessor relationship numerically")
