import boto3
import os
import json
from io import BytesIO

class ToshData():
    
    def __init__(self):
        self.client = boto3.client('s3',
                          aws_access_key_id='S3RVER', 
                          aws_secret_access_key='S3RVER',
                          endpoint_url='http://localhost:4569')
        self.bucket_name = os.environ['S3_BUCKET_NAME']

        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(self.bucket_name, client=self.client)
        self.prefix="Tosh"         
               
    def get_next_id(self):
        size = sum(1 for _ in self.bucket.objects.filter(Prefix='%s/' % self.prefix))
        return size
       
    def create_tosh(self, tosh_name, faction_id=''):
        from .schema import Tosh   
        next_id  = str(self.get_next_id()) 
        new_tosh = Tosh(id=next_id, name=tosh_name)
        key = "%s/%s/%s" % (self.prefix, next_id, "object.json")
        response = self.bucket.put_object(Key=key, Body=json.dumps(new_tosh.__dict__))
        return new_tosh
     
    def get_tosh(self, tosh_id):
        from .schema import Tosh
        key = "%s/%s/%s" % (self.prefix, tosh_id, "object.json")
        obj = self.s3.Object(bucket_name=self.bucket_name, 
                        key=key, 
                        client=self.client)
        fo = BytesIO()
        obj.download_fileobj(fo)
        fo.seek(0)
        jsondata = json.load(fo)
        return Tosh(**jsondata)
    
    def get_toshs(self):
        toshs = []
        for obj_summary in self.bucket.objects.filter(Prefix='%s/' % self.prefix):
            prefix, tosh_id, filename = obj_summary.key.split('/')
            assert prefix == self.prefix
            toshs.append(self.get_tosh(tosh_id))
        return toshs   

def get_faction(_id):
    from .schema import Faction
    Faction(id="1", name="Alliance to Restore the Republic", toshs=["1", "2", "3", "4", "5"])