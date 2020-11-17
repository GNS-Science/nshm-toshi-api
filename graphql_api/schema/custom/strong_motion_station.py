"""
This module contains the schema definition for an NSHM Strong Motion Station.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

"""
import graphene
import datetime as dt
import logging

from graphene import relay
from graphene import Enum

global db_root

logger = logging.getLogger(__name__)

class StrongMotionStation(graphene.ObjectType):
    """A Strong Motion Station """
    class Meta:
        interfaces = (relay.Node,)
    created = graphene.DateTime(description="The time the SMS was created", )
    updated = graphene.DateTime(description="The time the SMS was updated", )


class CreateStrongMotionStation(relay.ClientIDMutation):
    class Input:
        created = graphene.DateTime(description="The time the SMS was created", )
        # updated = graphene.DateTime(description="The time the task was updated")

    strong_motion_station = graphene.Field(StrongMotionStation)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        strong_motion_station = db_root.thing.create('StrongMotionStation', **kwargs)
        return CreateStrongMotionStation(strong_motion_station=strong_motion_station)
