import graphene
from graphene import relay
from graphene_file_upload.scalars import Upload

from .data import create_tosh, get_faction, get_tosh, get_toshs


class Tosh(graphene.ObjectType):
    """A tosh in the Star Wars saga"""

    class Meta:
        interfaces = (relay.Node,)

    name = graphene.String(description="The name of the tosh.")

    @classmethod
    def get_node(cls, info, id):
        return get_tosh(id)


class ToshConnection(relay.Connection):
    class Meta:
        node = Tosh

class Faction(graphene.ObjectType):
    """A faction in the Star Wars saga"""

    class Meta:
        interfaces = (relay.Node,)

    name = graphene.String(description="The name of the faction.")
    toshs = relay.ConnectionField(
        ToshConnection, description="The toshs used by the faction."
    )

    def resolve_toshs(self, info, **args):
        # Transform the instance tosh_ids into real instances
        return [get_tosh(tosh_id) for tosh_id in self.toshs]

    @classmethod
    def get_node(cls, info, id):
        return get_faction(id)


class CreateTosh(relay.ClientIDMutation):
    class Input:
        tosh_name = graphene.String(required=True)
        faction_id = graphene.String(required=True)

    tosh = graphene.Field(Tosh)
    faction = graphene.Field(Faction)

    @classmethod
    def mutate_and_get_payload(
        cls, root, info, tosh_name, faction_id, client_mutation_id=None
    ):
        tosh = create_tosh(tosh_name, faction_id)
        faction = get_faction(faction_id)
        return CreateTosh(tosh=tosh, faction=faction)


class ToshUploadMutation(graphene.Mutation):
    class Arguments:
        file_in = Upload(required=True)
    
    ok = graphene.Boolean()

    def mutate(self, info, file_in, **kwargs):
        # do something with your file
        for line in file_in:
            print(line)
        return ToshUploadMutation(ok=True)
    
class Query(graphene.ObjectType):
#     rebels = graphene.Field(Faction)
#     empire = graphene.Field(Faction)
    toshs = relay.ConnectionField(
        ToshConnection, description="The toshs used by the faction."
    )
    tosh = graphene.Field(Tosh)
    node = relay.Node.Field()

    def resolve_tosh(root, info):
        return get_tosh()
# 
#     def resolve_empire(root, info):
#         return get_empire()

    def resolve_toshs(root, info):
        return get_toshs()

class Mutation(graphene.ObjectType):
    create_tosh = CreateTosh.Field()
    my_upload= ToshUploadMutation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)