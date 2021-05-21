"""
The object manager for File (and subclassed) schema objects
"""
import json
from importlib import import_module
import logging

from .base_s3_data import BaseS3Data, append_uniq

logger = logging.getLogger(__name__)


class FileData(BaseS3Data):
    """
    FileData provides the S3 interface forFile objects
    """
    def create(self, clazz_name, **kwargs):
        """
        create the S3 represtentation if the File in S3. This is two files:

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

        #TODO error handling
        self._write_object(next_id, body)

        data_key = "%s/%s/%s" % (self._prefix, next_id, body["file_name"])

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
            # print('S3 URL: %s' % parts['url'])
            # print('fields: %s' % parts['fields'])
        new.post_url = json.dumps(parts['fields'])
        return new

    def get_one(self, file_id):
        """
        Args:
            file_id (string): the object id

        Returns:
            File: the File object
        """
        jsondata = self._read_object(file_id)
        return self.from_json(jsondata)
        # return File(**jsondata)

    def get_presigned_url(self, _id):
        """
        Args:
            _id (string): the object id

        Returns:
            string: a temporary URL that may be used to download the raw file data.
        """
        file = self.get_one(_id)
        key = "%s/%s/%s" % (self._prefix, _id, file.file_name)
        url = self._client.generate_presigned_url('get_object',
            Params={
                'Bucket': self._bucket_name,
                'Key': key,
            },
            ExpiresIn=3600)
        return url

    def get_next_id(self):
        """FIle used  2 S3 objects, so we divide the S3 object count by 2

        Returns:
            int: the next available id
        """
        size = sum(1 for _ in self._bucket.objects.filter(Prefix='%s/' % self._prefix))/2
        return append_uniq(size)
        # return int(super().get_next_id()/2)

    def get_all(self):
        """
        Returns:
            list: a list containing all the objects materialised from the S3 bucket
        """
        task_results = []
        for obj_summary in self._bucket.objects.filter(Prefix='%s/' % self._prefix):
            prefix, task_result_id, filename = obj_summary.key.split('/')
            assert prefix == self._prefix
            if filename=="object.json":
                task_results.append(self.get_one(task_result_id))
        return task_results

    def add_thing_relation(self, file_id, relation_id):
        """
        Args:
            file_id (string): the file object id
            relation_id (string): the thing object id
        """
        obj = self._read_object(file_id)
        logger.info("add_thing_relation: file_id %s, thing_id: %s" % (file_id, relation_id))
        try:
            obj['relations'].append(relation_id)
        except (KeyError, AttributeError):
            obj['relations'] = [relation_id]
        self._write_object(file_id, obj)
        return self.from_json(obj)

    @staticmethod
    def from_json(jsondata):
        logger.info("get_one: %s" % str(jsondata))

        #datetime comversions
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.datetime.fromisoformat(created)

        clazz_name = jsondata.pop('clazz_name')
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        # print('updated json', jsondata)
        return clazz(**jsondata)
