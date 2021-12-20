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

    created = graphene.DateTime(description="When the thing was created")

    files = relay.ConnectionField(
         FileRelationConnection, description="Files associated with this object."
    )

    def resolve_files(root, info, **args):
        if not root.files: return []

        #OPTIMISE return list of None, if total count is the ONLY field selection
        if len(info.field_asts[0].selection_set.selections)==1:
            if info.field_asts[0].selection_set.selections[0].name.value == 'total_count':
                return FileRelationConnection(edges= [None for x in range(len(root.files))])

        if isinstance(root.files[0], dict):
            #new form, files is list of objects
            return [get_data_manager().file_relation.build_one(file['file_id'], root.id, file['file_role']) for file in root.files]
        else:
            #old form, files is list of strings
            return [get_data_manager().file_relation.get_one(_id) for _id in root.files]

class ThingConnection(relay.Connection):
    """A Relay connection listing Things"""
    class Meta:
        node = Thing

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)
