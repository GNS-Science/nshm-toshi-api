"""
"""
import graphene
from graphene import relay
from graphene import Enum
from graphql_relay import from_global_id, to_global_id

global db_root

from .file import File
# from .custom import SmsFileLink


class FileRelation(graphene.Interface):
    """A """
    class Meta:
        interfaces = (relay.Node, )

    thing = graphene.Field('graphql_api.schema.thing.Thing', required=True)
    file = graphene.Field(File, required=True)

    thing_id = graphene.String()
    file_id = graphene.String()



