"""
Object manager for ThingRelation (and subclassed) schema objects
"""
import logging
import backoff
import pynamodb.exceptions
from pynamodb.transactions import TransactWrite

from importlib import import_module
from .base_data import BaseDynamoDBData

logger = logging.getLogger(__name__)

class ThingRelationData(BaseDynamoDBData):
    """
    ThingRelationData provides the S3 interface for ThingRelation objects
    """

    @backoff.on_exception(backoff.expo,
        pynamodb.exceptions.TransactWriteError,
        max_time=60)
    def create(self, parent_clazz, child_clazz, parent_id, child_id, **kwargs):
        """
        Args:
            clazz_name (String): the class name of schema object
            parent_id (TYPE): Description
            child_id (TYPE): Description
            **kwargs: the field data
        """
        parent = self._db_manager.thing.get_object(parent_id)
        child = self._db_manager.thing.get_object(child_id)

        parent_content = parent.object_content
        if not parent_content.get('children'):
            parent_content['children'] = []
        parent_content['children'].append({'child_id': child_id, 'child_clazz': child_clazz})

        child_content = child.object_content
        if not child_content.get('parents'):
            child_content['parents'] = []
        child_content['parents'].append({'parent_id': parent_id, 'parent_clazz': parent_clazz})

        with TransactWrite(connection=self._connection) as transaction:
            transaction.update(parent,
                actions=[self._db_manager.thing.model.object_content.set(parent_content)])
            transaction.update(child,
                actions=[self._db_manager.thing.model.object_content.set(child_content)])

        logger.info(f'create add_child_relation transaction OK: added: {child_id} to children {len(parent_content["children"])} of parent {parent_id}')
        logger.info(f'create parent_relation : added: {parent_id} to parents {len(child_content["parents"])} of child {child_id}')

        # self._db_manager.search_manager.index_document(parent.object_id, parent_content)
        # self._db_manager.search_manager.index_document(child.object_id, child_content)

        es_parent_key = f"{self._db_manager.thing._prefix}_{parent_id}"
        es_child_key = f"{self._db_manager.thing._prefix}_{child_id}"

        logger.info(f"update ES for key {es_parent_key}")
        logger.info(f"update ES for key {es_child_key}")

        self._db_manager.search_manager.index_document(es_parent_key, parent_content)
        self._db_manager.search_manager.index_document(es_child_key, child_content)


        return self.build_one(parent_id, child_id)

    def get_one(self, _id):
        """
        Args:
            _id (string): the object id
        Returns:
            File: the Thing object
        """
        logger.info(f'LEGACY RELATION GET ONE{_id}')
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
        
        clazz = getattr(import_module('graphql_api.schema'), "TaskTaskRelation")

        #id is no longer a class attribute, but some old objects may still exist
        jsondata.pop('id', None)
        jsondata.pop('clazz_name', None)
        return clazz(**jsondata)