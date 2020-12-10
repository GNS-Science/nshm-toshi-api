
import graphene
from graphene import relay
from graphene import Enum
# from graphql_api.schema.file_relation import FileRelation
from graphql_relay import from_global_id, to_global_id

global db_root

class SmsFileType(Enum):
    BH = "bh"
    CPT = "cpt"
    DH = "dh"
    HVSR = "hsvr"
    SW = "sw"

class SmsFileLink(graphene.ObjectType):

    class Meta:
        interfaces = (relay.Node, )

    file_type = SmsFileType(required=True)

    thing = graphene.Field('graphql_api.schema.thing.Thing', required=True)
    file = graphene.Field('graphql_api.schema.file.File', required=True)
    thing_id = graphene.String()
    file_id = graphene.String()


class CreateSmsFileLink(graphene.Mutation):
    class Arguments:
        sms_id = graphene.ID(required=True)
        file_id = graphene.ID(required=True)
        file_type = SmsFileType(required=True)

    ok = graphene.Boolean()
    sms_file_link = graphene.Field(SmsFileLink)

    def mutate(self, info, **kwargs):
        print("CreateSmsFileLink.mutate: ", kwargs)
        ftype, file_id = from_global_id(kwargs.pop('file_id'))
        #file = db_root.file.get_one(file_id)
        ttype, thing_id = from_global_id(kwargs.pop('sms_id'))
        #thing = db_root.thing.get_one(kwargs.pop('strong_motion_station_id'))

        sms_file_link = db_root.file_relation.create('SmsFileLink', thing_id, file_id, **kwargs)
        return CreateSmsFileLink(ok=True, sms_file_link=sms_file_link)

class SmsFileLinkConnection(relay.Connection):
    """A Relay connection listing Files"""
    class Meta:
        node = SmsFileLink