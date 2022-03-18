"""
Object manager for FileRelation (and subclassed) schema objects
"""
import logging
import datetime as dt
from importlib import import_module
import backoff
import pynamodb.exceptions
from pynamodb.transactions import TransactWrite
from .base_data import BaseDynamoDBData

logger = logging.getLogger(__name__)

class FileRelationData(BaseDynamoDBData):
    """
    FileRelationData provides the data interface for FileRelation objects
    """

    @backoff.on_exception(backoff.expo,
        pynamodb.exceptions.TransactWriteError,
        max_time=60)
    def create(self, clazz_name, thing_id, file_id, role):

        thing = self._db_manager.thing.get_object(thing_id)
        file = self._db_manager.file.get_object(file_id)

        thing_content = thing.object_content
        if not thing_content.get('files'):
            thing_content['files'] = []
        thing_content['files'].append({'file_id': file_id, 'file_role': role})

        file_content = file.object_content
        if not file_content.get('relations'):
            file_content['relations'] = []
        file_content['relations'].append({'id': thing_id, 'role': role})

        with TransactWrite(connection=self._connection) as transaction:
            transaction.update(thing,
                actions=[self._db_manager.thing.model.object_content.set(thing_content)])
            transaction.update(file,
                actions=[self._db_manager.file.model.object_content.set(file_content)])

        logger.info(f'FileRelationData.create() linking file {file_id} to and thing {thing_id} in role {role}')

        logger.debug(f'FileRelationData.create() thing {thing_id} has {len(thing_content["files"])} file')
        logger.debug(f'FileRelationData.create() file {file_id} has {len(file_content["relations"])} related things')

        self._db_manager.search_manager.index_document(thing.object_id, thing_content)
        self._db_manager.search_manager.index_document(file.object_id, file_content)

        return self.build_one(file_id, thing_id, role)


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