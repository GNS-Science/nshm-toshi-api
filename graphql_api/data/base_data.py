"""
BaseData is the base class for AWS_S3 data handlers
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
from graphql_relay.node.node import from_global_id
from pynamodb.connection.base import Connection
from pynamodb.exceptions import PutError, VerboseClientError, DoesNotExist
from pynamodb.transactions import TransactWrite
from botocore.exceptions import ClientError
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject

from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION, DB_ENDPOINT, IS_OFFLINE, TESTING, DEPLOYMENT_STAGE, S3_BUCKET_NAME
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
        self._bucket_name = S3_BUCKET_NAME
        self._s3 = boto3.resource('s3')
        self._bucket = self._s3.Bucket(self._bucket_name, client=self._client)
        self._prefix = self.__class__.__name__
        self._connection = Connection()

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
    
    def _read_object(self, object_id):
        """read object contents from the DynamoDB or S3 bucket.

        Args:
            object_id int): unique iD of the obect

        Returns:
            dict: object data deserialised from the json object
        """
        # TODO NEEDS TEST COVERAGE for fail to S3
        t0 = dt.utcnow()
        key = "%s/%s" % (self._prefix, object_id)
        print('key: ', key, 'prefix', self._prefix)
        
        try:
            obj = self._model.get(key, self._prefix)
            db_metrics.put_duration(__name__, '_read_object' , dt.utcnow()-t0)
            return obj.object_content
        except:
            S3_key = "%s/%s/%s" % (self._prefix, object_id, 'object.json')
            obj = self._s3.Object(bucket_name=self._bucket_name,
                                  key=S3_key,
                                  client=self._client)
            file_object = BytesIO()
            obj.download_fileobj(file_object)
            file_object.seek(0)
            db_metrics.put_duration(__name__, '_read_object' , dt.utcnow()-t0)
            return json.load(file_object)

    def get_all_in(self, _id_list):
        pass
        #TODO

if IS_OFFLINE: 
    FIRST_ID = 0 #start new ids at some large number to make sure of no clashes, unless running locally (then breaks smoketests)
else:
    FIRST_ID = 10000

class BaseDynamoDBData(BaseData):
    def __init__(self, client_args, db_manager, model, connection=Connection()):
        super().__init__(client_args, db_manager)
        self._model = model
        self._connection = connection
        if not TESTING and IS_OFFLINE:
            self._connection = Connection(host=DB_ENDPOINT)
            
    def get_next_id(self) -> str:
        """
        Returns:
                int: the next available id
        """
        t0 = dt.utcnow()
        try:
            identity = ToshiIdentity.get(self._prefix)
        except DoesNotExist as e:
            # very first use of the identity
            identity = ToshiIdentity(table_name=self._prefix, object_id=FIRST_ID)
            identity.save()
        db_metrics.put_duration(__name__, 'get_all' , dt.utcnow()-t0)
        return identity.object_id    

    def _write_object(self, object_id, object_type, body):
        """write object contents to the DynamoDB table.

        Args:
            object_id (int): unique iD of the obect
            body (dict): dict to be serialised to JSON
        """
        
        t0 = dt.utcnow()
        key = "%s/%s" % (self._prefix, object_id)
        
        identity = ToshiIdentity.get(self._prefix) #first time round is handled in get_next_id()

        #TODO: make a transacion conditional check (maybe)
        if not identity.object_id == object_id:
            raise RuntimeError(F"object ids are not consistent!) {(identity.object_id, object_id)}")

        toshi_object = self._model(object_id=key, object_type=self._prefix, object_content=body)
       
        with TransactWrite(connection=self._connection) as transaction:
            transaction.update(identity, 
                            actions=[ToshiIdentity.object_id.add(1)])
            transaction.save(toshi_object)
    
        db_metrics.put_duration(__name__, '_write_object' , dt.utcnow()-t0)
        # print('BODY', body)
        es_key = key.replace("/", "_")
        self._db_manager.search_manager.index_document(es_key, body)

    def transact_update(self, object_id, object_type, body):
        t0 = dt.utcnow()
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
                new_object = self._model(object_id=key, object_type=self._prefix, object_content=body)
                new_object.save()
            
        es_key = key.replace("/", "_")
        self._db_manager.search_manager.index_document(es_key, body)
        db_metrics.put_duration(__name__, 'transact_update' , dt.utcnow()-t0)
        print('#####updated:', object_id, self._model.get(key, object_type).object_content)