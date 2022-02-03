"""
BaseS3Data is the base class for AWS_S3 data handlers
"""
import os
import json
from importlib import import_module
from datetime import datetime as dt
from io import BytesIO
import boto3
import random
import logging
from graphql_api.dynamodb.models import ToshiIdentity

from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)

logger = logging.getLogger(__name__)

_ALPHABET = list("23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


def append_uniq(size):
    uniq = ''.join(random.choice(_ALPHABET) for _ in range(5))
    return str(size)+uniq


class BaseData():
    """
    BaseData is the base class for data handlers
    """

    def __init__(self, client_args, db_manager):
        """Args:
            client_args (dict): optional)arguments for the boto3 client
            db_manager (DataManager): reference to the singleton DataManager object
        """
        args = client_args or {}
        self._db_manager = db_manager
        self._client = boto3.client('s3', **args)
        self._bucket_name = os.environ.get(
            'S3_BUCKET_NAME', "nshm-tosh-api-test")
        self._s3 = boto3.resource('s3')
        self._bucket = self._s3.Bucket(self._bucket_name, client=self._client)
        self._prefix = self.__class__.__name__

    def get_next_id(self):
        """
        Returns:
            int: the next available id
        """
        t0 = dt.utcnow()
        size = sum(1 for _ in self._bucket.objects.filter(Prefix='%s/' % self._prefix))
        db_metrics.put_duration(__name__, 'get_next_id' , dt.utcnow()-t0)
        return append_uniq(size)


    def get_one_raw(self, _id):
        """
        Args:
            file_id (string): the object id

        Returns:
            File: the File object json
        """
        obj = self._read_object(_id)
        return obj

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
        t0 = dt.utcnow()
        if clazz_name:
            clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        else:
            clazz = None

        results = []
        for obj_summary in self._bucket.objects.filter(Prefix='%s/' % self._prefix):
            prefix, result_id, _ = obj_summary.key.split('/')
            assert prefix == self._prefix
            object = self.get_one(result_id)
            if (clazz == None or isinstance(object, clazz)):
                results.append(object)
        db_metrics.put_duration(__name__, 'get_all' , dt.utcnow()-t0)
        return results
    
    def get_all_in(self, _id_list):
        pass
    #TODO

class BaseS3Data(BaseData):
    def get_next_id(self):
        """
        Returns:
            int: the next available id
        """
        size = sum(1 for _ in self._bucket.objects.filter(
            Prefix='%s/' % self._prefix))
        return append_uniq(size)
    
    def _write_object(self, object_id, body):
        """write object contents to the S3 bucket.

        Args:
            object_id (int): unique iD of the obect
            body (dict): dict to be serialised to JSON
        """
        key = "%s/%s/%s" % (self._prefix, object_id, "object.json")
        # TODO: add some error handling here
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

class BaseDynamoDBData(BaseData):
    def __init__(self, client_args, db_manager, model):
        super().__init__(client_args, db_manager)
        self._model = model
    
    def get_next_id(self) -> int:
        """
        Returns:
                int: the next available id
        """
        """
        1: Read objectID for the table type
        2: Increment the object ID to +1
        3: create new object with new ID
        4: save object to DB
        note: this should complete the transaction and should fail if there was a clash on the object ID,
              the result of this transaction should be both the Identity.object_ID and File.object_id should be equal and both succeed
        """
        
        size = sum(1 for _ in self._model.scan(
            self._model.object_id.startswith(self._prefix)))
        return append_uniq(size)
    
    def _write_object(self, object_id, body):
        """write object contents to the DynamoDB table.

        Args:
            object_id (int): unique iD of the obect
            body (dict): dict to be serialised to JSON
        """
        t0 = dt.utcnow()
        db_metrics.put_duration(__name__, '_write_object' , dt.utcnow()-t0)
        key = "%s/%s/%s" % (self._prefix, object_id, "object.json")
        # TODO: add some error handling here
        response = self._model(object_id=key,
                                object_type=self._prefix,
                                object_content=body)
        response.save()
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
        try:
            obj = self._model.get(key, self._prefix)
            return obj.object_content
        except:
            obj = self._s3.Object(bucket_name=self._bucket_name,
                        key=key,
                        client=self._client)
            file_object = BytesIO()
            obj.download_fileobj(file_object)
            file_object.seek(0)
            return json.load(file_object)