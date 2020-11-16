from flask import Flask
from flask_graphql import GraphQLView
from graphql_api.schema import root_schema

app = Flask(__name__)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
    'graphql',
    schema=root_schema,
    graphiql=True,
))

if __name__ == '__main__':
    app.run()