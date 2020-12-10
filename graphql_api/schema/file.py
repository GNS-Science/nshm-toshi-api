"""
The NSHM data file graphql schema.
"""
import graphene
from graphene import relay
from graphql_api.data_s3 import DataManager

global db_root

class File(graphene.ObjectType):
    """A data file  """
    class Meta:
        interfaces = (relay.Node, )

    file_name = graphene.String(description="The name of the file")
    md5_digest = graphene.String(description="The base64-encoded md5 digest of the file")
    file_size = graphene.Int(description="The size of the file in bytes")
    file_url = graphene.String(description="A pre-signed URL to download the file from s3")
    post_url = graphene.String(description="A pre-signed URL to post the data to s3")

    things = relay.ConnectionField(
        'graphql_api.schema.thing.FileThingRelationConnection', description="things related to this data file")


    def resolve_file_url(self, info, **args):
	    return db_root.file.get_presigned_url(self.id)

    def resolve_things(self, info, **args):
        # Transform the instance thing_ids into real instances
        if not self.things: return []
        return [db_root.file_relation.get_one(_id) for _id in self.things]


    @classmethod
    def get_node(cls, info, _id):
        node = db_root.file.get_one(_id)
        return node

class FileConnection(relay.Connection):
    """A Relay connection for Files"""
    class Meta:
        node = File

class CreateFile(graphene.Mutation):
    class Arguments:
        file_name = graphene.String()
        md5_digest = graphene.String("The base64-encoded md5 digest  of the file")
        file_size = graphene.Int()

    ok = graphene.Boolean()
    file_result = graphene.Field(File)

    def mutate(self, info, **kwargs):
        # print("CreateFile.mutate: ", file_in, kwargs)
        file_result = db_root.file.create(**kwargs)
        return CreateFile(ok=True, file_result=file_result)

