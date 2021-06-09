
import os
from io import BytesIO
import boto3
import botocore
from copy import copy
import json

from datetime import datetime as dt, timedelta

class CacheObject():

    def __init__(self, key, value):
        self._key = key
        self._value = value
        self._created = dt.utcnow()
        self._accessed = copy(self._created)

    def age(self):
        return dt.utcnow() - self._accessed

    def key(self):
        return self._key

    def value(self):
        self._accessed = dt.utcnow()
        return self._value


class S3WriteThroughCache():
    """
    S3WriteThroughCache is a super simple cache for AWS_S3 objects
    """
    max_cache_objects = 200
    max_cache_ttl = timedelta(microseconds=1000)

    def __init__(self, client_args):
        """Args:
            client_args (dict): optional)arguments for the boto3 client
        """
        args = client_args or {}
        self._client = boto3.client('s3', **args)
        self._bucket_name = os.environ.get('S3_BUCKET_NAME', "nzshm22-toshi-api-local")
        self._s3 = boto3.resource('s3')
        self._bucket = self._s3.Bucket(self._bucket_name, client=self._client)

        self.__cache = dict()

    def _clean_cache(self):
        """
        remove stale objects
        """
        deletions = []
        for k, v in self.__cache.items():
            if v.age() > self.max_cache_ttl:
                deletions.append(k)

        for k in deletions:
            print('popping', self.__cache.pop(k))

    def _cache_put(self, object_key, body):
        self.__cache[object_key] = CacheObject(object_key, body)
        self._clean_cache()


    def _cache_get(self, object_key):
        cached = self.__cache.get(object_key, None)
        if cached:
            return cached.value()
        self._clean_cache()

    def __len__(self):
        return len(self.__cache)

    def write_through(self, object_key, body):
        """write object contents to the S3 bucket.

        Args:
            object_id (int): unique iD of the obect
            body (dict): dict to be serialised to JSON
        """
        #Add to cache
        self._cache_put(object_key, body)
        response = self._bucket.put_object(Key=object_key, Body=json.dumps(body))


    def read_through(self, object_key):
        """read object contents from the cache or S3 bucket.

        Args:
            object_id int): S3 object key

        Returns:
            dict: object data deserialised from the json object
        """

        #check if object is in cache
        # if object_key in self.__cache:
        #   return self.__cache[object_key]
        cached =  self._cache_get(object_key)
        if cached:
            return cached

        #no, then let get the object....
        obj = self._s3.Object(bucket_name=self._bucket_name,
                        key=object_key,
                        client=self._client)
        file_object = BytesIO()
        obj.download_fileobj(file_object)
        file_object.seek(0)
        object_data =  json.load(file_object)

        #and add to the cache
        self._cache_put(object_key, copy(object_data))
        # self.__cache[object_key] = copy(object_data)

        return object_data

