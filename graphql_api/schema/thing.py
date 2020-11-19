import graphene
from graphene import relay

global db_root

class Thing(graphene.Interface):
    """A Task in the NSHM saga"""
    class Meta:
        interfaces = (relay.Node, )

    created = graphene.DateTime(description="The time the task was started")

    files = relay.ConnectionField(
         'graphql_api.schema.schema.FileThingRelationConnection', description="Files associated with this task."
    )

    def resolve_files(self, info, **args):
        # Transform the instance ship_ids into real instances
        if not self.files: return []
        return [db_root.file_relation.get_one(_id) for _id in self.files]


class ThingConnection(relay.Connection):
    """A Relay connection listing Files"""
    class Meta:
        node = Thing


