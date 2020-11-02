"""
Object manager for File schema objects
"""
import json
from .base_s3_data import BaseS3Data

class FileData(BaseS3Data):
    """
    FileData provides the S3 interface forFile objects
    """
    def create(self, file_obj, **kwargs):
        """create the S3 represtentation if the File in S3. This is two files:

         - the object.json contains the file metadata.
         - the raw file object, named as per the object filename.

        Args:
            file_obj (dict): file meta data fields
            **kwargs: not used
        Returns:
            File: the File object
        """
        from graphql_api.schema import File
        next_id  = str(self.get_next_id())
        new = File(next_id, **kwargs)
        body = new.__dict__.copy()
        meta_key = "%s/%s/%s" % (self._prefix, next_id, "object.json")
        #TODO error handling
        response = self._bucket.put_object(Key=meta_key, Body=json.dumps(body))

        data_key = "%s/%s/%s" % (self._prefix, next_id, body["file_name"])
        if file_obj:
            file_obj.seek(0)
            #TODO error handling...     
            response2 = self._bucket.put_object(Key=data_key, Body=file_obj)
        else:
            response2 = self._bucket.put_object(Key=data_key, Body="placeholder_to_be_overwritten")
            parts = self._client.generate_presigned_post(Bucket=self._bucket_name,
                                              Key=data_key,
                                              Fields={
                                                'acl': 'public-read',
                                                'Content-MD5': body.get('hex_digest'),
                                                'Content-Type': 'binary/octet-stream'
                                                },
                                              Conditions=[
                                                  {"acl": "public-read"},
                                                  ["starts-with", "$Content-Type", ""],
                                                  ["starts-with", "$Content-MD5", ""]
                                              ]
                                              )
                                
            kwargs['post_url'] = json.dumps(parts['fields'])
            new = File(next_id, **kwargs)
        return new

    def get_one(self, _id):
        """
        Args:
            _id (string): the object id

        Returns:
            File: the File object
        """
        from graphql_api.schema import File
        jsondata = self._read_object(_id)
        #remove deprecated field
        jsondata.pop('reader_tasks', None)
        return File(**jsondata)

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
        return int(super().get_next_id()/2)

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

    def add_task_file(self, object_id, task_file_id):
        """Append the new file object id to the related task in S3.

        Args:
            object_id (string): the file object id
            task_file_id (string): the task object id
        """
        obj = self._read_object(object_id)
        try:
            obj['consumers'].append(task_file_id)
        except AttributeError:
            obj['consumers'] = [task_file_id]
        self._write_object(task_file_id, obj)
