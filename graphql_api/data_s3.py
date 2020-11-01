import boto3
import os
import json
from io import BytesIO
import datetime as dt
# from graphql import GraphQLError
import base64

class BaseS3Data():

    def __init__(self, client_args, db_manager):
        args = client_args or {}
        self.db_manager = db_manager

        self.client = boto3.client('s3', **args)
        self.bucket_name = os.environ.get('S3_BUCKET_NAME', "nshm-tosh-api-test")
        self.s3 = boto3.resource('s3')
        print("BaseS3Data.__init__ buecket:", self.bucket_name)
        self.bucket = self.s3.Bucket(self.bucket_name, client=self.client)
        self.prefix = self.__class__.__name__
        
    def get_next_id(self):
        size = sum(1 for _ in self.bucket.objects.filter(Prefix='%s/' % self.prefix))
        return size

    def get_all(self):
        task_results = []
        for obj_summary in self.bucket.objects.filter(Prefix='%s/' % self.prefix):
            prefix, task_result_id, filename = obj_summary.key.split('/')
            assert prefix == self.prefix
            task_results.append(self.get_one(task_result_id))
        return task_results

    def _write_object(self, object_id, body):    
        key = "%s/%s/%s" % (self.prefix, object_id, "object.json")
        response = self.bucket.put_object(Key=key, Body=json.dumps(body))

    def _read_object(self, object_id):
        key = "%s/%s/%s" % (self.prefix, object_id, "object.json")
        obj = self.s3.Object(bucket_name=self.bucket_name,
                        key=key,
                        client=self.client)
        fo = BytesIO()
        obj.download_fileobj(fo)
        fo.seek(0)
        return json.load(fo)

class TaskResultData(BaseS3Data):

    def create(self, **kwargs):
        from .schema import OpenshaRuptureGenResult
        next_id  = str(self.get_next_id())
        if not  kwargs['started'].tzname(): #must have a timezone set
            raise ValueError("'started' DateTime() field must have a timezone set.")
        
        new = OpenshaRuptureGenResult(next_id, **kwargs)
        body = new.__dict__.copy()
        body['started'] = body['started'].isoformat()
        self._write_object(next_id, body)
        return new
    
    def get_one(self, task_result_id):
        from .schema import OpenshaRuptureGenResult, TaskResultType

        jsondata = self._read_object(task_result_id)
        
        #Field type transforms...
        started = jsondata.get('started')
        if started:
            jsondata['started'] = dt.datetime.fromisoformat(started)
        print("get_one", jsondata)
        #remove deprecated field
        jsondata.pop('data_files', None)
        
        #add new fields
        if not jsondata.get('input_files'):
            jsondata['input_files'] = []           
        return OpenshaRuptureGenResult(**jsondata)

    # def get_files(self, task_result_id):
    #     return []

    def add_task_file(self, object_id, task_file_id):
        obj = self._read_object(object_id)
        try:
            obj['input_files'].append(task_file_id)
        except (AttributeError, KeyError):
            obj['input_files'] = [task_file_id]
        self._write_object(object_id, obj)


class DataFileData(BaseS3Data):

    def create(self, file_obj, **kwargs):
        from .schema import DataFile
        next_id  = str(self.get_next_id())
        new = DataFile(next_id, **kwargs)
        body = new.__dict__.copy()
        meta_key = "%s/%s/%s" % (self.prefix, next_id, "object.json")
        response = self.bucket.put_object(Key=meta_key, Body=json.dumps(body))

        data_key = "%s/%s/%s" % (self.prefix, next_id, body["file_name"])
        file_obj.seek(0)
        response2 = self.bucket.put_object(Key=data_key, Body=file_obj)
        return new

    def get_one(self, _id):
        from .schema import DataFile
        jsondata = self._read_object(_id)
        
        #remove deprecated field
        jsondata.pop('reader_tasks', None)            
        return DataFile(**jsondata)

    def get_presigned_url(self, _id):
        datafile = self.get_one(_id)
        key = "%s/%s/%s" % (self.prefix, _id, datafile.file_name)      
        url = self.client.generate_presigned_url('get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': key,
            },                                  
            ExpiresIn=3600)
        return url

    def get_next_id(self):
        """2 objects stored per ID, so divide object count by 2"""
        return int(super().get_next_id()/2)

    def get_all(self):
        task_results = []
        for obj_summary in self.bucket.objects.filter(Prefix='%s/' % self.prefix):
            prefix, task_result_id, filename = obj_summary.key.split('/')
            assert prefix == self.prefix
            if filename=="object.json":
                task_results.append(self.get_one(task_result_id))
        return task_results

    def add_task_file(self, object_id, task_file_id):
        obj = self._read_object(object_id)
        try:
            obj['consumers'].append(task_file_id)
        except (AttributeError):
            obj['consumers'] = [task_file_id]
        self._write_object(task_file_id, obj)


def get_objectid_from_global(global_id):
    type, id  = base64.b64decode(global_id).decode().split(':')
    return id
        
class TaskFileData(BaseS3Data):

    def create(self, **kwargs):
        from .schema import TaskFile
        next_id  = str(self.get_next_id())

        task_id = get_objectid_from_global(kwargs['task_id'])
        file_id = get_objectid_from_global(kwargs['file_id'])

        task = self.db_manager.task.get_one(task_id)
        file = self.db_manager.file.get_one(file_id)

        new = TaskFile(id=next_id, task=task, file=file)
        #disk representation has just objectids
        body = dict(id=next_id, task_id=task_id, file_id=file_id)

        #write new object
        meta_key = "%s/%s/%s" % (self.prefix, next_id, "object.json")
        response = self.bucket.put_object(Key=meta_key, Body=json.dumps(body))

        #TODO update file and task pointers to new TaskFile
        self.db_manager.task.add_task_file(task_id, next_id)
        self.db_manager.file.add_task_file(file_id, next_id)
        return new


    def get_one(self, _id):
        from .schema import TaskFile
        key = "%s/%s/%s" % (self.prefix, _id, "object.json")
        print("KEY:", key)
        obj = self.s3.Object(bucket_name=self.bucket_name,
                        key=key,
                        client=self.client)
        fo = BytesIO()
        obj.download_fileobj(fo)
        fo.seek(0)
        jsondata = json.load(fo)

        task = self.db_manager.task.get_one(jsondata['task_id'])
        file = self.db_manager.file.get_one(jsondata['file_id'])

        return TaskFile(id=jsondata['id'], task=task, file=file)


class DataManager():

    def __init__(self, client_args=None):
        _args = client_args or {}
        self._task = TaskResultData(_args, self)
        self._file = DataFileData(_args, self)
        self._task_file = TaskFileData(_args, self)

    @property
    def task(self):
        return self._task

    @property
    def file(self):
        return self._file

    @property
    def task_file(self):
        return self._task_file

# def get_faction(_id):
#     from .schema import Faction
#     Faction(id="1", name="Alliance to Restore the Republic", task_results=["1", "2", "3", "4", "5"])
