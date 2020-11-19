"""
Object manager for FileRelationInterface schema objects
"""
import json
from io import BytesIO
import logging
from importlib import import_module
from . import get_objectid_from_global
from .base_s3_data import BaseS3Data


logger = logging.getLogger(__name__)

class FileRelationData(BaseS3Data):
    """
    FileRelationData provides the S3 interface for FileRelation objects
    """
    def create(self, clazz_name, related_id, file_id, **kwargs):
        """
        Args:
            clazz_name (String): the class name of schema object
            related_id (TYPE): Description
            file_id (TYPE): Description
            **kwargs: the field data

        Returns:
            Thing: a new instance of the clazz_name

        """
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        next_id  = str(self.get_next_id())
        # if not  kwargs['created'].tzname(): #must have a timezone set
        #     raise ValueError("'created' DateTime() field must have a timezone set.")

        file_relation = clazz(next_id, thing_id=related_id, file_id=file_id, **kwargs)
        body = file_relation.__dict__.copy()
        body['clazz_name'] = clazz_name
        # body['created'] = body['created'].isoformat()
        self._write_object(next_id, body)

        #update backref to new FileRelation
        #self._db_manager.thing.add_file_relation(thing_id=related_id, file_relation_id=next_id)
        file_relation.file = self._db_manager.file.add_thing_relation(file_id=file_id, relation_id=next_id)
        file_relation.thing = self._db_manager.thing.add_file_relation(thing_id=related_id, relation_id=next_id)
        return file_relation

    def get_one(self, _id):
        """
        Args:
            _id (string): the object id
        Returns:
            File: the Thing object
        """
        jsondata = self._read_object(_id)
        logger.info("get_one: %s" % str(jsondata))
        print(jsondata)
        # task = self._db_manager.thing.get_one(jsondata['task_id'])
        # file = self._db_manager.file.get_one(jsondata['file_id'])
        # #task_role = TaskFileRole.get(jsondata.get('task_role', 'undefined'))
        relation =  self.from_json(jsondata)
        relation.file = self._db_manager.file.get_one(jsondata['file_id'])
        relation.thing = self._db_manager.thing.get_one(jsondata['thing_id'])
        return relation


    @staticmethod
    def from_json(jsondata):
         #datetime comversions
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.datetime.fromisoformat(created)

        clazz_name = jsondata.pop('clazz_name')
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        # print('updated json', jsondata)
        return clazz(**jsondata)