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

    tasks = relay.ConnectionField(
    	'graphql_api.schema.task_file.TaskFileConnection', description="tasks using this data file")

    def resolve_file_url(self, info, **args):
	    return db_root.file.get_presigned_url(self.id)

    def resolve_tasks(self, info, **args):
        # Transform the instance ship_ids into real instances
        if not self.tasks: return []
        return [db_root.task_file.get_one(_id) for _id in self.tasks]

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

    def mutate(self, info, file_in=None, **kwargs):
        # print("CreateFile.mutate: ", file_in, kwargs)
        file_result = db_root.file.create(file_in, **kwargs)
        return CreateFile(ok=True, file_result=file_result)

