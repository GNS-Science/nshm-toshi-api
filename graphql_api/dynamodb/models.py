from pynamodb.attributes import JSONAttribute, NumberAttribute, UnicodeAttribute, VersionAttribute
from pynamodb.models import Model

from graphql_api.config import DEPLOYMENT_STAGE, IS_OFFLINE, REGION, TESTING


class ToshiTableObject(Model):
    class Meta:
        billing_mode = 'PAY_PER_REQUEST'
        table_name = f"ToshiTableObject-{DEPLOYMENT_STAGE}"
        region = REGION
        if IS_OFFLINE and not TESTING:
            host = "http://localhost:8000"

    object_id = UnicodeAttribute(hash_key=True)
    object_type = UnicodeAttribute()
    object_content = JSONAttribute()  # the json string
    version = VersionAttribute()


class ToshiFileObject(Model):
    class Meta:
        billing_mode = 'PAY_PER_REQUEST'
        table_name = f"ToshiFileObject-{DEPLOYMENT_STAGE}"
        region = REGION
        if IS_OFFLINE and not TESTING:
            host = "http://localhost:8000"

    object_id = UnicodeAttribute(hash_key=True)
    object_type = UnicodeAttribute()
    object_content = JSONAttribute()  # the json string
    version = VersionAttribute()


class ToshiThingObject(Model):
    class Meta:
        billing_mode = 'PAY_PER_REQUEST'
        table_name = f"ToshiThingObject-{DEPLOYMENT_STAGE}"
        region = REGION
        if IS_OFFLINE and not TESTING:
            host = "http://localhost:8000"

    object_id = UnicodeAttribute(hash_key=True)
    object_type = UnicodeAttribute()  # eg WLG-10000
    object_content = JSONAttribute()  # the json string
    version = VersionAttribute()


class ToshiIdentity(Model):
    class Meta:
        billing_mode = 'PAY_PER_REQUEST'
        table_name = f"ToshiIdentity-{DEPLOYMENT_STAGE}"
        region = REGION
        if IS_OFFLINE and not TESTING:
            host = "http://localhost:8000"

    table_name = UnicodeAttribute(hash_key=True)
    object_id = NumberAttribute()
    version = VersionAttribute()


tables = [ToshiFileObject, ToshiTableObject, ToshiThingObject, ToshiIdentity]


def migrate():
    for table in tables:
        if not table.exists():
            table.create_table(wait=True)
            print(f"Migrate created table: {table}")


def drop_tables():
    for table in tables:
        if table.exists():
            table.delete_table()
            print(f'deleted table: {table}')
