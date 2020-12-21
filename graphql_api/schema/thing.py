import graphene
from graphene import relay
from graphene import Enum
from graphql_relay import from_global_id
from graphql_api.schema.file_relation import FileRelationConnection
from graphql_api.data_s3 import get_data_manager


class Thing(graphene.Interface):
    """A Thing in the NSHM saga"""
    class Meta:
        interfaces = (relay.Node, )

    created = graphene.DateTime(description="The time the task was started")

    files = relay.ConnectionField(
         FileRelationConnection, description="Files associated with this object."
    )

    def resolve_files(self, info, **args):
        # Transform the instance ship_ids into real instances
        if not self.files: return []
        return [get_data_manager().file_relation.get_one(_id) for _id in self.files]

class ThingConnection(relay.Connection):
    """A Relay connection listing Files"""
    class Meta:
        node = Thing
