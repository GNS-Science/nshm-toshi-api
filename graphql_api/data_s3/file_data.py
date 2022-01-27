"""
The object manager for File (and subclassed) schema objects
"""
from importlib import import_module
from datetime import datetime as dt
import json
import logging
from graphql_api.dynamodb.models import ToshiObject

from .base_s3_data import BaseS3Data, append_uniq

logger = logging.getLogger(__name__)

from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)

class FileData(BaseS3Data):
    """
    FileData provides the S3 interface forFile objects
    """

    def update(self, id, updated_body):
        #TODO error handling
        #print('UPDATE', updated_body)
        logger.info("FiledData.update: %s : %s" % (id, str(updated_body)))
        self._write_object(id, updated_body)
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
        from graphql_api.schema import File
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        next_id  = str(self.get_next_id())

        new = clazz(next_id, **kwargs)
        body = new.__dict__.copy()
        body['clazz_name'] = clazz_name
        if body.get('created'):
            body['created'] = body['created'].isoformat()

        #TODO error handling
        self._write_object(next_id, body)

        data_key = "%s/%s/%s" % (self._prefix, next_id, body["file_name"])

        t0 = dt.utcnow()
        response2 = self._bucket.put_object(Key=data_key, Body="placeholder_to_be_overwritten")
        parts = self._client.generate_presigned_post(Bucket=self._bucket_name,
                                          Key=data_key,
                                          Fields={
                                            'acl': 'public-read',
                                            'Content-MD5': body.get('md5_digest'),
                                            'Content-Type': 'binary/octet-stream'
                                            },
                                          Conditions=[
                                              {"acl": "public-read"},
                                              ["starts-with", "$Content-Type", ""],
                                              ["starts-with", "$Content-MD5", ""]
                                          ]
                                      )

        db_metrics.put_duration(__name__, 'create[placeholder+generate-presigned-post]' , dt.utcnow()-t0)

        new.post_url = json.dumps(parts['fields'])
        return new

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

    def get_next_id(self):
        """FIle used  2 S3 objects, so we divide the S3 object count by 2

        Returns:
            int: the next available id
        """
        t0 = dt.utcnow()
        db_metrics.put_duration(__name__, 'get_next_id' , dt.utcnow()-t0)
        size = sum(1 for _ in ToshiObject.scan(ToshiObject.object_id.startswith(self._prefix)))
        return append_uniq(float(size))

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

    def add_thing_relation(self, file_id, thing_id, thing_role):
        """
        Args:
            file_id (string): the file object id
            thing_id (string): the thing object id
            thing_role: the thing's role
        """
        obj = self._read_object(file_id)
        logger.info("add_thing_relation: file_id %s, thing_id: %s" % (file_id, thing_id))
        try:
            obj['relations'].append({'id': thing_id, 'role': thing_role})
        except (KeyError, AttributeError):
            obj['relations'] = [{'id': thing_id, 'role': thing_role}]
        self._write_object(file_id, obj)
        return self.from_json(obj)

    @staticmethod
    def from_json(jsondata):
        logger.info("from_json: %s" % str(jsondata))

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

        #table datetime conversions
        if jsondata.get('tables'):
            for tbl in jsondata.get('tables'):
                tbl['created'] = dt.fromisoformat(tbl['created'])

        # print('updated json', jsondata)
        return clazz(**jsondata)
