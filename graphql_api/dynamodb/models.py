from pynamodb.attributes import UnicodeAttribute, JSONAttribute
from pynamodb.models import Model

class ToshiObject(Model):
    class Meta:
        read_capacity_units = 10
        write_capacity_units = 20
        table_name = "ToshiObject"
        region = 'ap-southeast-2'
        host = "http://localhost:8000"

    object_id = UnicodeAttribute(hash_key=True)
    object_type = UnicodeAttribute(range_key=True) #eg WLG-10000
    object_content = JSONAttribute() # the json string


        
def migrate():
    if not ToshiObject.exists():
        ToshiObject.create_table(wait=True)
        print(f"Migrate created table: {ToshiObject}")
        
        