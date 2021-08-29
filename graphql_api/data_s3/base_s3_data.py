"""
BaseS3Data is the base class for AWS_S3 data handlers
"""
import os
import json
from importlib import import_module
from io import BytesIO
import boto3
import random
import logging

logger = logging.getLogger(__name__)

_ALPHABET = list("23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

def append_uniq(size):
    uniq = ''.join(random.choice(_ALPHABET) for _ in range(5))
    return str(size)+uniq

class BaseS3Data():
    """
    BaseS3Data is the base class for AWS_S3 data handlers
    """

    def __init__(self, client_args, db_manager):
        """Args:
            client_args (dict): optional)arguments for the boto3 client
            db_manager (DataManager): reference to the singleton DataManager object
        """
        args = client_args or {}
        self._db_manager = db_manager
        self._client = boto3.client('s3', **args)
        self._bucket_name = os.environ.get('S3_BUCKET_NAME', "nshm-tosh-api-test")
        self._s3 = boto3.resource('s3')
        self._bucket = self._s3.Bucket(self._bucket_name, client=self._client)
        self._prefix = self.__class__.__name__

    def get_next_id(self):
        """
        Returns:
            int: the next available id
        """
        size = sum(1 for _ in self._bucket.objects.filter(Prefix='%s/' % self._prefix))
        return append_uniq(size)


    def get_one_raw(self, _id):
        """
        Args:
            file_id (string): the object id

        Returns:
            File: the File object json
        """
        logger.info("BaseS3Data.get_one_raw: %s" % _id)
        return self._read_object(_id)


    def get_one(self, _id):
        """Summary

        Args:
            _id (int): id for an object

        Raises:
            NotImplementedError: must override
        """
        raise NotImplementedError("method needs to be defined by sub-class")

    def get_all(self, clazz_name=None):
        """
        Returns:
            list: a list containing all the objects materialised from the S3 bucket
        """
        if clazz_name:
            clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        else:
            clazz=None

        results = []
        for obj_summary in self._bucket.objects.filter(Prefix='%s/' % self._prefix):
            prefix, result_id, _ = obj_summary.key.split('/')
            assert prefix == self._prefix
            object = self.get_one(result_id)
            if (clazz==None or isinstance(object, clazz)):
                results.append(object)
        return results

    def _write_object(self, object_id, body):
        """write object contents to the S3 bucket.

        Args:
            object_id (int): unique iD of the obect
            body (dict): dict to be serialised to JSON
        """
        key = "%s/%s/%s" % (self._prefix, object_id, "object.json")
        #TODO: add some error handling here
        response = self._bucket.put_object(Key=key, Body=json.dumps(body))
        es_key = key.replace("/", "_")
        self._db_manager.search_manager.index_document(es_key, body)


    def _read_object(self, object_id):
        """read object contents from the S3 bucket.

        Args:
            object_id int): unique iD of the obect

        Returns:
            dict: object data deserialised from the json object
        """
        key = "%s/%s/%s" % (self._prefix, object_id, "object.json")
        obj = self._s3.Object(bucket_name=self._bucket_name,
                        key=key,
                        client=self._client)
        file_object = BytesIO()
        obj.download_fileobj(file_object)
        file_object.seek(0)
        return json.load(file_object)
