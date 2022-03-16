"""
Object manager for ThingRelation (and subclassed) schema objects
"""
import datetime as dt
from graphql_api.dynamodb.models import ToshiThingObject
from pynamodb.exceptions import TransactWriteError
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
        # TODO: a more consistent approach would check that both succeed
        #try:
        self._db_manager.thing.add_child_relation(thing_id=parent_id, relation_id=child_id, relation_clazz=child_clazz)
        #except TransactWriteError as e:
        #    self._db_manager.thing.add_child_relation(thing_id=parent_id, relation_id=child_id, relation_clazz=child_clazz)

        #try:
        self._db_manager.thing.add_parent_relation(thing_id=child_id, relation_id=parent_id, relation_clazz=parent_clazz)
        #except TransactWriteError as e:
        #    self._db_manager.thing.add_parent_relation(thing_id=child_id, relation_id=parent_id, relation_clazz=parent_clazz)
        return self.build_one(parent_id, child_id)

    def get_one(self, _id):
        """
        Args:
            _id (string): the object id
        Returns:
            File: the Thing object
        """
        print('THING RELATION GET ONE', _id)
        jsondata = self._read_object(_id)
        logger.info("get_one: %s" % str(jsondata))
        relation =  self.from_json(jsondata)
        return relation

    def build_one(self, parent_id, child_id):
        """
        Args:
            parent_id (string): the object id
            child_id(string): the object id
        Returns:
            File: the TaskTaskRelation object
        """
        jsondata = {'parent_id': parent_id, 'child_id': child_id}
        logger.info("build_one: %s" % str(jsondata))
        relation =  self.from_json(jsondata)
        return relation

    @staticmethod
    def from_json(jsondata):
        
        # created = jsondata.get('created')
        # if created:
        #     jsondata['created'] = dt.datetime.fromisoformat(created)

        # jsondata.pop('id', None)
        clazz = getattr(import_module('graphql_api.schema'), "TaskTaskRelation")

        #id is no longer a class attribute, but some old objects may still exist
        jsondata.pop('id', None)
        jsondata.pop('clazz_name', None)
        return clazz(**jsondata)