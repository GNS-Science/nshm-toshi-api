import os
from flask import Flask
from flask_graphql import GraphQLView
from graphql_api.schema import root_schema
from flask_cors import CORS

# ## the following doesn't seem to work/be used anywhere ?? Smoketests??
# if os.getenv("IS_OFFLINE", None):
# 	print("Offline, setting random seed for tests")
# 	import random
# 	random.seed(42)

app = Flask(__name__)
CORS(app)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
    'graphql',
    schema=root_schema,
    graphiql=True,
))

if __name__ == '__main__':
    app.run()