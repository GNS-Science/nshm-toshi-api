from hashlib import sha256

from gql import gql, Client, AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport

sample_transport=RequestsHTTPTransport(
    url='http://127.0.0.1:5000/graphql',
    verify=False,
    retries=3,
)

transport = AIOHTTPTransport(url='http://127.0.0.1:5000/graphql')

class DataFileClient():

    def __init__(self):
        #set client here
        self.client = Client(
	    	transport=transport,
		    fetch_schema_from_transport=True
		)

    def upload(self, filename):
        qry = gql('''
            mutation ($file: Upload!, $digest: String!, $file_name: String!, $file_size: Int!) {
              createDataFile(
                  fileIn: $file
                  hexDigest: $digest
                  fileName: $file_name
                  fileSize: $file_size
              ) {
                  ok
                  fileResult { id, fileName, fileSize, hexDigest }
              }
            }''')
        filedata = open(filename, 'r')
        digest = sha256(filedata.read().encode()).hexdigest()
        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.seek(0) #important!
        variables = dict(file=filedata, digest=digest, file_name=filename, file_size=size)
        executed = self.client.execute(qry, variable_values=variables, upload_files=True)
        print(executed)


if __name__ == "__main__":
    myapi = DataFileClient()
    myapi.upload("requirements.txt")
               
