"""
Module entry point
"""

def get_objectid_from_global(global_id):
    _, _id  = base64.b64decode(global_id).decode().split(':')
    return _id

from .base_s3_data import BaseS3Data
from .task_data import TaskResultData
from .file_data import FileData
from .task_file_data import TaskFileData


class DataManager():

    """DataManager provides the entry point to the s3 data handlers
    """
    
    def __init__(self, client_args=None):
        _args = client_args or {}
        self._task = TaskResultData(_args, self)
        self._file = FileData(_args, self)
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