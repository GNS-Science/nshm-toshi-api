import base64
import json
import os
import requests

from gql import gql, Client, AIOHTTPTransport
from hashlib import md5
from pathlib import Path

API_URL = "https://qsz8j27tw6.execute-api.ap-southeast-2.amazonaws.com/test/graphql"
#API_URL = 'http://127.0.0.1:5000/graphql'

transport = AIOHTTPTransport(url=API_URL)

class DataFileClient():

    def __init__(self):
        self.client = Client(
  	        transport=transport,
  		      fetch_schema_from_transport=True
		    )

    def upload(self, filepath):
        qry = gql('''
            mutation ($digest: String!, $file_name: String!, $file_size: Int!) {
              createFile(
                  hexDigest: $digest
                  fileName: $file_name
                  fileSize: $file_size
              ) {
                  ok
                  fileResult { id, fileName, fileSize, hexDigest, postUrl }
              }
            }''')
        
        filedata = open(filepath, 'rb')
        digest = base64.b64encode(md5(filedata.read()).digest()).decode()
        # print('DIGEST:', digest)

        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.close()
        # filedata.seek(0) #important!
        
        variables = dict(digest=digest, file_name=filepath.parts[-1], file_size=size)
        executed = self.client.execute(qry, variable_values=variables) 
        # print(executed)
        pu = json.loads(executed['createFile']['fileResult']['postUrl'])
        return pu

    def upload2(self, post_url, filepath):
        # print('POST DATA %s' % post_url )
        URL = "https://nshm-tosh-api-test.s3.amazonaws.com/"
        filedata = open(filepath, 'rb')
        # filedata.seek(0) #important!
        files = {'file': filedata}
        response = requests.post(
          url=URL, 
          data=post_url,
          files=files)
        # print(dir(response))
        # print(response.status_code, response.text, response.reason)

if __name__ == "__main__":
    myapi = DataFileClient()
    #myapi.upload("requirements.txt")
    #post_url = myapi.upload("CFM_SANSTVZ_5.1km_downdip.zip")
    #myapi.upload2(post_url, "../opensha/nshm-nz-opensha/data/ruptureSets/CFM_SANSTVZ_5.1km_downdip.zip")

    filepath = Path("/Users/chrisbc/Downloads/CFM_crustal_rupture_set.zip")
    #filepath = Path("/Users/chrisbc/Downloads/tenjin/hiki50.log")

    post_url = myapi.upload(filepath)
    myapi.upload2(post_url, filepath)
