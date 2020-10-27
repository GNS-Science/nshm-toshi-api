from flask import Flask
from flask_graphql import GraphQLView
from graphene_file_upload.flask import FileUploadGraphQLView

from graphql_api.schema import schema
# from graphql_api import data_ as data

# data.setup()

app = Flask(__name__)

app.add_url_rule('/graphql', view_func=FileUploadGraphQLView.as_view(
    'graphql',
    schema=schema,
    graphiql=True,
))

# # Optional, for adding batch query support (used in Apollo-Client)
# app.add_url_rule('/graphql/batch', view_func=GraphQLView.as_view(
#     'graphql',
#     schema=schema,
#     batch=True
# ))

if __name__ == '__main__':
    app.run()