"""
The NSHM data file graphql schema.
"""
import graphene
from graphene import relay
from graphql_api.data_s3 import get_data_manager
from graphql_api.schema.custom.common import KeyValuePair, KeyValuePairInput

class File(graphene.ObjectType):
    """A data file"""
    class Meta:
        """standard graphene meta class"""
        interfaces = (relay.Node, )

    file_name = graphene.String(description="The name of the file")
    md5_digest = graphene.String(description="The base64-encoded md5 digest of the file")
    file_size = graphene.Int(description="The size of the file in bytes")
    file_url = graphene.String(description="A pre-signed URL to download the file from s3")
    post_url = graphene.String(description="A pre-signed URL to post the data to s3")

    meta = graphene.List(KeyValuePair, required=False,
            description="additional file meta data, as a list of Key Value pairs.")

    relations = relay.ConnectionField(
        'graphql_api.schema.thing.FileRelationConnection', description="things related to this data file")


    def resolve_file_url(self, info, **args):
	    return get_data_manager().file.get_presigned_url(self.id)

    def resolve_relations(self, info, **args):
        # Transform the instance thing_ids into real instances
        if not self.relations: return []
        return [get_data_manager().file_relation.get_one(_id) for _id in self.relations]

    @classmethod
    def get_node(cls, info, _id):
        node = get_data_manager().file.get_one(_id)
        return node


class FileConnection(relay.Connection):
    """A Relay connection for Files"""
    class Meta:
        node = File


class CreateFile(graphene.Mutation):
    class Arguments:
        file_name = graphene.String()
        md5_digest = graphene.String("The base64-encoded md5 digest of the file")
        file_size = graphene.Int()
        meta = graphene.List(KeyValuePairInput, required=False,
            description="additional file meta data, as a list of Key Value pairs.")

    ok = graphene.Boolean()
    file_result = graphene.Field(File)

    def mutate(self, info, **kwargs):
        # print("CreateFile.mutate: ", file_in, kwargs)
        file_result = get_data_manager().file.create('File', **kwargs)
        return CreateFile(ok=True, file_result=file_result)

