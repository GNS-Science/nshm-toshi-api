"""
BaseData is the base class for AWS_S3 data handlers
"""

import enum
import json
import logging
import random
from collections import namedtuple
from datetime import datetime as dt
from importlib import import_module
from io import BytesIO
from typing import Dict

import backoff
import boto3
import graphql
import pynamodb.exceptions
from pynamodb.connection.base import Connection
from pynamodb.exceptions import DoesNotExist
from pynamodb.transactions import TransactWrite

import graphql_api.dynamodb
from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import (
    CW_METRICS_RESOLUTION,
    DB_ENDPOINT,
    FIRST_DYNAMO_ID,
    IS_OFFLINE,
    REGION,
    S3_BUCKET_NAME,
    STACK_NAME,
    TESTING,
)
from graphql_api.dynamodb.models import ToshiIdentity

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

logger = logging.getLogger(__name__)

_ALPHABET = list("23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


ObjectIdentityRecord = namedtuple("ObjectIdentityRecord", "object_type, object_id")


def append_uniq(size):
    uniq = ''.join(random.choice(_ALPHABET) for _ in range(5))
    return str(size) + uniq


def json_serialised(obj):
    """A simple wrapper to facilitate testing."""
    return json.dumps(obj)


def replace_enums(kwargs: Dict) -> Dict:
    """Replace any Enum members with their values.

    So that Graphene object instances can be serialised as json.
    """
    new_kwargs = kwargs.copy()
    for key, value in kwargs.items():
        if isinstance(value, enum.Enum):
            new_kwargs[key] = value.value
        elif isinstance(value, list):
            new_list = []
            for itm in value:
                if isinstance(itm, enum.Enum):
                    new_list.append(itm.value)
                else:
                    new_list.append(itm)
            new_kwargs[key] = new_list
    return new_kwargs


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

    def get_one_raw(self, _id: str):
        """
        Args:
            _id: the object id

        Returns:
            File: the File object json
        """
        obj = self._read_object(_id)
        return obj

    def get_one(self, _id: str):
        """Summary

        Args:
            _id: id for an object

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
        for obj_summary in self.s3_bucket.objects.filter(Prefix='%s/' % self._prefix):
            prefix, result_id, _ = obj_summary.key.split('/')
            assert prefix == self._prefix
            object = self.get_one(result_id)
            if clazz is None or isinstance(object, clazz):
                results.append(object)
        db_metrics.put_duration(__name__, 'get_all', dt.utcnow() - t0)
        return results

    def get_all_s3_paginated(self, limit, after):
        """legacy iterator"""
        count, seen = 0, 0
        after = after or ""
        # TODO refine this, see
        #   https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/bucket/objects.html#filter
        # need to handle multiple versions
        # should use:
        #  - Marker to define start of itertion
        #  - MaxKeys to limit iteration
        marker = f"{self.prefix}/{after}" if after else ""
        filtered_objects = self.s3_bucket.objects.filter(
            Prefix='%s/' % self.prefix,
            Marker=marker,
            MaxKeys=limit,  # note this will optimise the filter behaviuor, but does not terminate the loop,
        )

        # setup f-string arguments for object_ids
        keylen = len(str(FIRST_DYNAMO_ID))
        fill = " "
        align = '>'

        for obj_summary in filtered_objects:
            prefix, object_id, file_name = obj_summary.key.split('/')
            seen += 1

            # need special handling for File because these are expected to have two objects
            if not file_name == 'object.json':
                continue

            if object_id == after:
                # print(f"skip marker {object_id}")
                continue

            # for FileData types
            #  respect the FIRST_DYNAMO_DB
            if self.prefix == "FileData":
                numeric_part = object_id.split(".")[0]
                padded_id = f'{numeric_part:{fill}{align}{keylen}}'
                if padded_id >= str(FIRST_DYNAMO_ID):
                    # print(f"skip legacy {object_id}")
                    continue

            raw_object = self._from_s3(object_id)
            latest_identity = ObjectIdentityRecord(object_type=raw_object['clazz_name'], object_id=object_id)
            yield latest_identity
            count += 1

            if count >= limit:
                break

        print(f'looked at {seen} object_summaries; yielded {count} objects')

    @property
    def prefix(self):
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
        except DoesNotExist:
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
        except Exception:
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

        # We've been caught out by Schema classes that are not json-serialisable (the ENUM issue).
        # This should make that more obvious if it happens again.
        try:
            json_serialised(body)
        except Exception:
            msg = (
                "This object cannot be persisted to a PynamoDB.Model,"
                " check that all enums and types are json serialisable!"
            )
            logging.error(msg)
            raise graphql.GraphQLError(f'{__name__}._write_object() method failed with exception. %s' % msg)

        toshi_object = self._model(object_id=str(object_id), object_type=body['clazz_name'], object_content=body)

        logger.debug(f"toshi_object: {toshi_object}")

        with TransactWrite(connection=self._connection) as transaction:
            transaction.update(identity, actions=[ToshiIdentity.object_id.add(1)])
            transaction.save(toshi_object)

        logger.info(f"toshi_object: object_id {object_id} object_type: {body['clazz_name']}")

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
            transaction.update(model, actions=[self._model.object_content.set(replace_enums(body))])

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
        logger.info(f"create() {clazz_name} {kwargs} for model class : {self._model}")

        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        next_id = self.get_next_id()

        # TODO: this whole approach sucks !@#%$#
        # consider the ENUM problem, and datatime serialisation
        # cant we just use the graphene classes json serialisation ??
        # UPDATE: there is no such support, I guess graphene doesn't expect this sort of use case?
        # For now we stick with our helper methods `new_body` and 'replace_enums`
        #  and discuss in code review

        def new_body(next_id, kwargs):
            new = clazz(next_id, **kwargs)
            body = new.__dict__.copy()
            body['clazz_name'] = clazz_name
            if body.get('created'):
                body['created'] = body['created'].isoformat()
            return body

        object_instance = clazz(next_id, **kwargs)

        logger.debug(object_instance.__class__)
        logger.debug(type(object_instance))
        logger.debug(dir(object_instance))
        logger.debug(f" TODICT: {graphql.utilities.ast_to_dict(object_instance)}")

        try:
            self._write_object(next_id, self._prefix, new_body(next_id, replace_enums(kwargs)))
        except Exception as err:
            logger.error(F"failed to write {clazz_name} {kwargs} {err}")
            raise

        logger.info(f"create() object_instance: {object_instance}")
        return object_instance

    def get_all(self, object_type, limit: int, after: str):
        t0 = dt.utcnow()
        after = after or "-1"
        logger.info(f"get_all, {self._model} {self.prefix} {object_type} after {after}")
        for object_meta in self._model.model_id_index.query(
            object_type, self._model.object_id > after, limit=limit  # range condition
        ):
            yield ObjectIdentityRecord(object_meta.object_type, object_meta.object_id)

        db_metrics.put_duration(__name__, 'get_all', dt.utcnow() - t0)
