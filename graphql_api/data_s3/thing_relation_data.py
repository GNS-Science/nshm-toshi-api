"""
Object manager for ThingRelation (and subclassed) schema objects
"""
import logging
from importlib import import_module
from .base_s3_data import BaseDynamoDBData

logger = logging.getLogger(__name__)

class ThingRelationData(BaseDynamoDBData):
    """
    ThingRelationData provides the S3 interface for ThingRelation objects
    """
    def create(self, clazz_name, parent_id, child_id, **kwargs):
        """
        Args:
            clazz_name (String): the class name of schema object
            parent_id (TYPE): Description
            child_id (TYPE): Description
            **kwargs: the field data

        Returns:
            a new instance of the clazz_name

        """
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        next_id  = str(self.get_next_id())
        # if not  kwargs['created'].tzname(): #must have a timezone set
        #     raise ValueError("'created' DateTime() field must have a timezone set.")

        body = dict(id=next_id, parent_id=parent_id, child_id=child_id, **kwargs)
        body['clazz_name'] = clazz_name
        # body['created'] = body['created'].isoformat()
        self._write_object(next_id, body)

        # #update backrefs to new ThingRelation
        parent = self._db_manager.thing.add_child_relation(thing_id=parent_id, relation_id=next_id)
        child = self._db_manager.thing.add_parent_relation(thing_id=child_id, relation_id=next_id)

        # thing_relation.thing = self._db_manager.thing.add_thing_relation(thing_id=parent_id, relation_id=next_id)
        return clazz(id=next_id, parent=parent, child=child)

    def get_one(self, _id):
        """
        Args:
            _id (string): the object id
        Returns:
            File: the Thing object
        """
        jsondata = self._read_object(_id)
        logger.info("get_one: %s" % str(jsondata))
        relation =  self.from_json(jsondata)
        relation.child = self._db_manager.thing.get_one(jsondata['child_id'])
        relation.parent = self._db_manager.thing.get_one(jsondata['parent_id'])
        return relation


    @staticmethod
    def from_json(jsondata):
         #datetime comversions
        # created = jsondata.get('created')
        # if created:
        #     jsondata['created'] = dt.datetime.fromisoformat(created)

        clazz_name = jsondata.pop('clazz_name')
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        return clazz(**jsondata)