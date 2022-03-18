from .file_data import FileData
from .thing_data import ThingData
from .file_relation_data import FileRelationData
from .thing_relation_data import ThingRelationData
from .table_data import TableData
from graphql_api.dynamodb.models import ToshiFileObject, ToshiTableObject, ToshiThingObject

dm_instance = None

def get_data_manager():
    return dm_instance

class DataManager():

    """DataManager provides the entry point to the data handlers
    """

    def __init__(self, search_manager, client_args=None):
        _args = client_args or {}
        self._file = FileData(_args, self, ToshiFileObject)
        self._thing = ThingData(_args, self, ToshiThingObject)
        self._table = TableData(_args, self, ToshiTableObject)
        self._file_relation = FileRelationData(_args, self, None)
        self._thing_relation = ThingRelationData(_args, self, None)
        self._search_manager = search_manager
        #set up the singleton
        global dm_instance
        dm_instance = self

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
    def thing_relation(self):
        return self._thing_relation

    @property
    def table(self):
        return self._table

    @property
    def search_manager(self):
        return self._search_manager