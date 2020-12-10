"""
Search Manager
"""
#from importlib import import_module
import requests
from .custom.rupture_generation import RuptureGenerationTask
from .file import File

from graphql_api.data_s3.thing_data import ThingData

TYPE = '_doc'

class SearchManager():

    def __init__(self, endpoint, es_index, awsauth):
        self._awsauth = awsauth
        self._endpoint = endpoint
        self._es_index = es_index
        self._url = endpoint + '/' + es_index + '/' + TYPE + '/'

    def index_document(self, key, document):
        # Index the document
        headers = { "Content-Type": "application/json" }
        try:
            print("SearchManager.index_document", self._url + key)
            response = requests.put(self._url + key, auth=self._awsauth, json=document, headers=headers)
            print(response.content)
        except (Exception) as err:
            print("ERR SearchManager.index_document ", err)

    def search(self, term):
        headers = {} # "Content-Type": "application/json" }
        result = []
        try:
            #print("SearchManager.search( ", term)
            qurl = self._endpoint + '/' + self._es_index  + '/_search?q=' + term
            #print("Query URL: ", qurl)
            response = requests.get(qurl, auth=self._awsauth, headers=headers).json()
            print(response)
            #count = response['hits']['total']
            #print ("count",  count)
            for obj in response['hits']['hits']:
                print( obj['_index'], obj['_type'], obj['_id'], obj['_score'])
                if 'TaskData' in obj['_id']:
                    result.append(RuptureGenerationTask.from_json(obj['_source']))
                elif 'FileData' in obj['_id']:
                    result.append(File(**obj['_source']))
                elif 'ThingData' in obj['_id']:
                    # clazz_name = obj['_source'].pop('clazz_name')
                    # clazz = getattr(import_module('graphql_api.schema'), clazz_name)
                    result.append(ThingData.from_json(obj['_source']))
                else:
                    raise ValueError("unable to resolve, object id", obj['_source'])

        except (Exception) as err:
            print("ERR SearchManager.search() ", err)

        return result