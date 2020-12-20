from .file_data import FileData
from .thing_data import ThingData
from .file_relation_data import FileRelationData

class DataManager():

    """DataManager provides the entry point to the data handlers
    """

    def __init__(self, search_manager, client_args=None):
        _args = client_args or {}
        self._file = FileData(_args, self)
        self._thing = ThingData(_args, self)
        self._file_relation = FileRelationData(_args, self)
        self._search_manager = search_manager

    @property
    def thing(self):
        return self._thing

    @property
    def file(self):
        return self._file

    @property
    def file_relation(self):
        return self._file_relation

    @property
    def search_manager(self):
        return self._search_manager