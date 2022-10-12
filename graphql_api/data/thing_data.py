"""
Object manager for Thing schema objects
"""
import datetime as dt
import json
import logging
from importlib import import_module
from benedict import benedict

from .base_data import BaseDynamoDBData
# from .helpers import get_objectid_from_global
from graphql_relay import from_global_id, to_global_id

logger = logging.getLogger(__name__)

class ThingData(BaseDynamoDBData):
    """
    ThingData provides the data storage for Thing objects
    """

    def create(self, clazz_name, **kwargs):
        if not  kwargs['created'].tzname(): #must have a timezone set
            raise ValueError("'created' DateTime() field must have a timezone set.")
        return super().create(clazz_name, **kwargs)

    def migrate_old_thing_object(self, thing):
        """
        Migrate to the new_simplified object from the old form

        NB only handles gitrefs
        """
        if thing.get('clazz_name') == 'RuptureGenerationTask':
            ##fix gitrefs
            env = dict()
            gitrefs = thing.pop('git_refs', None)
            if gitrefs:
                env["gitref_opensha-core"] = gitrefs.get('opensha_core', "")
                env["gitref_opensha-commons"] = gitrefs.get('opensha_commons', "")
                env["gitref_opensha-ucerf3"] = gitrefs.get('opensha_ucerf3', "")
                env["gitref_nshm-nz-opensha"] = gitrefs.get('nshm_nz_opensha', "")

            env_as_kvs = [dict(k=str(k), v=str(v)) for k, v in env.items()]
            envnew = thing.get('environment') or []
            envnew.extend(env_as_kvs)
            thing['environment'] = envnew
        
        # print('Migrated ', thing)
        return thing

    def get_one(self, thing_id):
        """
        Args:
            _id (string): the object id
        Returns:
            File: the Thing object
        """

        jsondata = self.migrate_old_thing_object(self._read_object(thing_id))
        return self.from_json(jsondata)


    def update(self, clazz_name, thing_id, **kwargs):
        """
        Args:
            task_id (TYPE): the object id
            **kwargs: the received schema fields

        Returns:
            TYPE: the Thing object
        """
        _type, this_id = from_global_id(thing_id)
        #print('thingupdate$$$$$$$$$$$', this_id, thing_id, clazz_name)
        assert _type == clazz_name

        if kwargs.get('created'):
            kwargs['created'] = kwargs['created'].isoformat()

        if kwargs.get('updated'):
            kwargs['updated'] = kwargs['updated'].isoformat()

        jsondata = self.migrate_old_thing_object(self.get_one_raw(this_id))
        body = benedict(jsondata)
        body.merge(kwargs)
        logger.debug("ThingData.update: %s : %s" % (this_id, str(body)))
        self.transact_update(this_id, _type, body)
        return self.from_json(body)

    def add_file_relation(self, thing_id, file_id, file_role):
        obj = self._read_object(thing_id)
        logger.info("add_file_relation: thing_id: %s, file_id %s, " % (thing_id, file_id))
        try:
            obj['files'].append({'file_id': file_id, 'file_role': file_role})
        except (KeyError, AttributeError):
            obj['files'] = [{'file_id': file_id, 'file_role': file_role}]
        self.transact_update(thing_id, self._prefix, obj)
        return self.from_json(obj)

    @staticmethod
    def from_json(jsondata):
        logger.debug("from_json: %s" % str(jsondata))

        created = jsondata.get('created')
        if created and not isinstance(created, dt.datetime):
            jsondata['created'] = dt.datetime.fromisoformat(created)

        updated = jsondata.get('updated')
        if updated and not isinstance(updated, dt.datetime):
            jsondata['updated'] = dt.datetime.fromisoformat(updated)
            
        clazz_name = jsondata.pop('clazz_name')
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)

        logger.debug(f'from_json() CLAZZ from json: {jsondata}')
        return clazz(**jsondata)
