from pynamodb.attributes import UnicodeAttribute, JSONAttribute
from pynamodb.models import Model
from graphql_api.local_config import DEPLOYMENT_STAGE

class ToshiObject(Model):
    class Meta:
        billing_mode = 'PAY_PER_REQUEST'
        table_name = f"SolutionRupture-{DEPLOYMENT_STAGE}"
        region = 'ap-southeast-2'
        if DEPLOYMENT_STAGE == 'LOCAL':
            host = "http://localhost:8000"

    object_id = UnicodeAttribute(hash_key=True)
    object_type = UnicodeAttribute(range_key=True) #eg WLG-10000
    object_content = JSONAttribute() # the json string


        
def migrate():
    if not ToshiObject.exists():
        ToshiObject.create_table(wait=True)
        print(f"Migrate created table: {ToshiObject}")
        
        