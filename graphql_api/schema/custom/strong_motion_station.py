"""
This module contains the schema definition for an NSHM Strong Motion Station.

Comments and descriptions defined here will be available to end-users of the API via the graphql schema, which is generated
automatically by Graphene.

"""

import datetime as dt
import logging

import graphene
from graphene import Enum, relay

from graphql_api.data import get_data_manager
from graphql_api.schema.thing import Thing

logger = logging.getLogger(__name__)


class SmsSiteClass(Enum):
    """
    NZS1170.5 Site Class, one of A,B,C,D,E
    """

    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'


class SmsSiteClassBasis(Enum):
    """
    NZS1170.5 Site Class Basis, one of Vs,SPT,su
    """

    Vs = 'Vs'
    SPT = 'SPT'
    su = 'su'


class StrongMotionStationFields:
    """All the Strong Motion Station fields"""

    created = graphene.DateTime(
        description="When the SMS record was created",
    )
    updated = graphene.DateTime(
        description="When SMS record was updated",
    )

    site_code = graphene.String(description='A unique, four character SMS identifier')
    site_class = SmsSiteClass(description="The NZS1170.5 Site Class")
    site_class_basis = SmsSiteClassBasis(description="The data source used for site classification")

    Vs30_mean = graphene.List(graphene.Float, description="Array of Vs30 mean measurements")
    Vs30_std_dev = graphene.List(graphene.Float, description="Array of Vs30 mean measurements")

    bedrock_encountered = graphene.Boolean(
        description="Indicate whether subsurface investigations have encountered bedrock"
    )
    liquefiable = graphene.Boolean(description="Indicate presence of soils that can liquify")
    soft_clay_or_peat = graphene.Boolean(description="Indicate presence of soft clay or peat soils")


class StrongMotionStation(StrongMotionStationFields, graphene.ObjectType):
    """A Strong Motion Station"""

    class Meta:
        interfaces = (relay.Node, Thing)

    @classmethod
    def get_node(cls, info, id):
        return get_data_manager().thing.get_one(id)


class StrongMotionStationConnection(relay.Connection):
    """A list of StrongMotionStation items"""

    class Meta:
        node = StrongMotionStation


class CreateStrongMotionStation(relay.ClientIDMutation):
    class Input:
        created = graphene.DateTime(
            description="When the SMS record was created",
        )
        updated = graphene.DateTime(
            description="When SMS record was updated",
        )

        site_code = graphene.String(description='A unique, four character SMS identifier')
        site_class = SmsSiteClass(description="The NZS1170.5 Site Class")
        site_class_basis = SmsSiteClassBasis(description="The data source used for site classification")

        Vs30_mean = graphene.List(graphene.Float, description="Array of Vs30 mean measurements")
        Vs30_std_dev = graphene.List(graphene.Float, description="Array of Vs30 mean measurements")

        bedrock_encountered = graphene.Boolean(
            description="Indicate whether subsurface investigations have encountered bedrock"
        )
        liquefiable = graphene.Boolean(description="Indicate presence of soils that can liquify")
        soft_clay_or_peat = graphene.Boolean(description="Indicate presence of soft clay or peat soils")

    strong_motion_station = graphene.Field(StrongMotionStation)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        print("mutate_and_get_payload: ", kwargs)
        strong_motion_station = get_data_manager().thing.create('StrongMotionStation', **kwargs)
        return CreateStrongMotionStation(strong_motion_station=strong_motion_station)
