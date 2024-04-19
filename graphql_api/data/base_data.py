"""
BaseData is the base class for AWS_S3 data handlers
"""
import json
import logging
import os
import random
import traceback
from datetime import datetime as dt
from importlib import import_module
from io import BytesIO

import backoff
import boto3
import pynamodb.exceptions
import requests.exceptions
from botocore.exceptions import ClientError
from graphene.relay import connection
from graphql_relay.node.node import from_global_id
from pynamodb.connection.base import Connection
from pynamodb.exceptions import DoesNotExist, PutError, TransactWriteError, VerboseClientError
from pynamodb.transactions import TransactWrite

import graphql_api.dynamodb
from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import (
    CW_METRICS_RESOLUTION,
    DB_ENDPOINT,
    DEPLOYMENT_STAGE,
    FIRST_DYNAMO_ID,
    IS_OFFLINE,
    REGION,
    S3_BUCKET_NAME,
    STACK_NAME,
    TESTING,
)
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

logger = logging.getLogger(__name__)

_ALPHABET = list("23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


def append_uniq(size):
    uniq = ''.join(random.choice(_ALPHABET) for _ in range(5))
    return str(size) + uniq


class BaseData:
    """
    BaseData is the base class for data handlers
    """

    def __init__(self, client_args, db_manager):
        """Args:
        client_args (dict): optional)arguments for the boto3 client
        db_manager (DataManager): reference to the singleton DataManager object
        """
        self._aws_client_args = client_args or {}
        self._prefix = self.__class__.__name__
        self._db_manager = db_manager
        self._s3_conn = None
        self._s3_client = None
        self._s3_bucket = None
        # self._connection = None
        self._bucket_name = S3_BUCKET_NAME

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
            if clazz == None or isinstance(object, clazz):
                results.append(object)
        db_metrics.put_duration(__name__, 'get_all', dt.utcnow() - t0)
        return results

    @property
    def object_type(self):
        return self._prefix

    @property
    def s3_client(self):
        if not self._s3_client:
            self._s3_client = boto3.client('s3', **self._aws_client_args)
        return self._s3_client

    @property
    def s3_connection(self):
        if not self._s3_conn:
            self._s3_conn = boto3.resource('s3')
            # self._connection = Connection(region=REGION)
        return self._s3_conn

    @property
    def s3_bucket(self):
        if not self._s3_bucket:
            self._s3_bucket = self.s3_connection.Bucket(self._bucket_name, client=self.s3_client)
        return self._s3_bucket

    def _from_s3(self, object_id):
        S3_key = "%s/%s/%s" % (self._prefix, object_id, 'object.json')
        logger.info(f"get object from bucket {self._bucket_name}, key={S3_key})")

        s3obj = self.s3_connection.Object(self._bucket_name, S3_key, client=self.s3_client)
        file_object = BytesIO()
        s3obj.download_fileobj(file_object)
        file_object.seek(0)
        return json.load(file_object)

    def get_all_in(self, _id_list):
        pass
        # TODO


def backoff_hdlr(details):
    logger.debug(
        "Backoff {wait:0.1f} seconds after {tries} tries "
        "calling function {target} with args {args} and kwargs "
        "{kwargs}".format(**details)
    )


class BaseDynamoDBData(BaseData):
    def __init__(self, client_args, db_manager, model, connection=Connection(region=REGION)):
        super().__init__(client_args, db_manager)
        self._model = model
        self._connection = connection
        if not TESTING and IS_OFFLINE:
            self._connection = Connection(host=DB_ENDPOINT)

    @property
    def model(self):
        return self._model

    def get_object(self, object_id):
        """get a pynamodb model instance from  DynamoDB.

        Args:
            object_id int: unique ID of the obect
        Returns:
            pynamodb model object
        """
        t0 = dt.utcnow()
        logger.debug('get dynamo key: %s for model %s' % (object_id, self._model))
        obj = self._model.get(str(object_id))
        db_metrics.put_duration(__name__, 'get_object', dt.utcnow() - t0)
        return obj

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
            logger.debug(f'get_next_id setting initial ID; table_name={self._prefix}, object_id={FIRST_DYNAMO_ID}')
            identity = ToshiIdentity(table_name=self._prefix, object_id=FIRST_DYNAMO_ID)
            identity.save()
        db_metrics.put_duration(__name__, 'get_next_id', dt.utcnow() - t0)
        return identity.object_id

    def _read_object(self, object_id):
        """read object contents from the DynamoDB or S3 bucket.

        Args:
            object_id int): unique iD of the obect

        Returns:
            dict: object data deserialised from the json object
        """
        t0 = dt.utcnow()
        key = "%s/%s" % (self._prefix, object_id)
        logger.debug(f'_read_object; key: {key}, prefix {self._prefix}')

        try:
            obj = self.get_object(object_id)
            db_metrics.put_duration(__name__, '_read_object', dt.utcnow() - t0)
            return obj.object_content
        except:
            obj = self._from_s3(object_id)
            db_metrics.put_duration(__name__, '_read_object', dt.utcnow() - t0)
            return obj

    @backoff.on_exception(backoff.expo, pynamodb.exceptions.TransactWriteError, max_time=60, on_backoff=backoff_hdlr)
    def _write_object(self, object_id, object_type, body):
        """write object contents to the DynamoDB table.

        Args:
            object_id (int): unique iD of the obect
            body (dict): dict to be serialised to JSON
        """

        t0 = dt.utcnow()
        identity = ToshiIdentity.get(self._prefix)  # first time round is handled in get_next_id()

        # TODO: make a transacion conditional check (maybe)
        if not identity.object_id == object_id:
            raise graphql_api.dynamodb.DynamoWriteConsistencyError(
                F"object ids are not consistent!) {(identity.object_id, object_id)}"
            )

        toshi_object = self._model(object_id=str(object_id), object_type=body['clazz_name'], object_content=body)

        with TransactWrite(connection=self._connection) as transaction:
            transaction.update(identity, actions=[ToshiIdentity.object_id.add(1)])
            transaction.save(toshi_object)

        logger.debug(f"toshi_object: object_id {object_id} object_type: {body['clazz_name']}")

        db_metrics.put_duration(__name__, '_write_object', dt.utcnow() - t0)
        es_key = f"{self._prefix}_{object_id}"
        self._db_manager.search_manager.index_document(es_key, body)

    @backoff.on_exception(backoff.expo, pynamodb.exceptions.TransactWriteError, max_time=60, on_backoff=backoff_hdlr)
    def transact_update(self, object_id, object_type, body):
        t0 = dt.utcnow()
        logger.info("%s.update: %s : %s" % (object_type, object_id, str(body)))

        model = self._model.get(object_id)
        assert model.object_type == body.get('clazz_name')
        with TransactWrite(connection=self._connection) as transaction:
            transaction.update(model, actions=[self._model.object_content.set(body)])

        es_key = f"{self._prefix}_{object_id}"
        self._db_manager.search_manager.index_document(es_key, body)
        db_metrics.put_duration(__name__, 'transact_update', dt.utcnow() - t0)

    @backoff.on_exception(
        backoff.expo, graphql_api.dynamodb.DynamoWriteConsistencyError, max_time=60, on_backoff=backoff_hdlr
    )
    def create(self, clazz_name, **kwargs):
        """
        Args:
            clazz_name (String): the class name of schema object
            **kwargs: the field data

        Returns:
            Table: a new instance of the clazz_name

        Raises:
            ValueError: invalid data exception
        """
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        next_id = self.get_next_id()

        def new_body(next_id, kwargs):
            new = clazz(next_id, **kwargs)
            body = new.__dict__.copy()
            body['clazz_name'] = clazz_name
            if body.get('created'):
                body['created'] = body['created'].isoformat()
            return body

        self._write_object(next_id, self._prefix, new_body(next_id, kwargs))
        return clazz(next_id, **kwargs)
