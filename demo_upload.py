from hashlib import sha256

class DataFileClient():

    def __init__(self):
        #set client here
        self.client = None

    def upload(self, filename):
        qry = '''
            mutation ($file: Upload!, $digest: String!, $file_name: String!, $file_size: Int!) {
              createDataFile(
                  fileIn: $file
                  hexDigest: $digest
                  fileName: $file_name
                  fileSize: $file_size
              ) { ok }
            }'''
        
        filedata = open(filename, 'r')
        digest = sha256(filedata.read().encode()).hexdigest()
        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.seek(0) #important!
        variables = dict(file=filedata, digest=digest, file_name=filename, file_size=size)
        executed = self.client.execute(qry, variable_values=variables)
        print(executed)


if __name__ == "__main__":
    myapi = DataFileClient()
    myapi.upload("requirements.txt")
               