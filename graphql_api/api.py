import logging
import logging.config
import os

import yaml
from flask import Flask
from flask_cors import CORS
from graphql_server.flask import GraphQLView

from graphql_api.config import LOGGING_CFG, TESTING
from graphql_api.dynamodb.models import migrate
from graphql_api.schema import root_schema

from .library_version_check import log_library_info

# from flask_graphql import GraphQLView


"""
Setup logging configuration
ref https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/

"""
if os.path.exists(LOGGING_CFG):
    with open(LOGGING_CFG, 'rt') as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)
else:
    print('warning, no logging config found, using basicConfig(INFO)')
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.debug('DEBUG logging enabled')
logger.info('INFO logging enabled')
logger.warning('WARN logging enabled')
logger.error('ERROR logging enabled')


if not TESTING:
    # because in testing, this screws up moto mocking
    log_library_info(['botocore', 'boto3'])

if os.getenv("TOSHI_FIX_RANDOM_SEED", None):
    print("Offline, setting random seed for smoketests")
    import random

    random.seed(42)

app = Flask(__name__)
CORS(app)

# ensure any tables exist ...
migrate()

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=root_schema,
        graphiql=True,
    ),
)

if __name__ == '__main__':
    app.run()
