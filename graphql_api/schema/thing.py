import graphene
from graphene import relay
from graphene import Enum
# from .file_relation import FileRelation
from graphql_relay import from_global_id
from .custom.sms_file_link import SmsFileLink

global db_root

class FileRole(Enum):
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"
    UNDEFINED = "undefined"

class FileLink(graphene.ObjectType):

    class Meta:
        interfaces = (relay.Node, )

    thing = graphene.Field('graphql_api.schema.thing.Thing', required=True)
    file = graphene.Field('graphql_api.schema.file.File', required=True)

    role = graphene.Field(FileRole, required=True)

    thing_id = graphene.String()
    file_id = graphene.String()

class FileThingRelation(graphene.Union):
    class Meta:
        types = (SmsFileLink, FileLink)

class FileThingRelationConnection(relay.Connection):
    class Meta:
        node = FileThingRelation

class Thing(graphene.Interface):
    """A Task in the NSHM saga"""
    class Meta:
        interfaces = (relay.Node, )

    created = graphene.DateTime(description="The time the task was started")

    files = relay.ConnectionField(
         FileThingRelationConnection, description="Files associated with this object."
    )

    def resolve_files(self, info, **args):
        # Transform the instance ship_ids into real instances
        if not self.files: return []
        return [db_root.file_relation.get_one(_id) for _id in self.files]


class ThingConnection(relay.Connection):
    """A Relay connection listing Files"""
    class Meta:
        node = Thing




class CreateFileLink(graphene.Mutation):
    class Arguments:
        thing_id = graphene.ID(required=True)
        file_id = graphene.ID(required=True)
        role = FileRole(required=True)

    ok = graphene.Boolean()
    file_link = graphene.Field(FileLink)

    def mutate(self, info, **kwargs):
        print("CreateFileLink.mutate: ", kwargs)
        ftype, file_id = from_global_id(kwargs.pop('file_id'))
        #file = db_root.file.get_one(file_id)
        ttype, thing_id = from_global_id(kwargs.pop('thing_id'))
        #thing = db_root.thing.get_one(kwargs.pop('strong_motion_station_id'))

        file_link = db_root.file_relation.create('FileLink', thing_id, file_id, **kwargs)
        return CreateFileLink(ok=True, file_link= file_link)

class FileLinkConnection(relay.Connection):
    """A Relay connection listing Files"""
    class Meta:
        node = FileLink