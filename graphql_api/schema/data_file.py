"""
The NSHM data file graphql schema.
"""
import base64
import graphene
from graphene import relay
from graphene_file_upload.scalars import Upload
from graphql_api.data_s3 import DataManager

global db_root

class DataFile(graphene.ObjectType):
    """A data file used in some TaskResult """
    class Meta:
        interfaces = (relay.Node, )
 
    file_name = graphene.String(description="The name of the file")
    hex_digest = graphene.String(description="The sha256 hexdigest of the file")
    file_size = graphene.Int(description="The size of the file in bytes")
    file_url = graphene.String(description="A pre-signed URL to download the file from s3")

    def resolve_file_url(self, info, **args):
	    return db_root.file.get_presigned_url(self.id)

    @classmethod
    def get_node(cls, info, _id):
        print("GETNODE")
        node = db_root.file.get_one(_id)
        return node   
    
class DataFileConnection(relay.Connection):
    """A Relay connection listing DataFiles"""
    class Meta:
        node = DataFile

class CreateDataFileMutation(graphene.Mutation):
    class Arguments:
        file_name = graphene.String()
        file_in = Upload(required=True)
        hex_digest = graphene.String("The sha256 hexdigest of the file")
        file_size = graphene.Int()

    ok = graphene.Boolean()
    file_result = graphene.Field(DataFile)

    def mutate(self, info, file_in, **kwargs):
        print("CreateDataFileMutation.mutate: ", file_in, kwargs)
        file_result = db_root.file.create(file_in, **kwargs)
        return CreateDataFileMutation(ok=True, file_result=file_result)

