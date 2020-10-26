import os
import json
 
DB_ROOT = "/tmp/%s" % os.environ['S3_BUCKET_NAME']
TOSH_ROOT = DB_ROOT + "/" + "Tosh"

def setup():
    global data
    from .schema import Tosh, Faction
        
    for classroot in [TOSH_ROOT,]:
        os.makedirs(classroot, exist_ok=True)

class ToshData:
            
    def get_next_tosh_id(self):
        file_cnt = 0
        with os.scandir(TOSH_ROOT) as it:
            for entry in it:
                if not entry.name.startswith('.') and entry.is_dir():
                    print(entry.name)
                    file_cnt+=1
        return file_cnt + 1
       
    def create_tosh(self, tosh_name):
        from .schema import Tosh
    
        next_id  = str(get_next_tosh_id()) 
        new_tosh = Tosh(id=next_id, name=tosh_name)
        
        js = json.dumps(new_tosh.__dict__)
        os.mkdir(TOSH_ROOT + "/" + next_id)
        
        new_file = open("%s/%s/%s" % (TOSH_ROOT, next_id, "object.json"), 'wb')
        new_file.write(js)
        new_file.close()
        return new_tosh
     
    def get_tosh(tosh_id):
        tosh_file = open("%s/%s/%s" % (TOSH_ROOT, tosh_id, "object.json"), 'wb')
        return data["Tosh"][_id]
    
    def get_toshs():
        with os.scandir(TOSH_ROOT) as it:
            for entry in it:
                if not entry.name.startswith('.') and entry.is_dir():     
                    yield get_tosh(entry.name)   
    