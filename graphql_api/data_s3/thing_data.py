"""
Object manager for Thing schema objects
"""
import datetime as dt
import logging
from importlib import import_module
from benedict import benedict

from .base_s3_data import BaseS3Data
# from .helpers import get_objectid_from_global
from graphql_relay import from_global_id, to_global_id

logger = logging.getLogger(__name__)

class ThingData(BaseS3Data):
    """
    ThingData provides the data storage for Thing objects
    """
    def create(self, clazz_name, **kwargs):
        """
        Args:
            clazz_name (String): the class name of schema object
            **kwargs: the field data

        Returns:
            Thing: a new instance of the clazz_name

        Raises:
            ValueError: invalid data exception
        """
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        next_id  = str(self.get_next_dynamo_id())
        if not  kwargs['created'].tzname(): #must have a timezone set
            raise ValueError("'created' DateTime() field must have a timezone set.")

        new = clazz(next_id, **kwargs)
        body = new.__dict__.copy()
        body['clazz_name'] = clazz_name
        body['created'] = body['created'].isoformat()
        self._write_object(next_id, body)
        return new


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

        print('Migrated ', thing)
        return thing

    def get_one(self, thing_id):
        """
        Args:
            _id (string): the object id
        Returns:
            File: the Thing object
        """
        # TODO: validate the type of the object in case ID passed in by client is invalid
        #
        # e.g. query get_new_task {
        # node(id:"UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA=") {
        #         __typename
        #                 ... on StrongMotionStation {
        #           id
        #           site_code
        #         }
        #     ... on RuptureGenerationTask {
        #             arguments {k v}
        #         created
        #         state
        #         result
        #         }
        #     }
        # }
        # after smoketests the query will return an SMS, but object Type in ID is RuptureGenerationTask
        #
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
        assert _type == clazz_name

        if kwargs.get('created'):
            kwargs['created'] = kwargs['created'].isoformat()

        if kwargs.get('updated'):
            kwargs['updated'] = kwargs['updated'].isoformat()

        jsondata = self.migrate_old_thing_object(self.get_one_raw(this_id))
        body = benedict(jsondata)
        body.merge(kwargs)
        #body['clazz_name'] = clazz_name

        self._write_object(this_id, body)
        return self.from_json(body)

    def add_file_relation(self, thing_id, file_id, file_role):
        obj = self._read_object(thing_id)
        logger.info("add_file_relation: thing_id: %s, file_id %s, " % (thing_id, file_id))
        print("####add_file_relation", thing_id, obj)
        try:
            obj['files'].append({'file_id': file_id, 'file_role': file_role})
        except (KeyError, AttributeError):
            obj['files'] = [{'file_id': file_id, 'file_role': file_role}]
        self._write_object(thing_id, obj)
        return self.from_json(obj)


    def add_child_relation(self, thing_id, relation_id):
        obj = self._read_object(thing_id)
        logger.info("add_child_relation: thing_id: %s, relation_id %s, " % (thing_id, relation_id))
        # print("####add_file_relation", thing_id, obj)
        try:
            obj['children'].append(relation_id)
        except (KeyError, AttributeError):
            obj['children'] = [relation_id]
        self._write_object(thing_id, obj)
        return self.from_json(obj)

    def add_parent_relation(self, thing_id, relation_id):
        obj = self._read_object(thing_id)
        logger.info("add_parent_relation: thing_id: %s, relation_id %s, " % (thing_id, relation_id))
        try:
            obj['parents'].append(relation_id)
        except (KeyError, AttributeError):
            obj['parents'] = [relation_id]
        self._write_object(thing_id, obj)
        return self.from_json(obj)


    @staticmethod
    def from_json(jsondata):
        logger.info("from_json: %s" % str(jsondata))

        created = jsondata.get('created')
        if created and not isinstance(created, dt.datetime):
            jsondata['created'] = dt.datetime.fromisoformat(created)

        updated = jsondata.get('updated')
        if updated and not isinstance(updated, dt.datetime):
            jsondata['updated'] = dt.datetime.fromisoformat(updated)

        clazz_name = jsondata.pop('clazz_name')
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)

        return clazz(**jsondata)
