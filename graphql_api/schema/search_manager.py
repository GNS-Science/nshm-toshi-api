"""
Search Manager
"""
import os
import re
import json
import requests

TYPE = '_doc'

class SearchManager():

    def __init__(self, endpoint, es_index, awsauth):
        self._awsauth = awsauth
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
        try:
            print("SearchManager.search( ", term)
            response = requests.get(ES_ENDPOINT + '/' + ES_INDEX  + '/_search?q=' + term,
                auth=self._awsauth, headers=headers)
            print(response.content)
        except (Exception) as err:
            print("ERR SearchManager.search() ", err)
