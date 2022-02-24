"""
Object manager for ThingRelation (and subclassed) schema objects
"""
import datetime as dt
from graphql_api.dynamodb.models import ToshiThingObject
import logging
from importlib import import_module
from .base_data import BaseData

logger = logging.getLogger(__name__)

class ThingRelationData(BaseData):
    """
    ThingRelationData provides the S3 interface for ThingRelation objects
    """
    def create(self, parent_clazz, child_clazz, parent_id, child_id, **kwargs):
        """
        Args:
            clazz_name (String): the class name of schema object
            parent_id (TYPE): Description
            child_id (TYPE): Description
            **kwargs: the field data

        """
        self._db_manager.thing.add_child_relation(thing_id=parent_id, relation_id=child_id, relation_clazz=child_clazz)
        self._db_manager.thing.add_parent_relation(thing_id=child_id, relation_id=parent_id, relation_clazz=parent_clazz)

    def get_one(self, _id, clazz):
        """
        Args:
            _id (string): the object id
        Returns:
            File: the Thing object
        """
        print('THING RELATION GET ONE', _id, clazz)
        jsondata = self._read_object(_id, clazz)
        logger.info("get_one: %s" % str(jsondata))
        relation =  self.from_json(jsondata)
        return relation

    def build_parent(self, parent_id, clazz_name):
        """
        Args:
            parent_id (string): the parent id
            child_id (string): the child id
        Returns:
            File: the Thing object
        """

        jsondata = {'id': parent_id, 'clazz_name': clazz_name}
        logger.info("build_one: %s" % str(jsondata))
        relation =  self.from_json(jsondata)
        return relation
    
    def build_child(self, child_id, clazz_name):
        """
        Args:
            parent_id (string): the parent id
            child_id (string): the child id
        Returns:
            File: the Thing object
        """

        jsondata = {'id': child_id, 'clazz_name': clazz_name}
        logger.info("build_one: %s" % str(jsondata))
        relation =  self.from_json(jsondata)
        return relation

    def _read_object(self, object_id, object_type):
        key = f'ThingData/{object_id}'
        print ('thing relation reads', key, object_type)
        obj = ToshiThingObject.get(key, 'ThingData')
        print(obj)
        return obj.object_content

    @staticmethod
    def from_json(jsondata):
        
        # created = jsondata.get('created')
        # if created:
        #     jsondata['created'] = dt.datetime.fromisoformat(created)

        # jsondata.pop('id', None)
        clazz_name = jsondata.pop('clazz_name', None)
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        return clazz(**jsondata)