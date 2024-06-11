"""
Object manager for FileRelation (and subclassed) schema objects
"""

import datetime as dt
import json
import logging
from importlib import import_module
from typing import Dict, List, Union

import backoff
import pynamodb.exceptions
from nzshm_common.util import compress_string, decompress_string
from pynamodb.transactions import TransactWrite

from graphql_api.dynamodb.models import ToshiFileObject

from .base_data import BaseDynamoDBData

logger = logging.getLogger(__name__)
UNCOMPRESSED_LIMIT = 100


def ensure_decompressed(maybe_compressed_list: Union[str, List]) -> List[Dict]:
    if isinstance(maybe_compressed_list, str):
        return json.loads(decompress_string(maybe_compressed_list))
    return maybe_compressed_list


class FileRelationData(BaseDynamoDBData):
    """
    FileRelationData provides the data interface for FileRelation objects
    """

    @backoff.on_exception(backoff.expo, pynamodb.exceptions.TransactWriteError, max_time=25)
    def create(self, clazz_name, thing_id, file_id, role):
        logger.debug(f'FileRelationData.create() linking file {file_id} to and thing {thing_id} in role {role}')

        thing = self._db_manager.thing.get_object(thing_id)
        thing_content = thing.object_content
        if not thing_content.get('files'):
            thing_content['files'] = []
        thing_content['files'].append({'file_id': file_id, 'file_role': role})

        try:
            file = self._db_manager.file.get_object(file_id)
        except pynamodb.exceptions.DoesNotExist:
            body = self._db_manager.file._from_s3(file_id)
            logger.info(
                f"Migrate object to Pynamodb: key={file_id};  type={self._db_manager.file._prefix};"
                f" object_type={body['clazz_name']}"
            )
            file = ToshiFileObject(object_id=file_id, object_type=body['clazz_name'], object_content=body)
            logger.debug(f'ToshiFileObject version {file.version}')

        file_content = file.object_content
        if not file_content.get('relations'):
            file_content['relations'] = []
        else:
            file_content['relations'] = ensure_decompressed(file_content['relations'])

        file_content['relations'].append({'id': thing_id, 'role': role})

        # compress file relations if the list grows large...
        if len(file_content['relations']) > UNCOMPRESSED_LIMIT:
            file_content['relations'] = compress_string(json.dumps(file_content['relations']))

        try:
            with TransactWrite(connection=self._connection) as transaction:
                transaction.update(thing, actions=[self._db_manager.thing.model.object_content.set(thing_content)])
                # update will create a new object if it doesn't exist
                transaction.update(file, actions=[self._db_manager.file.model.object_content.set(file_content)])

        except pynamodb.exceptions.TransactWriteError as err:
            thing_len = len(json.dumps(thing_content))
            file_len = len(json.dumps(file_content))
            logger.debug("length of thing_content: %s" % thing_len)
            logger.debug("length of file_content: %s" % file_len)
            if file_len >= 400e3:
                raise RuntimeError(
                    "File object of size (%s) maybe too big, transaction raised exception: %s" % (file_len, err.cause)
                )

            if thing_len >= 400e3:
                raise RuntimeError(
                    "Thing object of size (%s) maybe too big, transaction raised exception: %s" % (thing_len, err.cause)
                )

        logger.debug(f'FileRelationData.create() thing {thing_id} has {len(thing_content["files"])} file')
        logger.debug(f'FileRelationData.create() file {file_id} has {len(file_content["relations"])} related things')

        es_thing_key = f"{self._db_manager.thing._prefix}_{thing_id}"
        es_file_key = f"{self._db_manager.file._prefix}_{file_id}"

        logger.debug(f"update ES for key {es_thing_key}")
        logger.debug(f"update ES for key {es_file_key}")

        self._db_manager.search_manager.index_document(es_thing_key, thing_content)
        self._db_manager.search_manager.index_document(es_file_key, file_content)
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
        relation = self.from_json(jsondata)
        return relation

    def build_one(self, file_id, thing_id, thing_role):
        """
        Args:
            file_id (string): the object id
        Returns:
            File: the Thing object
        """
        jsondata = {'file_id': file_id, 'thing_id': thing_id, 'role': thing_role}
        logger.debug("get_one: %s" % str(jsondata))
        relation = self.from_json(jsondata)
        return relation

    @staticmethod
    def from_json(jsondata):
        # datetime comversions
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.datetime.fromisoformat(created)

        clazz = getattr(import_module('graphql_api.schema'), "FileRelation")
        # id is no longer a class attribute, but some old objects may still exist
        jsondata.pop('id', None)
        jsondata.pop('clazz_name', None)
        return clazz(**jsondata)
