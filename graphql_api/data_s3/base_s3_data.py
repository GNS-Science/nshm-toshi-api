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
from graphene.relay import connection
from pynamodb.connection.base import Connection
from pynamodb.exceptions import PutError, VerboseClientError, DoesNotExist
from pynamodb.transactions import TransactWrite
from botocore.exceptions import ClientError
from graphql_api.dynamodb.models import ToshiIdentity

from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION, DB_ENDPOINT, IS_OFFLINE
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
        self._connection = Connection()

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
        if IS_OFFLINE:
            self._connection = Connection(host=DB_ENDPOINT)
        else:
            self._connection = Connection()
        print(self._connection.host)
            
    def get_next_id(self) -> str:
        """
        Returns:
                int: the next available id
        """

        try:
            identity = ToshiIdentity.get(self._prefix)
        except DoesNotExist as e:
            identity = ToshiIdentity(table_name=self._prefix, object_id=0)
            identity.save()
        
        return append_uniq(identity.object_id)    

    def _write_object(self, object_id, object_type, body):
        """write object contents to the DynamoDB table.

        Args:
            object_id (int): unique iD of the obect
            body (dict): dict to be serialised to JSON
        """
        
        t0 = dt.utcnow()
        key = "%s/%s" % (self._prefix, object_id)
        
        try:
            identity = ToshiIdentity.get(self._prefix)
        except DoesNotExist as e:
            identity = ToshiIdentity(table_name=self._prefix, object_id=0)
            identity.save()
            
        toshi_object = self._model(object_id=key, object_type=object_type, object_content=body)
       
        with TransactWrite(connection=self._connection) as transaction:
            transaction.update(identity, 
                            actions=[ToshiIdentity.object_id.add(1)])
            transaction.save(toshi_object)
    
        db_metrics.put_duration(__name__, '_write_object' , dt.utcnow()-t0)
        es_key = key.replace("/", "_")
        self._db_manager.search_manager.index_document(es_key, body)

    def _read_object(self, object_id):
        """read object contents from the DynamoDB or S3 bucket.

        Args:
            object_id int): unique iD of the obect

        Returns:
            dict: object data deserialised from the json object
        """
        # TODO NEEDS TEST COVERAGE for fail to S3
        key = "%s/%s" % (self._prefix, object_id)
        print('key: ', key, 'prefix', self._prefix)
        try:
            obj = self._model.get(key, self._prefix)
            return obj.object_content
        except:
            S3_key = "%s/%s/%s" % (self._prefix, object_id, 'object.json')
            obj = self._s3.Object(bucket_name=self._bucket_name,
                                  key=S3_key,
                                  client=self._client)
            file_object = BytesIO()
            obj.download_fileobj(file_object)
            file_object.seek(0)
            return json.load(file_object)

    def transact_update(self, object_id, object_type, body):
        logger.info("%s.update: %s : %s" % (object_type, object_id, str(body)))
        key = "%s/%s" % (self._prefix, object_id)
        try:
            model = self._model.get(key, object_type)
            with TransactWrite(connection=self._connection) as transaction:
                transaction.update(
                    model,
                    actions=[self._model.object_content.set(body)]
                )
        except DoesNotExist as e:
                logger.info(f'Saving new object: {object_id}')
                new_object = self._model(object_id=key, object_type=object_type, object_content=body)
                new_object.save()
            
        es_key = key.replace("/", "_")
        self._db_manager.search_manager.index_document(es_key, body)
        print('#####updated:', object_id, self._model.get(key, object_type).object_content)