"""
Object manager for Thing schema objects
"""
import datetime as dt
import logging
from importlib import import_module
from benedict import benedict

from .base_s3_data import BaseS3Data
# from .helpers import get_objectid_from_global
from graphql_relay import from_global_id, to_global_id
# import graphql_api.schema

logger = logging.getLogger(__name__)


class ThingData(BaseS3Data):
    """
    ThingData provides the data storage for Thing objects
    """
    def create(self, clazz_name, **kwargs):
        """
        Args:
            clazz_name (String): the class name of schema object
            **kwargs: the field data

        Returns:
            Thing: a new instance of the clazz_name

        Raises:
            ValueError: invalid data exception
        """
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        next_id  = str(self.get_next_id())
        if not  kwargs['created'].tzname(): #must have a timezone set
            raise ValueError("'created' DateTime() field must have a timezone set.")

        new = clazz(next_id, **kwargs)
        body = new.__dict__.copy()
        body['clazz_name'] = clazz_name
        body['created'] = body['created'].isoformat()
        self._write_object(next_id, body)
        return new


    def get_one(self, thing_id):
        """
        Args:
            _id (string): the object id
        Returns:
            File: the Thing object
        """
        # TODO: get_one should validate the type of the object in case ID passed in by client is invalid
        jsondata = self._read_object(thing_id)
        return self.from_json(jsondata)


    def update(self, clazz_name, thing_id, **kwargs):
        """
        Args:
            task_id (TYPE): the object id
            **kwargs: the received schema fields

        Returns:
            TYPE: the Thing object
        """
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)

        _type, this_id = from_global_id(thing_id)

        body = benedict(self.get_one(this_id).__dict__.copy())
        body.merge(kwargs)
        body['created'] = body['created'].isoformat()
        body['clazz_name'] = clazz_name
        self._write_object(this_id, body)
        body.pop('clazz_name')
        # print(body)
        return clazz(**body)


    def add_file_relation(self, thing_id, relation_id):
        obj = self._read_object(thing_id)
        logger.info("add_file_relation: thing_id: %s, relation_id %s, " % (thing_id, relation_id))
        print("####add_file_relation", thing_id, obj)
        try:
            obj['files'].append(relation_id)
        except (KeyError, AttributeError):
            obj['files'] = [relation_id]
        self._write_object(thing_id, obj)
        return self.from_json(obj)


    def add_child_relation(self, thing_id, relation_id):
        obj = self._read_object(thing_id)
        logger.info("add_child_relation: thing_id: %s, relation_id %s, " % (thing_id, relation_id))
        # print("####add_file_relation", thing_id, obj)
        try:
            obj['children'].append(relation_id)
        except (KeyError, AttributeError):
            obj['children'] = [relation_id]
        self._write_object(thing_id, obj)
        return self.from_json(obj)

    def add_parent_relation(self, thing_id, relation_id):
        obj = self._read_object(thing_id)
        logger.info("add_parent_relation: thing_id: %s, relation_id %s, " % (thing_id, relation_id))
        try:
            obj['parents'].append(relation_id)
        except (KeyError, AttributeError):
            obj['parents'] = [relation_id]
        self._write_object(thing_id, obj)
        return self.from_json(obj)


    @staticmethod
    def from_json(jsondata):
        logger.info("from_json: %s" % str(jsondata))

        #datetime comversions
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.datetime.fromisoformat(created)

        clazz_name = jsondata.pop('clazz_name')
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        # print('updated json', jsondata)
        return clazz(**jsondata)
