"""
Module entry point
"""
import base64

def get_objectid_from_global(global_id):
    _, _id  = base64.b64decode(global_id).decode().split(':')
    return _id

from .base_s3_data import BaseS3Data
from .task_data import TaskData
from .file_data import FileData
from .task_file_data import TaskFileData


class DataManager():

    """DataManager provides the entry point to the s3 data handlers
    """

    def __init__(self, search_manager, client_args=None):
        _args = client_args or {}
        self._task = TaskData(_args, self)
        self._file = FileData(_args, self)
        self._task_file = TaskFileData(_args, self)
        self._search_manager = search_manager

    @property
    def task(self):
        return self._task

    @property
    def file(self):
        return self._file

    @property
    def task_file(self):
        return self._task_file

    @property
    def search_manager(self):
        return self._search_manager
