import os
import logging
from flask import Flask
from flask_graphql import GraphQLView
from graphql_api.schema import root_schema
from flask_cors import CORS

if os.getenv("TOSHI_FIX_RANDOM_SEED", None):
	print("Offline, setting random seed for smoketests")
	import random
	random.seed(42)

app = Flask(__name__)
CORS(app)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
    'graphql',
    schema=root_schema,
    graphiql=True,
))


for logger in (
    app.logger,
    #logging.getLogger('pynamodb'),
    #logging.getLogger('other_package'),
):
    #logger.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    app.run()