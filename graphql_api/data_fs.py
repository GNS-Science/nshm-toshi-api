import os
import json
 
DB_ROOT = "/tmp/%s" % os.environ.get('S3_BUCKET_NAME', 'TEST_BUCKET')
# TOSH_ROOT = DB_ROOT + "/" + "Tosh"


class ToshData():
    
    def __init__(self, root=DB_ROOT):
        global data
        from .schema import Tosh
        self._db_root =  root + '/' + Tosh.__name__   
        os.makedirs(self._db_root, exist_ok=True)
               
    def get_next_id(self):
        file_cnt = 0
        with os.scandir(self._db_root) as it:
            for entry in it:
                if not entry.name.startswith('.') and entry.is_dir():
                    file_cnt+=1
        return file_cnt
       
    def create_tosh(self, tosh_name, faction_id=''):   
        next_id  = str(self.get_next_id()) 
        new_tosh = Tosh(id=next_id, name=tosh_name)
        
        js = json.dumps(new_tosh.__dict__)
        os.mkdir(self._db_root + "/" + next_id)
        
        new_file = open("%s/%s/%s" % (self._db_root, next_id, "object.json"), 'w')
        new_file.write(js)
        new_file.close()
        return new_tosh
     
    def get_tosh(self, tosh_id):

        tosh_file = "%s/%s/%s" % (self._db_root, tosh_id, "object.json")
        jsondata = json.load(open(tosh_file, 'r'))
        return Tosh(**jsondata)
    
    def get_toshs(self):
        toshs = []
        with os.scandir(self._db_root) as it:
            for entry in it:
                if not entry.name.startswith('.') and entry.is_dir():     
                    toshs.append(get_tosh(entry.name))
        return toshs   

def get_faction(_id):
    pass