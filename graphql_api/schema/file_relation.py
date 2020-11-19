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

    #created = graphene.DateTime(description="The time the relation was created")
    thing = graphene.Field('graphql_api.schema.thing.Thing', required=True)
    file = graphene.Field(File, required=True)

    thing_id = graphene.String()
    file_id = graphene.String()

    # def resolve_file(root, info, **kwargs):
    #      print('resolve_file', kwargs, info, root, root.file)
    #      _type, _id = from_global_id(kwargs.id)
    #      return db_root.file.get_one(_id)


    # def resolve_thing(root, info, id):
    #      _type, _id = from_global_id(id)
    #      print('HHHHH')
    #      return db_root.thing.get_one(_id)


