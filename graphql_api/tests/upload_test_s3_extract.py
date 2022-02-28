import boto3
import os
# from graphql_api.schema import SearchManager
# raises ModuleNotFoundError: No module named 'graphql_api'

'''
This script is for populating the serverless local S3 service with some dummy data to perform local development of the API.
To Run:
sls dynamodb start --stage local & sls s3 start & SLS_OFFLINE=1 TOSHI_FIX_RANDOM_SEED=1 sls wsgi serve
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.8.0
S3_TEST_DATA_PATH={path/to/your/data} python3 graphql_api/tests/upload_test_s3_extract.py 
'''

local_path = os.environ.get('S3_TEST_DATA_PATH', None)
client = boto3.client('s3', 
    aws_access_key_id='S3RVER',
    aws_secret_access_key='S3RVER',
    endpoint_url='http://localhost:4569/')
bucket_name = os.environ.get('S3_BUCKET_NAME', "nshm22-toshi-api-local")
s3 = boto3.resource('s3')
search_manager = sm.SearchManager(endpoint=ES_ENDPOINT, es_index=ES_INDEX, awsauth=None)
try:
    client.create_bucket(Bucket=bucket_name)
except:
    print(f'Bucket {bucket_name} Exists!')
bucket = s3.Bucket(bucket_name, client=client)


def upload_objects(root_path):
    try:
        for path, subdirs, files in os.walk(root_path):
            directory_name = path.replace(root_path,"")[1:]
            for file in files:
                key = "%s/%s" % (directory_name, file)
                print(f'Uploading {key}!')
                bucket.upload_file(os.path.join(path, file), key)
                # es_key = key.replace("/", "_")
                # search_manager.index_document(es_key, body)
    except Exception as err:
        print(err)
    
    print('Done uploading!')
if __name__ == '__main__':
    upload_objects(local_path)

    