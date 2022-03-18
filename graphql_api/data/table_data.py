"""
Object manager for Table schema objects
"""
import datetime as dt
import logging
from importlib import import_module
from benedict import benedict

from .base_data import BaseDynamoDBData
# from .helpers import get_objectid_from_global
from graphql_relay import from_global_id, to_global_id
# import graphql_api.schema

logger = logging.getLogger(__name__)


class TableData(BaseDynamoDBData):
    """
    TableData provides the data storage for Table objects
    """

    def create(self, clazz_name, **kwargs):
        """
        Args:
            clazz_name (String): the class name of schema object
            **kwargs: the field data

        Returns:
            Table: a new instance of the clazz_name

        Raises:
            ValueError: invalid data exception
        """
        if not  kwargs['created'].tzname(): #must have a timezone set
            raise ValueError("'created' DateTime() field must have a timezone set.")

        return super().create(clazz_name, **kwargs)


    def get_one(self, thing_id):
        """
        Args:
            _id (string): the object id
        Returns:
            File: the Table object
        """
        # jsondata = self.migrate_old_thing_object(self._read_object(thing_id))
        return self.from_json(self._read_object(thing_id))


    def update(self, clazz_name, thing_id, **kwargs):
        """
        Args:
            task_id (TYPE): the object id
            **kwargs: the received schema fields

        Returns:
            TYPE: the Table object
        """
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)

        _type, this_id = from_global_id(thing_id)

        body = benedict(self.get_one(this_id).__dict__.copy())
        body.merge(kwargs)
        body['created'] = body['created'].isoformat()
        body['clazz_name'] = clazz_name
        self.transact_update(this_id, clazz_name, body)
        body.pop('clazz_name')
        # print(body)
        return clazz(**body)


    @staticmethod
    def from_json(jsondata):
        logger.info("from_json: %s" % str(jsondata))

        #datetime comversions
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.datetime.fromisoformat(created)

        clazz_name = jsondata.pop('clazz_name')
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        return clazz(**jsondata)
