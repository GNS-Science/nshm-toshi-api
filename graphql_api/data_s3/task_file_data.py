import json
from io import BytesIO
from . import get_objectid_from_global
from .base_s3_data import BaseS3Data

class TaskFileData(BaseS3Data):

    def create(self, **kwargs):
        from graphql_api.schema  import TaskFile
        next_id  = str(self.get_next_id())

        task_id = get_objectid_from_global(kwargs['task_id'])
        file_id = get_objectid_from_global(kwargs['file_id'])

        task = self._db_manager.task.get_one(task_id)
        file = self._db_manager.file.get_one(file_id)

        new = TaskFile(id=next_id, task=task, file=file)
        #disk representation has just objectids
        body = dict(id=next_id, task_id=task_id, file_id=file_id)

        #write new object
        meta_key = "%s/%s/%s" % (self._prefix, next_id, "object.json")
        response = self._bucket.put_object(Key=meta_key, Body=json.dumps(body))

        #TODO update file and task pointers to new TaskFile
        self._db_manager.task.add_task_file(task_id, next_id)
        self._db_manager.file.add_task_file(file_id, next_id)
        return new


    def get_one(self, _id):
        from graphql_api.schema import TaskFile
        key = "%s/%s/%s" % (self._prefix, _id, "object.json")
        print("KEY:", key)
        obj = self._s3.Object(bucket_name=self._bucket_name,
                        key=key,
                        client=self._client)
        fo = BytesIO()
        obj.download_fileobj(fo)
        fo.seek(0)
        jsondata = json.load(fo)

        task = self._db_manager.task.get_one(jsondata['task_id'])
        file = self._db_manager.file.get_one(jsondata['file_id'])

        return TaskFile(id=jsondata['id'], task=task, file=file)
