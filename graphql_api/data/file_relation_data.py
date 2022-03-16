"""
Object manager for FileRelation (and subclassed) schema objects
"""
import logging
from importlib import import_module
from .base_data import BaseData
from pynamodb.exceptions import TransactWriteError
import datetime as dt

logger = logging.getLogger(__name__)

class FileRelationData(BaseData):
    """
    FileRelationData provides the S3 interface for FileRelation objects
    """
    def create(self, clazz_name, thing_id, file_id, role, **kwargs):
        """
        Args:
            clazz_name (String): the class name of schema object
            related_id (TYPE): Description
            file_id (TYPE): Description
            **kwargs: the field data
        """
        # TODO: a more consistent approach would check that both succeed
        # try:
        self._db_manager.file.add_thing_relation(file_id=file_id, thing_id=thing_id, thing_role=role)
        # except TransactWriteError as e:
        #     self._db_manager.file.add_thing_relation(file_id=file_id, thing_id=thing_id, thing_role=role)

        #try:
        self._db_manager.thing.add_file_relation(thing_id=thing_id, file_id=file_id, file_role=role)
        # except TransactWriteError as e:
        #     self._db_manager.thing.add_file_relation(thing_id=thing_id, file_id=file_id, file_role=role)


    def get_one(self, _id):
        """
        Args:
            _id (string): the object id
        Returns:
            the FileRelation object
        """
        jsondata = self._read_object(_id)
        logger.info("get_one: %s" % str(jsondata))
        relation =  self.from_json(jsondata)
        return relation

    def build_one(self, file_id, thing_id, thing_role):
        """
        Args:
            file_id (string): the object id
        Returns:
            File: the Thing object
        """

        jsondata = {'file_id': file_id, 'thing_id': thing_id, 'role': thing_role}
        logger.info("get_one: %s" % str(jsondata))
        relation =  self.from_json(jsondata)
        return relation


    @staticmethod
    def from_json(jsondata):
         #datetime comversions
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.datetime.fromisoformat(created)

        clazz = getattr(import_module('graphql_api.schema'), "FileRelation")
        
        #id is no longer a class attribute, but some old objects may still exist
        jsondata.pop('id', None)
        jsondata.pop('clazz_name', None)

        return clazz(**jsondata)