import graphene
from graphene import relay
from graphene import Enum
from graphql_relay import from_global_id

from .file import File
#from .custom.strong_motion_station_file import SmsFile
#from .custom.inversion_solution import InversionSolution
from graphql_api.data_s3 import get_data_manager

class FileRole(Enum):
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"
    UNDEFINED = "undefined"

class FileRelation(graphene.ObjectType):

    # class Meta:
    #     interfaces = (relay.Node, )


    thing = graphene.Field('graphql_api.schema.thing.Thing', required=True)
    file = graphene.Field('graphql_api.schema.schema.FileUnion', required=True)

    role = graphene.Field(FileRole, required=True)

    thing_id = graphene.String()
    file_id = graphene.String()


class FileRelationConnection(relay.Connection):
    class Meta:
        node = FileRelation

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)

class CreateFileRelation(graphene.Mutation):
    class Arguments:
        thing_id = graphene.ID(required=True)
        file_id = graphene.ID(required=True)
        role = FileRole(required=True)

    ok = graphene.Boolean()
    file_relation = graphene.Field(FileRelation)

    def mutate(self, info, **kwargs):
        print("CreateFileRelation.mutate: ", kwargs)
        ftype, file_id = from_global_id(kwargs.pop('file_id'))
        #file = db_root.file.get_one(file_id)
        ttype, thing_id = from_global_id(kwargs.pop('thing_id'))
        #thing = db_root.thing.get_one(kwargs.pop('strong_motion_station_id'))

        file_relation = get_data_manager().file_relation.create('FileRelation', thing_id, file_id, **kwargs)
        return CreateFileRelation(ok=True, file_relation= file_relation)
