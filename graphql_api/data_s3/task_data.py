"""
Object manager for Task schema objects
"""
# import datetime as dt
# import logging
# from benedict import benedict

# from .base_s3_data import BaseS3Data
# from . import get_objectid_from_global

# logger = logging.getLogger(__name__)


# class TaskData(BaseS3Data):
#     """
#     TaskData provides the S3 interface for Task objects
#     """
#     def create(self, **kwargs):
#         """
#         Args:
#             **kwargs: the field data
#         Returns:
#             RuptureGenerationTask: Description
#         Raises:
#             ValueError: invalid data exception
#         """
#         from graphql_api.schema import RuptureGenerationTask
#         next_id  = str(self.get_next_id())
#         if not  kwargs['started'].tzname(): #must have a timezone set
#             raise ValueError("'started' DateTime() field must have a timezone set.")

#         new = RuptureGenerationTask(next_id, **kwargs)
#         body = new.__dict__.copy()
#         body['started'] = body['started'].isoformat()
#         self._write_object(next_id, body)
#         return new


#     def get_one(self, task_result_id):
#         """
#         Args:
#             _id (string): the object id
#         Returns:
#             File: the Task object
#         """
#         from graphql_api.schema import RuptureGenerationTask
#         jsondata = self._read_object(task_result_id)
#         return RuptureGenerationTask.from_json(jsondata)


#     def add_task_file(self, task_id, task_file_id):
#         """
#         Args:
#             task_id (TYPE): the task_id
#             task_file_id (TYPE): the task_file_id
#         """
#         obj = self._read_object(task_id)
#         try:
#             obj['files'].append(task_file_id)
#         except (AttributeError, KeyError):
#             obj['files'] = [task_file_id]
#         self._write_object(task_id, obj)


#     def update(self, task_id, **kwargs):
#         """
#         Args:
#             task_id (TYPE): the object id
#             **kwargs: the received schema fields

#         Returns:
#             TYPE: the Task object
#         """
#         from graphql_api.schema import RuptureGenerationTask

#         this_id = get_objectid_from_global(task_id)

#         bd1 = benedict(self.get_one(this_id).__dict__.copy())
#         bd1.merge(kwargs)
#         bd1['started'] = bd1['started'].isoformat()
#         self._write_object(this_id, bd1)
#         # print(bd1)
#         return RuptureGenerationTask(**bd1)
