import boto3
import os
import s3fs

#os.environ['S3_BUCKET_NAME'] = 'TEST_ONLY_S3'

def setup():
    global data

    from .schema import Tosh, Faction
    
# Create an S3 client
def _handler(name, body):
    s3 = boto3.client('s3',
        aws_access_key_id='S3RVER', 
        aws_secret_access_key='S3RVER',
        endpoint_url='http://localhost:4569')
    bucket_name = os.environ['S3_BUCKET_NAME'] 
    # print("BUCKET", bucket_name) 
    # Add a file to your Object Store
    response = s3.put_object(
        Bucket=bucket_name,
        Key=name,
        Body=body,
        ACL='public-read'
    )
    return response

def _handler2(name, body):
    fs = s3fs.S3FileSystem(anon=False,
                           client_kwargs = dict(
                               aws_access_key_id='S3RVER', 
                               aws_secret_access_key='S3RVER',
                               endpoint_url='http://localhost:4569'))
    bucket_name = os.environ['S3_BUCKET_NAME'] 
    print(fs.ls(bucket_name))
    myfile = fs.open("%s/%s" % (bucket_name, name))
    for line in myfile:
        print(line)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']    
    res = _handler2('my_file', file_in)
    print(res)
