"""
Module entry point
"""
import base64

def get_objectid_from_global(global_id):
    _, _id  = base64.b64decode(global_id).decode().split(':')
    return _id

from .base_s3_data import BaseS3Data
# from .event_data import EventData
from .file_data import FileData
# from .event_file_data import EventFileData
from .thing_data import ThingData
from .file_relation_data import FileRelationData

class DataManager():

    """DataManager provides the entry point to the s3 data handlers
    """

    def __init__(self, search_manager, client_args=None):
        _args = client_args or {}
        # self._event = EventData(_args, self)
        self._file = FileData(_args, self)
        # self._event_file = EventFileData(_args, self)
        self._thing = ThingData(_args, self)
        self._file_relation = FileRelationData(_args, self)
        self._search_manager = search_manager

    # @property
    # def event(self):
    #     return self._event

    @property
    def thing(self):
        return self._thing

    @property
    def file(self):
        return self._file

    # @property
    # def event_file(self):
    #     return self._event_file

    @property
    def file_relation(self):
        return self._file_relation

    @property
    def search_manager(self):
        return self._search_manager

