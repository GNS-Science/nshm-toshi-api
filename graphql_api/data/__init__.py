"""
Module entry point
"""

import base64

from .base_data import BaseData, BaseDynamoDBData
from .data_manager import get_data_manager
from .file_data import FileData
from .table_data import TableData
from .thing_data import ThingData
