"""
Module entry point
"""
import base64
from .base_s3_data import BaseS3Data

def get_objectid_from_global(global_id):
    _, _id  = base64.b64decode(global_id).decode().split(':')
    return _id



