import boto3
import os
import json
from io import BytesIO
import datetime as dt
# from graphql import GraphQLError

class TaskResultData():
  
    def __init__(self):
        self.client = boto3.client('s3',
                          aws_access_key_id='S3RVER', 
                          aws_secret_access_key='S3RVER',
                          endpoint_url='http://localhost:4569')
        self.bucket_name = os.environ.get('S3_BUCKET_NAME', "UNDEFINED")
        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(self.bucket_name, client=self.client)
        self.prefix = self.__class__.__name__
        
    def get_next_id(self):
        size = sum(1 for _ in self.bucket.objects.filter(Prefix='%s/' % self.prefix))
        return size

    def create(self, **kwargs):
        from .schema import OpenshaRuptureGenResult
        next_id  = str(self.get_next_id())
        if not  kwargs['started'].tzname(): #must have a timezone set
            raise ValueError("'started' DateTime() field must have a timezone set.")
        
        #kwargs['started'] = kwargs['started'].isoformat()
        new = OpenshaRuptureGenResult(next_id, **kwargs)
        body = new.__dict__.copy()
        body['started'] = body['started'].isoformat()
        key = "%s/%s/%s" % (self.prefix, next_id, "object.json")
        response = self.bucket.put_object(Key=key, Body=json.dumps(body))
        return new

    def get_one(self, task_result_id):
        from .schema import OpenshaRuptureGenResult, TaskResultType
        key = "%s/%s/%s" % (self.prefix, task_result_id, "object.json")
        obj = self.s3.Object(bucket_name=self.bucket_name,
                        key=key,
                        client=self.client)
        fo = BytesIO()
        obj.download_fileobj(fo)
        fo.seek(0)
        jsondata = json.load(fo)
        
        #Field type transforms...
        started = jsondata.get('started')
        if started:
            jsondata['started'] = dt.datetime.fromisoformat(started)
        print("get_one", jsondata)            
        return OpenshaRuptureGenResult(**jsondata)

    def get_all(self):
        task_results = []
        for obj_summary in self.bucket.objects.filter(Prefix='%s/' % self.prefix):
            prefix, task_result_id, filename = obj_summary.key.split('/')
            assert prefix == self.prefix
            task_results.append(self.get_one(task_result_id))
        return task_results

def get_faction(_id):
    from .schema import Faction
    Faction(id="1", name="Alliance to Restore the Republic", task_results=["1", "2", "3", "4", "5"])
