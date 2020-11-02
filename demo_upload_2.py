import os
from hashlib import sha256
import json

from gql import gql, Client, AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport

import boto3
import requests

client_args = dict(aws_access_key_id='S3RVER', 
              aws_secret_access_key='S3RVER',
              endpoint_url='http://localhost:4569')
# client_args = {}
args = client_args or {}
s3_client = boto3.client('s3', **args)
s3_bucket_name = os.environ.get('S3_BUCKET_NAME', "nshm-tosh-api-test")

sample_transport=RequestsHTTPTransport(
    url='http://127.0.0.1:5000/graphql',
    verify=False,
    retries=3,
)

transport = AIOHTTPTransport(url='http://127.0.0.1:5000/graphql')
#transport = AIOHTTPTransport(url='https://qsz8j27tw6.execute-api.ap-southeast-2.amazonaws.com/test/graphql')

class DataFileClient():

    def __init__(self):
        #set client here
        self.client = Client(
	    	transport=transport,
		    fetch_schema_from_transport=True
		)

    def upload(self, filename):
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
        """
        filedata = open(filename, 'rb')
        try:
            digest = sha256(filedata.read()).hexdigest()
        except UnicodeDecodeError:
            digest = sha256(filedata.read().decode()).hexdigest()
        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.seek(0) #important!
        """
        variables = dict(digest="", file_name=filename, file_size=0)
        executed = self.client.execute(qry, variable_values=variables) #, upload_files=True)
        print(executed)
        pu = json.loads(executed['createFile']['fileResult']['postUrl'])
        return pu

    def upload2(self, post_url, filename):
        #s3 upload attempt
        # file_url = "http://localhost:4569/nshm-tosh-api-test/FileData/2/CFM_SANSTVZ_5.1km_downdip.zip?AWSAccessKeyId=S3RVER&Signature=Vp%2FIoJK2zaEopsD0JHU9e81Qnqg%3D&Expires=1604293354"
        # s3 = boto3.resource('s3')
        # bucket = s3.Bucket("nshm-tosh-api-test", client=s3_client)
        # bucket.put_object(Key=file_url, Body=open(filename, 'rb'))
        files = {'file': open(filename, 'rb')} # the key supposed to be file may be
        response = requests.post(
          url="http://localhost:4569/nshm-tosh-api-test", 
          data=post_url,
          files=files)
        print(response)

if __name__ == "__main__":
    myapi = DataFileClient()
    #myapi.upload("requirements.txt")
    post_url = myapi.upload("CFM_SANSTVZ_5.1km_downdip.zip")
    myapi.upload2(post_url, "../opensha/nshm-nz-opensha/data/ruptureSets/CFM_SANSTVZ_5.1km_downdip.zip")
