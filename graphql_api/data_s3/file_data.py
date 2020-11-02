import json
from .base_s3_data import BaseS3Data

class FileData(BaseS3Data):

    def create(self, file_obj, **kwargs):
        from graphql_api.schema import File
        next_id  = str(self.get_next_id())
        new = File(next_id, **kwargs)
        body = new.__dict__.copy()
        meta_key = "%s/%s/%s" % (self._prefix, next_id, "object.json")
        response = self._bucket.put_object(Key=meta_key, Body=json.dumps(body))

        data_key = "%s/%s/%s" % (self._prefix, next_id, body["file_name"])
        file_obj.seek(0)
        response2 = self._bucket.put_object(Key=data_key, Body=file_obj)
        return new

    def get_one(self, _id):
        from graphql_api.schema import File

        jsondata = self._read_object(_id)
        
        #remove deprecated field
        jsondata.pop('reader_tasks', None)            
        return File(**jsondata)

    def get_presigned_url(self, _id):
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
        """2 objects stored per ID, so divide object count by 2"""
        return int(super().get_next_id()/2)

    def get_all(self):
        task_results = []
        for obj_summary in self._bucket.objects.filter(Prefix='%s/' % self._prefix):
            prefix, task_result_id, filename = obj_summary.key.split('/')
            assert prefix == self._prefix
            if filename=="object.json":
                task_results.append(self.get_one(task_result_id))
        return task_results

    def add_task_file(self, object_id, task_file_id):
        obj = self._read_object(object_id)
        try:
            obj['consumers'].append(task_file_id)
        except AttributeError:
            obj['consumers'] = [task_file_id]
        self._write_object(task_file_id, obj)
