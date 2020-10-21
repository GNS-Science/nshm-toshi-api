#Example hacked from https://flask-restful.readthedocs.io/en/latest/quickstart.html
from flask import Flask
from flask_restful import (reqparse, abort, Api, Resource, 
                           fields, marshal_with, reqparse) 
app = Flask(__name__)
api = Api(app)


tosh_fields = dict(
    name=fields.String,
    date_created =  fields.DateTime,
    date_updated=  fields.DateTime,

    )
    
TOSHES = {
    'tosh1': {'name': 'build an API'},
    'tosh2': {'name': '?????'},
    'tosh3': {'name': 'profit!'},
}


def abort_if_tosh_doesnt_exist(tosh_id):
    if tosh_id not in TOSHES:
        abort(404, message="Tosh {} doesn't exist".format(tosh_id))

parser = reqparse.RequestParser()
parser.add_argument('task')


# Tosh
# shows a single tosh item and lets you delete a tosh item
class Tosh(Resource):
    
    @marshal_with(tosh_fields)
    def get(self, tosh_id):
        abort_if_tosh_doesnt_exist(tosh_id)
        return TOSHES[tosh_id]

    def delete(self, tosh_id):
        abort_if_tosh_doesnt_exist(tosh_id)
        del TOSHES[tosh_id]
        return '', 204
    
    @marshal_with(tosh_fields)
    def put(self, tosh_id):
        abort_if_tosh_doesnt_exist(tosh_id)
        args = parser.parse_args()
        tosh = {'name': args['name']}
        TOSHES[tosh_id] = tosh
        return tosh, 201


# ToshList
# shows a list of all toshs, and lets you POST to add new tasks
class ToshList(Resource):
    def get(self):
        return TOSHES

    def post(self):
        args = parser.parse_args()
        tosh_id = int(max(TOSHES.keys()).lstrip('tosh')) + 1
        tosh_id = 'tosh%i' % tosh_id
        TOSHES[tosh_id] = {'task': args['task']}
        return TOSHES[tosh_id], 201

##
## Actually setup the Api resource routing here
##
api.add_resource(ToshList, '/toshs')
api.add_resource(Tosh, '/toshs/<tosh_id>')


if __name__ == '__main__':
    app.run(debug=True)