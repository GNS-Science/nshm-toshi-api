"""
Object manager for Task schema objects
"""
import datetime as dt
import logging
from .base_s3_data import BaseS3Data

logger = logging.getLogger(__name__)

class TaskData(BaseS3Data):
    """
    TaskData provides the S3 interface for Task objects
    """
    def create(self, **kwargs):
        """
        Args:
            **kwargs: the field data
        Returns:
            RuptureGenerationTask: Description
        Raises:
            ValueError: invalid data exception
        """
        from graphql_api.schema import RuptureGenerationTask
        next_id  = str(self.get_next_id())
        if not  kwargs['started'].tzname(): #must have a timezone set
            raise ValueError("'started' DateTime() field must have a timezone set.")

        new = RuptureGenerationTask(next_id, **kwargs)
        body = new.__dict__.copy()
        body['started'] = body['started'].isoformat()
        self._write_object(next_id, body)
        return new

    def get_one(self, task_result_id):
        """
        Args:
            _id (string): the object id
        Returns:
            File: the Task object
        """
        from graphql_api.schema import RuptureGenerationTask

        jsondata = self._read_object(task_result_id)

        #Field type transforms...
        started = jsondata.get('started')
        if started:
            jsondata['started'] = dt.datetime.fromisoformat(started)
        logger.info("get_one: %s" % str(jsondata))

        #remove deprecated field(s)...
        jsondata.pop('data_files', None)

        #add new fields
        if not jsondata.get('input_files'):
            jsondata['input_files'] = []
        return RuptureGenerationTask(**jsondata)


    def add_task_file(self, object_id, task_file_id):
        obj = self._read_object(object_id)
        try:
            obj['input_files'].append(task_file_id)
        except (AttributeError, KeyError):
            obj['input_files'] = [task_file_id]
        self._write_object(object_id, obj)
