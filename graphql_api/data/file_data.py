"""
The object manager for File (and subclassed) schema objects
"""
from importlib import import_module
from datetime import datetime as dt
import json
import logging
import re
from boto3.resources.model import Identifier
from graphene.relay import connection
from graphql_api.dynamodb.models import ToshiIdentity, ToshiFileObject, ToshiThingObject
from pynamodb.exceptions import DoesNotExist
from pynamodb.transactions import TransactWrite, TransactGet, Connection

from .base_data import BaseDynamoDBData, append_uniq

logger = logging.getLogger(__name__)

from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)

class FileData(BaseDynamoDBData):
    """
    FileData provides the S3 interface forFile objects
    """

    def update(self, id, updated_body):
        print('UPDATE', updated_body)
        self.transact_update(id, self._prefix, updated_body)
        return self.from_json(updated_body)

    def create(self, clazz_name, **kwargs):
        """
        create the S3 representation if the File in S3. This is two files:

        Args:
         - clazz_name (String): the class name of schema object
         - kwargs (dict): the file metadata.

        Returns:
            File: the File object
        """
        new_instance = super().create(clazz_name, **kwargs)
        data_key = "%s/%s/%s" % (self._prefix, new_instance.id, new_instance.file_name)

        t0 = dt.utcnow()
        response2 = self._bucket.put_object(Key=data_key, Body="placeholder_to_be_overwritten")
        parts = self._client.generate_presigned_post(Bucket=self._bucket_name,
                                          Key=data_key,
                                          Fields={
                                            'acl': 'public-read',
                                            'Content-MD5': new_instance.md5_digest,
                                            'Content-Type': 'binary/octet-stream'
                                            },
                                          Conditions=[
                                              {"acl": "public-read"},
                                              ["starts-with", "$Content-Type", ""],
                                              ["starts-with", "$Content-MD5", ""]
                                          ]
                                      )

        db_metrics.put_duration(__name__, 'create[placeholder+generate-presigned-post]' , dt.utcnow()-t0)

        new_instance.post_url = json.dumps(parts['fields'])
        return new_instance

    def get_one(self, file_id, expected_class="File"):
        """
        Args:
            file_id (string): the object id

        Returns:
            File: the File/* object
        """
        jsondata = self.get_one_raw(file_id)

        #more migration hacks
        if not jsondata['clazz_name'] == expected_class:
            if expected_class == "InversionSolution":
                print(f"Upgrading {jsondata.get('clazz_name')} to InversionSolution")
                jsondata['clazz_name'] = expected_class

        return self.from_json(jsondata)

    def get_presigned_url(self, _id):
        """
        Args:
            _id (string): the object id

        Returns:
            string: a temporary URL that may be used to download the raw file data.
        """
        t0 = dt.utcnow()
        file = self.get_one(_id)
        key = "%s/%s/%s" % (self._prefix, _id, file.file_name)
        url = self._client.generate_presigned_url('get_object',
            Params={
                'Bucket': self._bucket_name,
                'Key': key,
            },
            ExpiresIn=3600)
        db_metrics.put_duration(__name__, 'get_presigned_url' , dt.utcnow()-t0)
        return url

    def get_all(self):
        """
        Returns:
            list: a list containing all the objects materialised from the S3 bucket
        """
        t0 = dt.utcnow()
        task_results = []
        for obj_summary in self._bucket.objects.filter(Prefix='%s/' % self._prefix):
            prefix, task_result_id, filename = obj_summary.key.split('/')
            assert prefix == self._prefix
            if filename=="object.json":
                task_results.append(self.get_one(task_result_id))
        db_metrics.put_duration(__name__, 'get_all' , dt.utcnow()-t0)
        return task_results

    @staticmethod
    def from_json(jsondata):
        logger.debug("from_json: %s" % str(jsondata))

        #datetime comversions
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.fromisoformat(created)

        clazz_name = jsondata.pop('clazz_name')
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)

        #Rule based migration
        if (clazz_name == "File" and (jsondata.get('tables') or jsondata.get('metrics'))):
            #this is actually an InversionSolution
            logger.info("from_json migration to InversionSolution of: %s" % str(jsondata))
            clazz = getattr(import_module('graphql_api.schema'), 'InversionSolution')

        ## produced_by_id -> produced_by schema migration
        produced_by_id = jsondata.pop('produced_by_id', None)
        if produced_by_id and not jsondata.get('produced_by'):
            jsondata['produced_by'] = produced_by_id

        #table datetime conversions
        if jsondata.get('tables'):
            for tbl in jsondata.get('tables'):
                tbl['created'] = dt.fromisoformat(tbl['created'])

        # print('updated json', jsondata)
        return clazz(**jsondata)
