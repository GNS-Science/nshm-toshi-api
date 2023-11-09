#! strong_motion_station_file.py


import graphene
from graphene import Enum, relay

from graphql_api.data import get_data_manager
from graphql_api.schema.custom.scalars import BigInt
from graphql_api.schema.file import FileInterface


class SmsFileType(Enum):
    BH = "bh"
    CPT = "cpt"
    DH = "dh"
    HVSR = "hsvr"
    SW = "sw"


class SmsFile(graphene.ObjectType):
    class Meta:
        """standard graphene meta class"""

        interfaces = (relay.Node, FileInterface)

    file_type = SmsFileType(required=True)


class CreateSmsFile(graphene.Mutation):
    class Arguments:
        file_name = graphene.String()
        md5_digest = graphene.String("The base64-encoded md5 digest of the file")
        file_size = BigInt()
        file_type = SmsFileType(required=True)

    ok = graphene.Boolean()
    file_result = graphene.Field(SmsFile)

    def mutate(self, info, **kwargs):
        # print("CreateFile.mutate: ", file_in, kwargs)
        file_result = get_data_manager().file.create('SmsFile', **kwargs)
        return CreateSmsFile(ok=True, file_result=file_result)
